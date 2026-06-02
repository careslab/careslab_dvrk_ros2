#!/usr/bin/env python
import datetime as dt
import rospy
import numpy as np
from sensor_msgs.msg import Joy, JointState
from geometry_msgs.msg import PoseStamped, Point
from std_msgs.msg import Float64 



headsensor = None
psm1_desired_position = None
psm1_current_position = None
psm2_desired_position = None
psm2_current_position = None
psm1_transformed_position = None
psm2_transformed_position = None
psm1_current_velocity_buffer = []
psm1_current_position_buffer = []
psm1_cartesian_position_buffer = []
psm1_velocity_buffer_length = 100
psm1_position_buffer_length = 10
sixth_joint_diff = []
psm1_jerk_diff = []
count = 0
window_size = 20
first = True


def psm1_desired_callback(data):
    global psm1_desired_position
    psm1_desired_position = data.position
    #print(psm1_desired_position[0])

def psm1_current_callback(data):
    global psm1_current_velocity_buffer
    global psm1_current_position_buffer
    global first
    psm1_current_position_buffer.append(data.position)
    if len(psm1_current_position_buffer) >= psm1_position_buffer_length:
        if (first):
            psm1_current_position_buffer = []
            first = False
            return()
        calculate_collision()

def psm2_desired_callback(data):
    global psm2_desired_position
    psm2_desired_position = data.position

def psm2_current_callback(data):
    global psm2_current_position
    psm2_current_position = data.position

def psm1_cartesian_pos_callback(data):
    global psm1_cartesian_position
    psm1_cartesian_position = data.pose
    psm1_cartesian_position_buffer.append(data.pose)
    #print(psm1_cartesian_position_buffer)
"""     if len(psm1_cartesian_position_buffer) >= psm1_position_buffer_length:
        calculate_collision_cartesian() """

def psm2_cartesian_pos_callback(data):
    global psm2_cartesian_position
    psm2_cartesian_position = data.pose

def psm1_transformed_pos_callback(data):
    global psm1_transformed_position
    psm1_transformed_position = data

def psm2_transformed_pos_callback(data):
    global psm2_transformed_position
    psm2_transformed_position = data

def headsensor_callback(data):
    global headsensor
    headsensor = data.buttons[0]

def moving_average_filter(data, window_size):
    return np.convolve(data, np.ones(window_size) / window_size, mode='valid')

def calculate_collision():
    global psm1_current_position_buffer
    global psm1_jerk_diff, psm1_current_position_buffer, sixth_joint_diff
    global psm1_transformed_position, psm2_transformed_position
    global count

    #if len(psm1_current_position_buffer) >= window_size:
    #    smoothed_positions = np.array([moving_average_filter(np.array(psm1_current_position_buffer)[:, i], window_size) for i in range(len(psm1_current_position_buffer[0]))]).T
    #else:
    #    smoothed_positions = np.array(psm1_current_position_buffer)



    if psm1_current_position_buffer and headsensor == 1:
        psm1_velocity_diff = np.diff(psm1_current_position_buffer, axis=0)
        psm1_acceleration_diff = np.diff(psm1_velocity_diff, axis=0)
        psm1_jerk_diff = np.diff(psm1_acceleration_diff, axis=0)

        #sixth_joint_diff = np.append(sixth_joint_diff, psm1_jerk_diff[:, 5])
        
        #print(psm1_jerk_diff)

        #print(psm1_jerk_diff[:, 5])

        #if np.any(abs(psm1_jerk_diff[:, :]) > 0.1):
            #print(psm1_jerk_diff[:,:])

    if psm1_transformed_position and psm2_transformed_position and headsensor == 1:
        pos1 = np.array([psm1_transformed_position.x, psm1_transformed_position.y, psm1_transformed_position.z])
        pos2 = np.array([psm2_transformed_position.x, psm2_transformed_position.y, psm2_transformed_position.z])
        distance = np.linalg.norm(pos1 - pos2)
        print("Distance", distance)
        print("Jerk", psm1_jerk_diff)
        if distance < 0.05 and np.any(abs(psm1_jerk_diff[:, :]) > 0.03): # Does not include psm2 jerk
            print("Potential collision based on distance and jerk")
            count += 1
            print(count)
            

            if (count > 5):
                psm_safety_publisher.publish(Float64(count))
                count = 0

    psm1_current_position_buffer = [] 
    
def calculate_collision_cartesian():
    global psm1_cartesian_position_buffer
    global psm1_jerk_diff, psm1_current_position_buffer, sixth_joint_diff
    global psm1_cartesian_position, psm2_cartesian_position

    positions = np.array([[pose.position.x, pose.position.y, pose.position.z] for pose in psm1_cartesian_position_buffer])

    psm1_velocity_diff = np.diff(positions, axis=0)
    psm1_acceleration_diff = np.diff(psm1_velocity_diff, axis=0)
    psm1_jerk_diff = np.diff(psm1_acceleration_diff, axis=0)    

    #print(psm1_jerk_diff)
    psm1_jerk_diff_rounded = np.round(psm1_jerk_diff, decimals=4)

    print(psm1_jerk_diff_rounded) 

    if np.any(abs(psm1_jerk_diff[:, :]) > 0.0001 ):
        print("Collision detected based on jerk cartesian")
        print(psm1_jerk_diff[:,:])

    
    psm1_cartesian_position_buffer = [] 
   
    

def psm_safety():
    global psm_safety_publisher
    rospy.init_node('psm_safety', anonymous=True)
    rospy.Subscriber('/dvrk/PSM1/state_joint_desired', JointState, psm1_desired_callback, queue_size=1, tcp_nodelay=True)
    rospy.Subscriber('/dvrk/PSM1/state_joint_current', JointState, psm1_current_callback, queue_size=1, tcp_nodelay=True)
    rospy.Subscriber('/dvrk/PSM2/state_joint_desired', JointState, psm2_desired_callback, queue_size=1, tcp_nodelay=True)
    rospy.Subscriber('/dvrk/PSM2/state_joint_current', JointState, psm2_current_callback, queue_size=1, tcp_nodelay=True)
    rospy.Subscriber('/dvrk/PSM1/position_cartesian_current', PoseStamped, psm1_cartesian_pos_callback, queue_size=1, tcp_nodelay=True)
    rospy.Subscriber('/dvrk/PSM2/position_cartesian_current', PoseStamped, psm2_cartesian_pos_callback, queue_size=1, tcp_nodelay=True)
    rospy.Subscriber('/autocamera/PSM1/transformed_position', Point, psm1_transformed_pos_callback, queue_size=1, tcp_nodelay=True) #This is from autocamera_algorithm.py
    rospy.Subscriber('/autocamera/PSM2/transformed_position', Point, psm2_transformed_pos_callback, queue_size=1, tcp_nodelay=True) #This is from autocamera_algorithm.py
    rospy.Subscriber('/dvrk/footpedals/coag', Joy, headsensor_callback , queue_size=1, tcp_nodelay=True)
    psm_safety_publisher = rospy.Publisher('/safety/psm', Float64, queue_size=10)
    rospy.spin()

if __name__ == '__main__': 
    psm_safety()
    
    




    
