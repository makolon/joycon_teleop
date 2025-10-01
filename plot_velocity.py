#!/usr/bin/env python3
"""
Real-time Joy-Con velocity and angular velocity plotter.
Collects data for 10 seconds and plots x, y, z translation velocities and rx, ry, rz angular velocities.
"""

import matplotlib.pyplot as plt
import numpy as np
import time
from collections import deque
from pyjoycon import JoyCon, get_L_id, get_R_id
from teleop import to_attr_status, normalize_accel, normalize_gyro
from velocity_estimator import VelocityEstimator


class VelocityPlotter:
    """Real-time velocity data collector and plotter for Joy-Con controllers."""
    
    def __init__(self, duration: float = 10.0, sample_rate: float = 100.0):
        self.duration = duration
        self.sample_rate = sample_rate
        self.dt = 1.0 / sample_rate
        
        # Initialize velocity estimators
        self.left_velocity_estimator = VelocityEstimator()
        self.right_velocity_estimator = VelocityEstimator()
        
        # Data storage
        self.max_samples = int(duration * sample_rate)
        self.timestamps = deque(maxlen=self.max_samples)
        
        # Translation velocities (m/s)
        self.left_vel_x = deque(maxlen=self.max_samples)
        self.left_vel_y = deque(maxlen=self.max_samples)
        self.left_vel_z = deque(maxlen=self.max_samples)
        self.right_vel_x = deque(maxlen=self.max_samples)
        self.right_vel_y = deque(maxlen=self.max_samples)
        self.right_vel_z = deque(maxlen=self.max_samples)
        
        # Angular velocities (rad/s) - from gyroscope
        self.left_gyro_x = deque(maxlen=self.max_samples)
        self.left_gyro_y = deque(maxlen=self.max_samples)
        self.left_gyro_z = deque(maxlen=self.max_samples)
        self.right_gyro_x = deque(maxlen=self.max_samples)
        self.right_gyro_y = deque(maxlen=self.max_samples)
        self.right_gyro_z = deque(maxlen=self.max_samples)
        
        # Control flags
        self.collecting = False
        self.start_time = None
        
    def open_joycons(self):
        """Open both Joy-Con controllers."""
        try:
            # Open left Joy-Con
            vid_l, pid_l, mac_l = get_L_id()
            if vid_l is None:
                print("Left Joy-Con not found. Make sure it's paired and connected.")
                return False
            self.jcl = JoyCon(vid_l, pid_l, mac_l)
            print(f"Left Joy-Con connected: {(vid_l, pid_l, mac_l)}")
            
            # Open right Joy-Con
            vid_r, pid_r, mac_r = get_R_id()
            if vid_r is None:
                print("Right Joy-Con not found. Make sure it's paired and connected.")
                return False
            self.jcr = JoyCon(vid_r, pid_r, mac_r)
            print(f"Right Joy-Con connected: {(vid_r, pid_r, mac_r)}")
            
            return True
        except Exception as e:
            print(f"Failed to connect Joy-Cons: {e}")
            return False
    
    def collect_data(self):
        """Collect data from Joy-Cons for the specified duration."""
        print(f"Starting data collection for {self.duration} seconds...")
        print("Move the Joy-Cons around to generate motion data!")
        
        self.collecting = True
        self.start_time = time.time()
        
        while self.collecting:
            try:
                current_time = time.time() - self.start_time
                
                # Stop if duration exceeded
                if current_time >= self.duration:
                    self.collecting = False
                    break
                
                # Read Joy-Con status
                raw_l = self.jcl.get_status()
                raw_r = self.jcr.get_status()
                
                # Convert to attribute-style objects
                st_left = to_attr_status(raw_l)
                st_right = to_attr_status(raw_r)
                
                # Normalize sensor data
                left_accel = normalize_accel(st_left.accel)
                right_accel = normalize_accel(st_right.accel)
                left_gyro = normalize_gyro(st_left.gyro)
                right_gyro = normalize_gyro(st_right.gyro)
                
                # Calculate velocities
                left_vel = self.left_velocity_estimator.update(left_accel, self.dt)
                right_vel = self.right_velocity_estimator.update(right_accel, self.dt)
                
                # Store data
                self.timestamps.append(current_time)
                
                # Translation velocities
                self.left_vel_x.append(left_vel.x)
                self.left_vel_y.append(left_vel.y)
                self.left_vel_z.append(left_vel.z)
                self.right_vel_x.append(right_vel.x)
                self.right_vel_y.append(right_vel.y)
                self.right_vel_z.append(right_vel.z)
                
                # Angular velocities (convert from normalized to rad/s)
                # Assuming max gyro range is ±2000 deg/s = ±34.9 rad/s
                max_gyro_rad_s = 34.9
                self.left_gyro_x.append(left_gyro.x * max_gyro_rad_s)
                self.left_gyro_y.append(left_gyro.y * max_gyro_rad_s)
                self.left_gyro_z.append(left_gyro.z * max_gyro_rad_s)
                self.right_gyro_x.append(right_gyro.x * max_gyro_rad_s)
                self.right_gyro_y.append(right_gyro.y * max_gyro_rad_s)
                self.right_gyro_z.append(right_gyro.z * max_gyro_rad_s)
                
                # Print progress
                if len(self.timestamps) % 50 == 0:
                    progress = (current_time / self.duration) * 100
                    print(f"Progress: {progress:.1f}% ({current_time:.1f}s/{self.duration}s)")
                
                # Sleep to maintain sample rate
                time.sleep(self.dt)
                
            except KeyboardInterrupt:
                print("\nData collection interrupted by user.")
                self.collecting = False
                break
            except Exception as e:
                print(f"Error during data collection: {e}")
                time.sleep(0.1)
        
        print(f"Data collection complete. Collected {len(self.timestamps)} samples.")
    
    def plot_data(self):
        """Create plots for translation and angular velocities."""
        if len(self.timestamps) == 0:
            print("No data to plot!")
            return
        
        # Convert deques to numpy arrays
        t = np.array(self.timestamps)
        
        # Translation velocities
        left_vx = np.array(self.left_vel_x)
        left_vy = np.array(self.left_vel_y)
        left_vz = np.array(self.left_vel_z)
        right_vx = np.array(self.right_vel_x)
        right_vy = np.array(self.right_vel_y)
        right_vz = np.array(self.right_vel_z)
        
        # Angular velocities
        left_gx = np.array(self.left_gyro_x)
        left_gy = np.array(self.left_gyro_y)
        left_gz = np.array(self.left_gyro_z)
        right_gx = np.array(self.right_gyro_x)
        right_gy = np.array(self.right_gyro_y)
        right_gz = np.array(self.right_gyro_z)
        
        # Create subplots
        fig, axes = plt.subplots(2, 3, figsize=(15, 10))
        fig.suptitle('Joy-Con Motion Analysis', fontsize=16)
        
        # Translation velocity plots
        axes[0, 0].plot(t, left_vx, 'b-', label='Left', alpha=0.7)
        axes[0, 0].plot(t, right_vx, 'r-', label='Right', alpha=0.7)
        axes[0, 0].set_title('X-axis Translation Velocity')
        axes[0, 0].set_ylabel('Velocity (m/s)')
        axes[0, 0].set_ylim(-1.0, 1.0)  # Fixed y-axis range for translation velocity
        axes[0, 0].legend()
        axes[0, 0].grid(True, alpha=0.3)
        
        axes[0, 1].plot(t, left_vy, 'b-', label='Left', alpha=0.7)
        axes[0, 1].plot(t, right_vy, 'r-', label='Right', alpha=0.7)
        axes[0, 1].set_title('Y-axis Translation Velocity')
        axes[0, 1].set_ylabel('Velocity (m/s)')
        axes[0, 1].set_ylim(-1.0, 1.0)  # Fixed y-axis range for translation velocity
        axes[0, 1].legend()
        axes[0, 1].grid(True, alpha=0.3)
        
        axes[0, 2].plot(t, left_vz, 'b-', label='Left', alpha=0.7)
        axes[0, 2].plot(t, right_vz, 'r-', label='Right', alpha=0.7)
        axes[0, 2].set_title('Z-axis Translation Velocity')
        axes[0, 2].set_ylabel('Velocity (m/s)')
        axes[0, 2].set_ylim(-1.0, 1.0)  # Fixed y-axis range for translation velocity
        axes[0, 2].legend()
        axes[0, 2].grid(True, alpha=0.3)
        
        # Angular velocity plots
        axes[1, 0].plot(t, left_gx, 'b-', label='Left', alpha=0.7)
        axes[1, 0].plot(t, right_gx, 'r-', label='Right', alpha=0.7)
        axes[1, 0].set_title('X-axis Angular Velocity (Roll)')
        axes[1, 0].set_ylabel('Angular Velocity (rad/s)')
        axes[1, 0].set_xlabel('Time (s)')
        axes[1, 0].set_ylim(-10, 10)  # Fixed y-axis range for angular velocity
        axes[1, 0].legend()
        axes[1, 0].grid(True, alpha=0.3)
        
        axes[1, 1].plot(t, left_gy, 'b-', label='Left', alpha=0.7)
        axes[1, 1].plot(t, right_gy, 'r-', label='Right', alpha=0.7)
        axes[1, 1].set_title('Y-axis Angular Velocity (Pitch)')
        axes[1, 1].set_ylabel('Angular Velocity (rad/s)')
        axes[1, 1].set_xlabel('Time (s)')
        axes[1, 1].set_ylim(-10, 10)  # Fixed y-axis range for angular velocity
        axes[1, 1].legend()
        axes[1, 1].grid(True, alpha=0.3)
        
        axes[1, 2].plot(t, left_gz, 'b-', label='Left', alpha=0.7)
        axes[1, 2].plot(t, right_gz, 'r-', label='Right', alpha=0.7)
        axes[1, 2].set_title('Z-axis Angular Velocity (Yaw)')
        axes[1, 2].set_ylabel('Angular Velocity (rad/s)')
        axes[1, 2].set_xlabel('Time (s)')
        axes[1, 2].set_ylim(-10, 10)  # Fixed y-axis range for angular velocity
        axes[1, 2].legend()
        axes[1, 2].grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.show()
        
        # Print some statistics
        print("\n=== Motion Statistics ===")
        print(f"Recording duration: {t[-1]:.1f} seconds")
        print(f"Sample count: {len(t)}")
        print(f"Average sample rate: {len(t)/t[-1]:.1f} Hz")
        
        print("\nTranslation Velocity Statistics (m/s):")
        print(f"Left Joy-Con  - X: {np.mean(np.abs(left_vx)):.3f}±{np.std(left_vx):.3f}, "
              f"Y: {np.mean(np.abs(left_vy)):.3f}±{np.std(left_vy):.3f}, "
              f"Z: {np.mean(np.abs(left_vz)):.3f}±{np.std(left_vz):.3f}")
        print(f"Right Joy-Con - X: {np.mean(np.abs(right_vx)):.3f}±{np.std(right_vx):.3f}, "
              f"Y: {np.mean(np.abs(right_vy)):.3f}±{np.std(right_vy):.3f}, "
              f"Z: {np.mean(np.abs(right_vz)):.3f}±{np.std(right_vz):.3f}")
        
        print("\nAngular Velocity Statistics (rad/s):")
        print(f"Left Joy-Con  - X: {np.mean(np.abs(left_gx)):.3f}±{np.std(left_gx):.3f}, "
              f"Y: {np.mean(np.abs(left_gy)):.3f}±{np.std(left_gy):.3f}, "
              f"Z: {np.mean(np.abs(left_gz)):.3f}±{np.std(left_gz):.3f}")
        print(f"Right Joy-Con - X: {np.mean(np.abs(right_gx)):.3f}±{np.std(right_gx):.3f}, "
              f"Y: {np.mean(np.abs(right_gy)):.3f}±{np.std(right_gy):.3f}, "
              f"Z: {np.mean(np.abs(right_gz)):.3f}±{np.std(right_gz):.3f}")


def main():
    """Main function to run the velocity plotter."""
    print("Joy-Con Velocity Plotter")
    print("========================")
    
    # Create plotter instance
    plotter = VelocityPlotter(duration=10.0, sample_rate=100.0)
    
    # Connect to Joy-Cons
    if not plotter.open_joycons():
        print("Failed to connect to Joy-Cons. Please make sure they are paired and try again.")
        return
    
    print("\nPress Enter to start recording, or Ctrl+C to quit...")
    try:
        input("Start recording? Press Enter...")
    except KeyboardInterrupt:
        print("Exiting...")
        return
    
    # Collect data
    try:
        plotter.collect_data()
    except KeyboardInterrupt:
        print("\nCollection interrupted by user.")
    
    # Plot results
    plotter.plot_data()


if __name__ == "__main__":
    main()
