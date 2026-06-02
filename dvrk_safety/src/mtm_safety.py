#!/usr/bin/env python

import rospy
from geometry_msgs.msg import PoseStamped
from sensor_msgs.msg import Joy
from std_msgs.msg import Float64 

left_gripper_position = None
right_gripper_position = None
initial_left_gripper_position_x = None
initial_left_gripper_position_y = None
initial_left_gripper_position_z = None
initial_right_gripper_position_x = None
initial_right_gripper_position_y = None
initial_right_gripper_position_z = None
centroid_drift_threshold = 0.05
centroid_drift_count = 0
headsensor = None
clutch = None
initial_centroid_x = None
initial_centroid_y = None
initial_centroid_z = None


def left_gripper_callback(data):
    global left_gripper_position
    global initial_left_gripper_position_x
    global initial_left_gripper_position_y
    global initial_left_gripper_position_z

    left_gripper_position = data.pose

    if initial_left_gripper_position_x is None:
        initial_left_gripper_position_x = left_gripper_position.position.x
        initial_left_gripper_position_y = left_gripper_position.position.y
        initial_left_gripper_position_z = left_gripper_position.position.z

def right_gripper_callback(data):
    global right_gripper_position
    global initial_right_gripper_position_x
    global initial_right_gripper_position_y
    global initial_right_gripper_position_z

    right_gripper_position = data.pose

    if initial_right_gripper_position_x is None:
        initial_right_gripper_position_x = right_gripper_position.position.x
        initial_right_gripper_position_y = right_gripper_position.position.y
        initial_right_gripper_position_z = right_gripper_position.position.z
        

def headsensor_callback(data):
    global headsensor
    headsensor = data.buttons[0]

def clutch_callback(data):
    global clutch
    global centroid_drift_count
    clutch = data.buttons[0]
    if clutch == 1:
        centroid_drift_count = 0

def calculate_initial_centroid():
    global initial_centroid_x
    global initial_centroid_y
    global initial_centroid_z
    global clutch
    

    if (initial_left_gripper_position_x is not None and initial_left_gripper_position_y is not None and initial_left_gripper_position_z is not None
        and initial_right_gripper_position_x is not None and initial_right_gripper_position_y is not None and initial_right_gripper_position_z is not None):
            initial_centroid_x = (initial_left_gripper_position_x + initial_right_gripper_position_x) / 2
            initial_centroid_y = (initial_left_gripper_position_y + initial_right_gripper_position_y) / 2
            initial_centroid_z = (initial_left_gripper_position_z + initial_right_gripper_position_z) / 2
            # rospy.loginfo("Initial Centroid set: x=%f, y=%f, z=%f", initial_centroid_x, initial_centroid_y, initial_centroid_z)


def calculate_centroid(event):
    global centroid_drift_count
    calculate_initial_centroid()

    if left_gripper_position is not None and right_gripper_position is not None and headsensor == 1:
        centroid_x = (left_gripper_position.position.x + right_gripper_position.position.x) / 2
        centroid_y = (left_gripper_position.position.y + right_gripper_position.position.y) / 2
        centroid_z = (left_gripper_position.position.z + right_gripper_position.position.z) / 2

        # rospy.loginfo("Centroid: x=%f, y=%f, z=%f", centroid_x, centroid_y, centroid_z)

        rospy.loginfo("%f %f %f", centroid_x, centroid_y, centroid_z)

        if (abs(centroid_x - initial_centroid_x) > centroid_drift_threshold or
            abs(centroid_y - initial_centroid_y) > centroid_drift_threshold or
            abs(centroid_z - initial_centroid_z) > centroid_drift_threshold):
            centroid_drift_count += 1
            # rospy.loginfo("Centroid drift detected. Count: %d", centroid_drift_count)'
            rospy.loginfo("Drift")

        else:
            centroid_drift_count -=1
            if centroid_drift_count < 0:
                centroid_drift_count =0
            # rospy.loginfo("Centroid drift not detected!!!!!! Count: %d", centroid_drift_count)
    
    
    mtm_safety_publisher.publish(Float64(centroid_drift_count))


def mtm_safety():
    global mtm_safety_publisher
    rospy.init_node('mtm_safety', anonymous=True)
    rospy.Subscriber('/dvrk/MTML/position_cartesian_current', PoseStamped, left_gripper_callback, queue_size=1, tcp_nodelay=True)
    rospy.Subscriber('/dvrk/MTMR/position_cartesian_current', PoseStamped, right_gripper_callback, queue_size=1, tcp_nodelay=True)
    rospy.Subscriber('/dvrk/footpedals/coag', Joy, headsensor_callback , queue_size=1, tcp_nodelay=True)
    rospy.Subscriber('/dvrk/footpedals/clutch', Joy, clutch_callback , queue_size=1, tcp_nodelay=True)
    mtm_safety_publisher = rospy.Publisher('/safety/mtm', Float64, queue_size=10)
    rospy.Timer(rospy.Duration(1), calculate_centroid)
    rospy.spin()

if __name__ == '__main__':
    mtm_safety()
