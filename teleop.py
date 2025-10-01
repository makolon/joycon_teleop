from __future__ import annotations
import json
import socket
import time
from types import SimpleNamespace
from typing import Dict, Any

from pyjoycon import JoyCon, get_L_id, get_R_id

# Destination for UDP packets
DEST_HOST, DEST_PORT = "127.0.0.1", 5005


def _sanitize_key(key: str) -> str:
    """Convert Joy-Con status keys into Python-friendly attribute names."""
    return key.replace("-", "_")


def _dict_to_namespace(data: Any) -> Any:
    """Recursively wrap nested dictionaries into SimpleNamespace instances."""
    if isinstance(data, dict):
        return SimpleNamespace(**{_sanitize_key(k): _dict_to_namespace(v) for k, v in data.items()})
    return data


def _namespace_to_dict(data: Any) -> Any:
    """Recursively convert SimpleNamespace objects back into dictionaries."""
    if isinstance(data, SimpleNamespace):
        return {k: _namespace_to_dict(v) for k, v in vars(data).items()}
    if isinstance(data, dict):
        return {k: _namespace_to_dict(v) for k, v in data.items()}
    if isinstance(data, (list, tuple)):
        return [_namespace_to_dict(v) for v in data]
    return data


def to_attr_status(st: Dict[str, Any]) -> SimpleNamespace:
    """Wrap pyjoycon's dict status into an attribute-access object."""
    status = _dict_to_namespace(st)

    sticks = status.analog_sticks
    left = sticks.left
    right = sticks.right

    buttons = status.buttons
    b_left = buttons.left
    b_right = buttons.right
    b_shared = buttons.shared

    stick_left = SimpleNamespace(x=left.horizontal, y=left.vertical)
    stick_right = SimpleNamespace(x=right.horizontal, y=right.vertical)

    # Flatten button states for quick access and JSON payloads
    btn = SimpleNamespace(
        a=b_right.a,
        b=b_right.b,
        x=b_right.x,
        y=b_right.y,
        r=b_right.r,
        zr=b_right.zr,
        sl_right=b_right.sl,
        sr_right=b_right.sr,
        l=b_left.l,
        zl=b_left.zl,
        sl_left=b_left.sl,
        sr_left=b_left.sr,
        dpad_up=b_left.up,
        dpad_down=b_left.down,
        dpad_left=b_left.left,
        dpad_right=b_left.right,
        plus=b_shared.plus,
        minus=b_shared.minus,
        home=b_shared.home,
        capture=b_shared.capture,
        stick_left=b_shared.l_stick,
        stick_right=b_shared.r_stick,
        charging_grip=b_shared.charging_grip,
    )

    return SimpleNamespace(
        battery=status.battery,
        accel=status.accel,
        gyro=status.gyro,
        analog_sticks=sticks,
        button_groups=buttons,
        stick_left=stick_left,
        stick_right=stick_right,
        buttons=btn,
    )


def normalize_axis(v: int, center: int = 2048, span: int = 2048, deadzone: float = 0.05) -> float:
    """
    Map raw 0..4095-ish to [-1, 1] with a deadzone.
    Adjust 'center' and 'span' if your device is off-centered or scaled differently.
    """
    x = (v - center) / float(span)
    if abs(x) < deadzone:
        return 0.0
    return max(-1.0, min(1.0, x))


def normalize_accel(accel_data: Any) -> SimpleNamespace:
    """
    Normalize accelerometer data to [-1, 1] range.
    Based on observed values, accel typically ranges from -5000 to +6000.
    """
    max_accel = 6000.0
    return SimpleNamespace(
        x=max(-1.0, min(1.0, accel_data.x / max_accel)),
        y=max(-1.0, min(1.0, accel_data.y / max_accel)),
        z=max(-1.0, min(1.0, accel_data.z / max_accel))
    )


def normalize_gyro(gyro_data: Any) -> SimpleNamespace:
    """
    Normalize gyroscope data to [-1, 1] range.
    Based on observed values, gyro typically ranges from -5000 to +5000.
    """
    max_gyro = 5000.0
    return SimpleNamespace(
        x=max(-1.0, min(1.0, gyro_data.x / max_gyro)),
        y=max(-1.0, min(1.0, gyro_data.y / max_gyro)),
        z=max(-1.0, min(1.0, gyro_data.z / max_gyro))
    )


def open_joycon(side: str) -> JoyCon:
    """Open a Joy-Con by side ('L' or 'R') and print its IDs."""
    if side.upper() == "R":
        vid, pid, mac = get_R_id()
        print("Right Joy-Con ID:", (vid, pid, mac))
    else:
        vid, pid, mac = get_L_id()
        print("Left Joy-Con ID:", (vid, pid, mac))
    return JoyCon(vid, pid, mac)


def main() -> None:
    # Open both Joy-Cons
    jcl = open_joycon("L")
    jcr = open_joycon("R")

    # Create a UDP socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # Set a fixed loop rate
    loop_hz = 100.0
    dt = 1.0 / loop_hz

    while True:
        try:
            # Read raw dict statuses from both Joy-Cons
            raw_l = jcl.get_status()
            raw_r = jcr.get_status()

            # Convert to attribute-style objects
            st_left  = to_attr_status(raw_l)
            st_right = to_attr_status(raw_r)

            # Normalize sticks to [-1, 1]; flip signs if your app expects it
            lx = normalize_axis(st_left.stick_left.x)
            ly = normalize_axis(st_left.stick_left.y)
            rx = normalize_axis(st_right.stick_right.x)
            ry = normalize_axis(st_right.stick_right.y)

            # Normalize accelerometer and gyro data to [-1, 1] range
            left_accel = normalize_accel(st_left.accel)
            right_accel = normalize_accel(st_right.accel)
            left_gyro = normalize_gyro(st_left.gyro)
            right_gyro = normalize_gyro(st_right.gyro)

            # Prepare a JSON-safe payload
            payload = {
                "ts": time.time(),
                "lx": lx,
                "ly": ly,
                "rx": rx,
                "ry": ry,
                "left_buttons": _namespace_to_dict(st_left.buttons),
                "right_buttons": _namespace_to_dict(st_right.buttons),
                "left_accel": _namespace_to_dict(left_accel),
                "right_accel": _namespace_to_dict(right_accel),
                "left_gyro": _namespace_to_dict(left_gyro),
                "right_gyro": _namespace_to_dict(right_gyro),
                "left_battery": _namespace_to_dict(st_left.battery),
                "right_battery": _namespace_to_dict(st_right.battery),
            }
            
            # Send via UDP
            sock.sendto(json.dumps(payload).encode("utf-8"), (DEST_HOST, DEST_PORT))

            time.sleep(dt)
        except OSError as e:
            # Handle transient read/send errors gracefully
            print("read/send error:", e)
            time.sleep(0.1)
        except KeyboardInterrupt:
            print("Interrupted by user.")
            break


if __name__ == "__main__":
    main()
