from __future__ import annotations
import json
import socket
import time
from types import SimpleNamespace
from typing import Dict, Any

from pyjoycon import JoyCon, get_L_id, get_R_id

DEST_HOST, DEST_PORT = "127.0.0.1", 5005


def to_attr_status(st: Dict[str, Any]) -> SimpleNamespace:
    """Wrap pyjoycon's dict status into an attribute-access object."""
    sticks = st.get("analog-sticks", {})
    left = sticks.get("left", {})
    right = sticks.get("right", {})
    buttons = st.get("buttons", {})
    b_left = buttons.get("left", {})
    b_right = buttons.get("right", {})
    b_shared = buttons.get("shared", {})

    stick_left  = SimpleNamespace(x=left.get("horizontal", 0),  y=left.get("vertical", 0))
    stick_right = SimpleNamespace(x=right.get("horizontal", 0), y=right.get("vertical", 0))

    # Expose common buttons as attributes (0/1 integers per pyjoycon)
    btn = SimpleNamespace(
        a=b_right.get("a", 0), b=b_right.get("b", 0),
        x=b_right.get("x", 0), y=b_right.get("y", 0),
        r=b_right.get("r", 0), zr=b_right.get("zr", 0),
        l=b_left.get("l", 0),  zl=b_left.get("zl", 0),
        plus=b_shared.get("plus", 0), minus=b_shared.get("minus", 0),
        home=b_shared.get("home", 0), capture=b_shared.get("capture", 0),
        stick_left=b_shared.get("l-stick", 0),   # stick press (L)
        stick_right=b_shared.get("r-stick", 0),  # stick press (R)
        sl_left=b_left.get("sl", 0), sr_left=b_left.get("sr", 0),
        sl_right=b_right.get("sl", 0), sr_right=b_right.get("sr", 0),
    )
    return SimpleNamespace(stick_left=stick_left, stick_right=stick_right, buttons=btn)


def normalize_axis(v: int, center: int = 2048, span: int = 2048, deadzone: float = 0.05) -> float:
    """
    Map raw 0..4095-ish to [-1, 1] with a deadzone.
    Adjust 'center' and 'span' if your device is off-centered or scaled differently.
    """
    x = (v - center) / float(span)
    if abs(x) < deadzone:
        return 0.0
    return max(-1.0, min(1.0, x))


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
    # Do not shadow builtins like `str`; use clear names.
    jcl = open_joycon("L")
    jcr = open_joycon("R")

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # Optional: tune per your app
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

            # Prepare a JSON-safe payload (only primitives and dicts)
            payload = {
                "ts": time.time(),
                "lx": lx, "ly": ly,
                "rx": rx, "ry": ry,
                "left_buttons": vars(st_left.buttons),
                "right_buttons": vars(st_right.buttons),
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
