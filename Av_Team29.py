"""
Alset IoT - Hugs the Lanes
Team 29: Matias, Naidelyn, Maya, Anshu
"""
import time
import random
from datetime import datetime
class SystemManagement:
    """handles logging and technician access for the whole system"""
    def __init__(self):
        self.logs = []
        self.technician_logged_in = False
        # default creds for demo purposes
        self.valid_credentials = {"tech1": "securepass123"}
        self.failed_attempts = {}

    def log_event(self, module, action, details=""):
        """logs any event with a timestamp, module name, and what happened"""
        entry = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "module": module,
            "action": action,
            "details": details
        }
        self.logs.append(entry)
        print(f"  [LOG] {entry['timestamp']} | {module} | {action} | {details}")

    def technician_login(self, username, password, otp_code):
        """multi-factor auth for technicians - password + otp"""
        if username not in self.valid_credentials:
            self._handle_failed_login(username)
            return False

        if self.failed_attempts.get(username, 0) >= 3:
            print("Account locked. Too many failed attempts.")
            self.log_event("SystemManagement", "account_locked", username)
            return False

        if self.valid_credentials[username] != password:
            self._handle_failed_login(username)
            return False

        # simulate otp check (in real life this would verify against a real otp)
        if otp_code != "123456":
            self._handle_failed_login(username)
            return False

        self.technician_logged_in = True
        self.failed_attempts[username] = 0
        self.log_event("SystemManagement", "technician_login", f"{username} logged in")
        return True

    def _handle_failed_login(self, username):
        """tracks failed login attempts and locks after 3"""
        self.failed_attempts[username] = self.failed_attempts.get(username, 0) + 1
        attempts = self.failed_attempts[username]
        print(f"Login failed. Attempt {attempts}/3.")
        self.log_event("SystemManagement", "login_failed", f"{username} attempt {attempts}")

    def technician_logout(self):
        """logs out the technician"""
        self.technician_logged_in = False
        self.log_event("SystemManagement", "technician_logout", "session ended")

    def view_logs(self):
        """shows all stored logs - only if technician is logged in"""
        if not self.technician_logged_in:
            print("Access denied. Technician login required.")
            return
        print("\n--- System Logs ---")
        for entry in self.logs:
            print(f"  {entry['timestamp']} | {entry['module']} | {entry['action']} | {entry['details']}")
        print("--- End Logs ---\n")

    def install_update(self, version):
        """simulates an ota software update"""
        if not self.technician_logged_in:
            print("Access denied. Technician login required.")
            return False
        self.log_event("SystemManagement", "ota_update", f"installing version {version}")
        print(f"Downloading update v{version}...")
        time.sleep(0.5)
        print(f"Update v{version} installed successfully.")
        self.log_event("SystemManagement", "ota_update", f"v{version} installed")
        return True


class SensorFusion:
    """combines data from lidar, camera, radar, gps, and imu into one picture"""
    def __init__(self, sys_mgmt):
        self.sys_mgmt = sys_mgmt
        self.lead_vehicle_distance = float('inf')
        self.lead_vehicle_speed = 0.0
        self.time_to_collision = float('inf')
        self.detected_objects = []
        self.lane_offset = 0.0  # how far off center we are in feet
        self.current_speed_limit = 55
        self.visibility_degraded = False

    def update_sensor_data(self, distance, lead_speed, objects, lane_offset, speed_limit):
        """takes in all the sensor readings and fuses them together"""
        self.lead_vehicle_distance = distance
        self.lead_vehicle_speed = lead_speed
        self.detected_objects = objects
        self.lane_offset = lane_offset
        self.current_speed_limit = speed_limit
        self._compute_ttc()

    def _compute_ttc(self):
        """calculates time to collision based on closing speed and distance"""
        closing_speed = max(0.1, self.lead_vehicle_speed - 0)  # simplified
        if self.lead_vehicle_distance > 0 and closing_speed > 0:
            self.time_to_collision = self.lead_vehicle_distance / closing_speed
        else:
            self.time_to_collision = float('inf')

    def set_visibility(self, degraded):
        """flags when wipers are on or its dark out"""
        self.visibility_degraded = degraded
        if degraded:
            self.sys_mgmt.log_event("SensorFusion", "visibility_degraded", "low visibility detected")

    def detect_traffic_signal(self, signal):
        """classifies a traffic signal - defaults to stop if unsure"""
        valid_signals = ["RED", "YELLOW", "GREEN", "STOP_SIGN"]
        if signal in valid_signals:
            self.sys_mgmt.log_event("SensorFusion", "signal_detected", signal)
            return signal
        # if we cant classify it, treat it as red (safety first)
        self.sys_mgmt.log_event("SensorFusion", "signal_unclassifiable", "defaulting to stop")
        return "RED"

    def detect_pedestrian(self):
        """checks if any detected objects are pedestrians or cyclists"""
        for obj in self.detected_objects:
            if obj["type"] in ["pedestrian", "cyclist"]:
                self.sys_mgmt.log_event(
                    "SensorFusion", "pedestrian_detected",
                    f"{obj['type']} at {obj['distance']}m"
                )
                return obj
        return None


