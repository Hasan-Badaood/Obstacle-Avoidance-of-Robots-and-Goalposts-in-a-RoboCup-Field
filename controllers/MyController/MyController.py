import sys
webots_path = r'C:\Program Files\Webots\lib\controller\python'
sys.path.append(webots_path)

import math
from controller import Robot

def get_robot_heading(compass_value):
    rad = math.atan2(compass_value[0], compass_value[1])
    bearing = (rad - 1.5708) / math.pi * 180.0
    if bearing < 0.0:
        bearing = bearing + 360.0
    heading = 360 - bearing
    if heading > 360.0:
        heading -= 360.0
    return heading

robot = Robot()

left_motor = robot.getDevice('left wheel motor')
right_motor = robot.getDevice('right wheel motor')
left_motor.setPosition(float('inf'))
right_motor.setPosition(float('inf'))
left_motor.setVelocity(0)
right_motor.setVelocity(0)

sampling_period = 1
gps = robot.getDevice("gps")
compass = robot.getDevice("compass")
gps.enable(sampling_period)
compass.enable(sampling_period)

sensor_names = ['ps0','ps1','ps2','ps3','ps4','ps5','ps6','ps7']
sensors = []
for name in sensor_names:
    s = robot.getDevice(name)
    s.enable(64)
    sensors.append(s)

robot.step(1000)

max_speed = 6.0
destination_coordinate = [-0.209, -0.249]
distance_threshold = 0.05
angle_threshold = 4
OBSTACLE_THRESHOLD = 100.0

def get_angle_to_goal():
    current = gps.getValues()
    direction_vector = [destination_coordinate[0] - current[0],
                        destination_coordinate[1] - current[1]]
    degree = math.atan2(direction_vector[0], direction_vector[1]) * 180 / math.pi
    return round(degree) % 360

def rotate_to_goal():
    degree_to_target = get_angle_to_goal()
    rotate_right = True if degree_to_target <= 180 else False
    print(f"Rotating to face goal: {degree_to_target} degrees")
    while robot.step(64) != -1:
        current_degree = get_robot_heading(compass.getValues())
        diff = abs(current_degree - degree_to_target)
        if diff < angle_threshold or diff > (360 - angle_threshold):
            left_motor.setVelocity(0)
            right_motor.setVelocity(0)
            robot.step(500)
            print("Facing goal!")
            break
        if rotate_right:
            left_motor.setVelocity(max_speed)
            right_motor.setVelocity(-max_speed)
        else:
            left_motor.setVelocity(-max_speed)
            right_motor.setVelocity(max_speed)

def is_obstacle_ahead():
    sv = [s.getValue() for s in sensors]
    return sv[7] > OBSTACLE_THRESHOLD or sv[0] > OBSTACLE_THRESHOLD, sv

# Step 1 - rotate to face goal
rotate_to_goal()
print("Moving to goal...")

while robot.step(64) != -1:

    current = gps.getValues()
    dist = math.sqrt((current[0]-destination_coordinate[0])**2 + 
                     (current[1]-destination_coordinate[1])**2)

    if dist < distance_threshold:
        print(f"=== GOAL REACHED! ===")
        left_motor.setVelocity(0)
        right_motor.setVelocity(0)
        break

    obstacle_ahead, sv = is_obstacle_ahead()

    if obstacle_ahead:
        print("Obstacle detected! Stepping aside...")
        
        # Step 1: STOP
        left_motor.setVelocity(0)
        right_motor.setVelocity(0)
        robot.step(500)
        
        # Step 2: Turn 90 degrees to the side
        if sv[0] > sv[7]:
            # obstacle more on right, turn LEFT 90 degrees
            print("Turning LEFT 90 degrees")
            for _ in range(25):
                left_motor.setVelocity(-max_speed)
                right_motor.setVelocity(max_speed)
                robot.step(64)
        else:
            # obstacle more on left, turn RIGHT 90 degrees
            print("Turning RIGHT 90 degrees")
            for _ in range(25):
                left_motor.setVelocity(max_speed)
                right_motor.setVelocity(-max_speed)
                robot.step(64)
        
        # Step 3: Move forward to clear the obstacle
        print("Moving sideways to clear obstacle...")
        for _ in range(40):
            left_motor.setVelocity(max_speed)
            right_motor.setVelocity(max_speed)
            robot.step(64)
        
        # Step 4: Stop
        left_motor.setVelocity(0)
        right_motor.setVelocity(0)
        robot.step(500)
        
        # Step 5: Re-rotate to face goal
        print("Re-orienting to goal...")
        rotate_to_goal()
        print("Continuing to goal!")

    else:
        # No obstacle - drive straight
        left_motor.setVelocity(max_speed)
        right_motor.setVelocity(max_speed)
        print(f"Driving to goal - dist:{dist:.3f}")