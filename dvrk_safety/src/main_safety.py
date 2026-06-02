#!/usr/bin/env python

import rospy
from geometry_msgs.msg import PoseStamped
from sensor_msgs.msg import Joy
from std_msgs.msg import Float64
import datetime as dt

class MainSafety:
    def __init__(self):
        rospy.init_node('main_safety', anonymous=True)
        rospy.Subscriber('/safety/blink_rate', Float64, self.blink_callback, queue_size=1, tcp_nodelay=True)
        rospy.Subscriber('/safety/mtm', Float64, self.mtm_callback, queue_size=1, tcp_nodelay=True)
        rospy.Subscriber('/safety/psm', Float64, self.psm_callback, queue_size=1, tcp_nodelay=True)
        self.blink_thresh = 20 # Number of blinks per minute   
        self.mtm_thresh = 5 # Time in seconds spent outside of "ideal" range
        self.psm_thresh = 5 # Number of PSM collisions
        self.first_time_blink = True
        self.current_time_blink = None

    def blink_callback(self, data):
        #rospy.loginfo("Number of blinks: %f" % float(data.data))
        if(self.first_time_blink):
            self.first_time_blink = False
            self.current_time_blink = dt.datetime.now()
            return
        new_time = dt.datetime.now()
        diff_time = abs(self.current_time_blink - new_time)
        rate = 60/diff_time.total_seconds()*2
        #print("Diff time in seconds",diff_time.total_seconds())
        #print("Diff time",diff_time.total_seconds())
        if rate < self.blink_thresh:
            print("Blink rate too low.")
        self.current_time_blink = new_time


    def mtm_callback(self, data):
        #rospy.loginfo("Centroid drift count: %f" % float(data.data))
        if(data.data > self.mtm_thresh):
            print("Outside of master workspace range.")

    def psm_callback(self, data):
        #rospy.loginfo("Collision detection count: %f" % float(data.data))
        print("High collision occurrence.")

if __name__ == '__main__':
    main_safety_node = MainSafety()
    rospy.spin()