class Planning:
    """decides what the car should do based on fused sensor data"""
    # priority order from our requirements doc (section 2.4)
    # 1. collision avoidance  2. emergency braking  3. lane stabilization  4. speed optimization
    def __init__(self, sensor_fusion, sys_mgmt):
        self.sensor = sensor_fusion
        self.sys_mgmt = sys_mgmt

    def evaluate_environment(self):
        """looks at everything and picks the highest priority action"""
        # check collision first (highest priority)
        if self.sensor.time_to_collision < 2.0:
            return self._handle_collision_threat()

        # check for pedestrians
        ped = self.sensor.detect_pedestrian()
        if ped and ped["distance"] < 15:
            return self._handle_pedestrian(ped)

        # check lane tracking
        if abs(self.sensor.lane_offset) > 1.0:
            return self._handle_lane_correction()

        # all good, just cruise
        return {"action": "maintain", "details": "no issues detected"}

    def _handle_collision_threat(self):
        """figures out if we should brake, steer, or both"""
        ttc = self.sensor.time_to_collision
        self.sys_mgmt.log_event("Planning", "collision_threat", f"ttc={ttc:.2f}s")
        if ttc < 1.0:
            return {"action": "emergency_brake", "force": 1.0, "details": f"ttc={ttc:.2f}s"}
        return {"action": "brake", "force": 0.6, "details": f"ttc={ttc:.2f}s, decelerating"}

    def _handle_pedestrian(self, ped):
        """slows down or stops for pedestrians and cyclists"""
        self.sys_mgmt.log_event(
            "Planning", "pedestrian_response",
            f"{ped['type']} at {ped['distance']}m"
        )
        if ped["distance"] < 5:
            return {"action": "full_stop", "details": f"{ped['type']} blocking path"}
        return {"action": "slow_down", "speed": 10, "details": f"{ped['type']} nearby"}

    def _handle_lane_correction(self):
        """steers back toward center when we drift"""
        offset = self.sensor.lane_offset
        # max correction angle is 20 degrees per our requirements (section 3.1.3)
        correction = min(20, abs(offset) * 5)
        direction = "right" if offset < 0 else "left"
        self.sys_mgmt.log_event("Planning", "lane_correction", f"offset={offset:.1f}ft, steer {direction}")
        return {"action": "steer", "angle": correction, "direction": direction}

    def handle_traffic_signal(self, signal):
        """responds to traffic lights and stop signs"""
        classified = self.sensor.detect_traffic_signal(signal)
        if classified in ["RED", "STOP_SIGN"]:
            self.sys_mgmt.log_event("Planning", "traffic_stop", classified)
            return {"action": "full_stop", "details": f"signal: {classified}"}
        elif classified == "YELLOW":
            self.sys_mgmt.log_event("Planning", "traffic_decel", "yellow light")
            return {"action": "decelerate", "details": "yellow light, slowing down"}
        else:
            self.sys_mgmt.log_event("Planning", "traffic_proceed", "green light, path clear")
            return {"action": "proceed", "details": "green light"}

    def calculate_following_distance(self, current_speed):
        """figures out safe following distance based on speed and conditions"""
        # base: 2 second rule
        safe_distance = current_speed * 2.0
        if self.sensor.visibility_degraded:
            safe_distance *= 1.5  # increase by 50% in bad visibility
        self.sys_mgmt.log_event(
            "Planning", "following_distance",
            f"safe={safe_distance:.1f}m, actual={self.sensor.lead_vehicle_distance:.1f}m"
        )
        return safe_distance


