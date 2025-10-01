from types import SimpleNamespace


class VelocityEstimator:
    """
    Simplified velocity estimator with basic drift compensation.
    """
    
    def __init__(self):
        # State variables
        self.velocity = SimpleNamespace(x=0.0, y=0.0, z=0.0)
        self.prev_accel = SimpleNamespace(x=0.0, y=0.0, z=0.0)
        self.is_initialized = False
        self.sample_count = 0
        
        # Simple gravity calibration
        self.gravity_offset = None
        self.init_samples = []
        
    def initialize_gravity(self, accel: SimpleNamespace, samples: int = 3):
        """Initialize gravity offset by averaging initial accelerometer readings."""
        self.init_samples.append(accel)
        
        if len(self.init_samples) >= samples:
            # Calculate average to estimate gravity vector
            avg_x = sum(s.x for s in self.init_samples) / len(self.init_samples)
            avg_y = sum(s.y for s in self.init_samples) / len(self.init_samples)
            avg_z = sum(s.z for s in self.init_samples) / len(self.init_samples)
            
            self.gravity_offset = SimpleNamespace(x=avg_x, y=avg_y, z=avg_z)
            self.is_initialized = True
            print(f"Gravity calibrated: x={avg_x:.3f}, y={avg_y:.3f}, z={avg_z:.3f}")
            
        return self.is_initialized
    
    def _remove_gravity(self, accel: SimpleNamespace) -> SimpleNamespace:
        """Remove gravity component from accelerometer data."""
        return SimpleNamespace(
            x=accel.x - self.gravity_offset.x,
            y=accel.y - self.gravity_offset.y,
            z=accel.z - self.gravity_offset.z
        )
    
    def update(self, raw_accel: SimpleNamespace, dt: float) -> SimpleNamespace:
        """Update velocity estimate with simple integration."""
        
        if not self.is_initialized:
            if self.initialize_gravity(raw_accel):
                print("Initialization complete, starting velocity estimation")
                return self.velocity
            else:
                print(f"Initializing... samples: {len(self.init_samples)}/3")
                return SimpleNamespace(x=0.0, y=0.0, z=0.0)
        
        self.sample_count += 1
        
        # Remove gravity
        accel_corrected = self._remove_gravity(raw_accel)
        
        # Simple integration with previous acceleration
        if hasattr(self, 'prev_accel') and self.prev_accel is not None:
            # Trapezoidal integration
            delta_vx = (accel_corrected.x + self.prev_accel.x) / 2.0 * dt
            delta_vy = (accel_corrected.y + self.prev_accel.y) / 2.0 * dt
            delta_vz = (accel_corrected.z + self.prev_accel.z) / 2.0 * dt
            
            self.velocity.x += delta_vx
            self.velocity.y += delta_vy
            self.velocity.z += delta_vz
            
            # Debug every 50 samples
            if self.sample_count % 50 == 0:
                accel_mag = (accel_corrected.x**2 + accel_corrected.y**2 + accel_corrected.z**2)**0.5
                vel_mag = (self.velocity.x**2 + self.velocity.y**2 + self.velocity.z**2)**0.5
                print(f"Sample {self.sample_count}: Accel mag: {accel_mag:.3f}, Vel mag: {vel_mag:.3f}")
                print(f"  dV: ({delta_vx:.4f}, {delta_vy:.4f}, {delta_vz:.4f})")
                print(f"  V: ({self.velocity.x:.4f}, {self.velocity.y:.4f}, {self.velocity.z:.4f})")
        
        # Simple velocity decay to prevent excessive drift
        decay = 0.99  # Very gentle decay
        self.velocity.x *= decay
        self.velocity.y *= decay
        self.velocity.z *= decay
        
        # Store current acceleration for next iteration
        self.prev_accel = SimpleNamespace(x=accel_corrected.x, y=accel_corrected.y, z=accel_corrected.z)
        
        # Limit velocity to reasonable range
        max_vel = 2.0
        self.velocity.x = max(-max_vel, min(max_vel, self.velocity.x))
        self.velocity.y = max(-max_vel, min(max_vel, self.velocity.y))
        self.velocity.z = max(-max_vel, min(max_vel, self.velocity.z))
        
        return SimpleNamespace(x=self.velocity.x, y=self.velocity.y, z=self.velocity.z)