class VehicleControlSystem:
    """actually controls the car - steering, brakes, throttle"""

    def __init__(self, sys_mgmt):
        self.sys_mgmt = sys_mgmt
        self.speed = 0.0
        self.steering_angle = 0.0
        self.braking_force = 0.0

    def execute_command(self, command):
        """takes a planning command and makes the car do it"""
        action = command["action"]

        if action == "emergency_brake":
            self._apply_brakes(command.get("force", 1.0))
            print(f"  !! EMERGENCY BRAKE !! force={self.braking_force}")

        elif action == "full_stop":
            self._apply_brakes(1.0)
            self.speed = 0
            print(f"  Vehicle stopped. Reason: {command.get('details', '')}")

        elif action == "brake" or action == "decelerate":
            force = command.get("force", 0.5)
            self._apply_brakes(force)
            self.speed = max(0, self.speed - (force * 20))
            print(f"  Braking. force={force}, speed now={self.speed:.1f} km/h")

        elif action == "slow_down":
            target = command.get("speed", 10)
            self.speed = min(self.speed, target)
            print(f"  Slowing to {target} km/h. Reason: {command.get('details', '')}")

        elif action == "steer":
            angle = command.get("angle", 0)
            direction = command.get("direction", "center")
            self._perform_steering(angle, direction)
            print(f"  Steering {direction} by {angle} degrees")

        elif action == "proceed":
            self.braking_force = 0
            print(f"  Proceeding at {self.speed:.1f} km/h")

        elif action == "maintain":
            print(f"  Cruising at {self.speed:.1f} km/h. All systems normal.")

        self.sys_mgmt.log_event(
            "VCS", f"execute_{action}",
            f"speed={self.speed:.1f}, steering={self.steering_angle:.1f}, brake={self.braking_force:.1f}"
        )

    def _apply_brakes(self, force):
        """applies braking with the given force (0.0 to 1.0)"""
        self.braking_force = min(1.0, max(0.0, force))

    def _perform_steering(self, angle, direction):
        """adjusts steering angle"""
        if direction == "left":
            self.steering_angle = -angle
        elif direction == "right":
            self.steering_angle = angle
        else:
            self.steering_angle = 0

    def set_speed(self, speed):
        """sets the current speed"""
        self.speed = speed


class Actor:
    """represents who is controlling the car - autonomous system or human"""
    def __init__(self, name):
        self.name = name

    def display_control_status(self):
        """shows who's currently driving"""
        print(f"  Current controller: {self.name}")


class Vehicle:
    """the main vehicle class that ties everything together"""

    def __init__(self):
        self.is_vehicle_started = False
        self.current_controller = "Autonomous_System"
        self.is_cruise_active = False
        self.desired_speed = 0
        self.is_adaptive_cruise_active = False
        self.following_distance = 0
        # init all our subsystems
        self.sys_mgmt = SystemManagement()
        self.sensor_fusion = SensorFusion(self.sys_mgmt)
        self.planning = Planning(self.sensor_fusion, self.sys_mgmt)
        self.vcs = VehicleControlSystem(self.sys_mgmt)

    def start_vehicle_with_card(self, card_tapped):
        """starts the car when you tap your card"""
        if card_tapped:
            self.is_vehicle_started = True
            self.sys_mgmt.log_event("Vehicle", "started", "card tap verified")
            print("Vehicle started. Systems initializing...")
            self._perform_system_checks()
            return True
        return False

    def _perform_system_checks(self):
        """runs initial checks to make sure everything works"""
        print("Running system checks...")
        self.sys_mgmt.log_event("Vehicle", "system_checks", "all sensors online")
        print("System checks passed. Vehicle is ready to drive.")

    def transfer_control(self, new_controller):
        """hands control between human and autonomous system"""
        if new_controller == self.current_controller:
            print(f"Control is already with {new_controller}.")
            return
        old = self.current_controller
        self.current_controller = new_controller
        self.sys_mgmt.log_event("Vehicle", "control_transfer", f"{old} -> {new_controller}")
        print(f"Transferring control from {old} to {new_controller}.")

    def activate_cruise_control(self, speed):
        """turns on regular cruise control at the given speed"""
        if not self.is_vehicle_started or speed <= 0:
            print("Vehicle must be started and speed must be positive to activate cruise control.")
            return
        self.desired_speed = speed
        self.is_cruise_active = True
        self.vcs.set_speed(speed)
        self.sys_mgmt.log_event("Vehicle", "cruise_on", f"{speed} km/h")
        print(f"Cruise control activated at {speed} km/h.")

    def deactivate_cruise_control(self):
        """turns off cruise control"""
        if self.is_cruise_active:
            self.is_cruise_active = False
            self.sys_mgmt.log_event("Vehicle", "cruise_off", "deactivated")
            print("Cruise control deactivated.")

    def activate_adaptive_cruise_control(self, distance):
        """turns on adaptive cruise - maintains following distance"""
        if not self.is_vehicle_started:
            print("Vehicle must be started to activate adaptive cruise control.")
            return
        self.following_distance = distance
        self.is_adaptive_cruise_active = True
        self.sys_mgmt.log_event("Vehicle", "adaptive_cruise_on", f"following at {distance}m")
        print(f"Adaptive cruise control activated with a following distance of {distance} meters.")

    def deactivate_adaptive_cruise_control(self):
        """turns off adaptive cruise"""
        if self.is_adaptive_cruise_active:
            self.is_adaptive_cruise_active = False
            self.sys_mgmt.log_event("Vehicle", "adaptive_cruise_off", "deactivated")
            print("Adaptive cruise control deactivated.")

    def start_navigation(self, destination):
        """starts gps navigation to a destination"""
        self.sys_mgmt.log_event("Vehicle", "navigation_start", destination)
        print(f"Navigation to {destination} started. Calculating route...")
        time.sleep(0.5)
        print("Route calculated. Proceed to destination.")

    def monitor_lane_position(self):
        """checks if were drifting out of our lane"""
        self.sys_mgmt.log_event("Vehicle", "lane_monitor", f"offset={self.sensor_fusion.lane_offset:.1f}ft")
        if abs(self.sensor_fusion.lane_offset) > 1.0:
            command = self.planning._handle_lane_correction()
            self.vcs.execute_command(command)
        else:
            print("Vehicle is correctly aligned within the lane.")

    def handle_traffic_control(self, signal):
        """responds to traffic lights and stop signs"""
        command = self.planning.handle_traffic_signal(signal)
        self.vcs.execute_command(command)

    def detect_and_respond_to_crash_threats(self):
        """scans for potential crashes and reacts"""
        self.sys_mgmt.log_event("Vehicle", "crash_scan", "scanning for threats")
        if self.sensor_fusion.time_to_collision < 2.0:
            command = self.planning.evaluate_environment()
            self.vcs.execute_command(command)
            print("Crash threat detected. Initiating avoidance maneuvers.")
        else:
            print("No crash threats detected.")


#                                       SIMULATION 


def main():
    print("=" * 60)
    print("  Alset IoT - Hugs the Lanes | Team 29 Simulation")
    print("=" * 60)

    my_vehicle = Vehicle()

    # start the car
    print("\n--- Starting Vehicle ---")
    my_vehicle.start_vehicle_with_card(True)

    # set up actor
    vehicle_actor = Actor("Autonomous_System")
    vehicle_actor.display_control_status()

    # cruise control demo
    print("\n--- Cruise Control ---")
    my_vehicle.activate_cruise_control(50)

    # adaptive cruise
    print("\n--- Adaptive Cruise ---")
    my_vehicle.activate_adaptive_cruise_control(30)

    # traffic light handling
    print("\n--- Traffic Light: RED ---")
    my_vehicle.handle_traffic_control("RED")

    print("\n--- Traffic Light: GREEN ---")
    my_vehicle.handle_traffic_control("GREEN")

    # crash detection
    print("\n--- Crash Detection ---")
    my_vehicle.sensor_fusion.update_sensor_data(
        distance=10, lead_speed=5,
        objects=[], lane_offset=0.0, speed_limit=55
    )
    my_vehicle.detect_and_respond_to_crash_threats()

    # pedestrian detection
    print("\n--- Pedestrian Detection ---")
    my_vehicle.sensor_fusion.update_sensor_data(
        distance=50, lead_speed=0,
        objects=[{"type": "pedestrian", "distance": 8}],
        lane_offset=0.0, speed_limit=30
    )
    command = my_vehicle.planning.evaluate_environment()
    my_vehicle.vcs.execute_command(command)

    # lane monitoring
    print("\n--- Lane Monitoring (drifting left) ---")
    my_vehicle.sensor_fusion.lane_offset = -1.5
    my_vehicle.monitor_lane_position()

    print("\n--- Lane Monitoring (centered) ---")
    my_vehicle.sensor_fusion.lane_offset = 0.2
    my_vehicle.monitor_lane_position()

    # navigation
    print("\n--- Navigation ---")
    my_vehicle.start_navigation("123 Main Street, Miami FL")

    # control transfer: autonomous -> human
    print("\n--- Control Transfer ---")
    vehicle_actor = Actor("Autonomous_System")
    vehicle_actor.display_control_status()
    my_vehicle.transfer_control("Human")
    vehicle_actor = Actor("Human")
    vehicle_actor.display_control_status()

    # transfer back to autonomous
    my_vehicle.transfer_control("Autonomous_System")
    vehicle_actor = Actor("Autonomous_System")
    vehicle_actor.display_control_status()

    # try transferring to current controller (should say already there)
    my_vehicle.transfer_control("Autonomous_System")

    # deactivate systems
    print("\n--- Deactivating ---")
    my_vehicle.deactivate_cruise_control()
    my_vehicle.deactivate_adaptive_cruise_control()

    # technician demo
    print("\n--- Technician Access ---")
    my_vehicle.sys_mgmt.technician_login("tech1", "securepass123", "123456")
    my_vehicle.sys_mgmt.install_update("2.1.0")
    my_vehicle.sys_mgmt.view_logs()
    my_vehicle.sys_mgmt.technician_logout()


if __name__ == "__main__":
    main()