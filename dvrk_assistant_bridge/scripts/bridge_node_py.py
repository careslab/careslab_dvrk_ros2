#!/usr/bin/env python
import rospy
from std_msgs.msg import String, Bool, Empty, Float32,Int16
from arm import arm as robot

#--------------------------------------------------------
# GLOBAL VALUES
#--------------------------------------------------------
__hw_ecm__ = robot('ECM')
__hw_psm1__ = robot('PSM1')
__hw_psm2__ = robot('PSM2')
__hw_mtml__ = robot('MTML')
__hw_mtmr__ = robot('MTMR')
__arms_homed__ = False

#--------------------------------------------------------
# Autocamera Callbacks
#--------------------------------------------------------
def autocameraRunCallback(data):
    print("auto camera run callback")
    rospy.Publisher('/autocamera/run', Bool, latch=True, queue_size=10).publish(data)
def autocameraTrackCallback(data):
    rospy.Publisher('/autocamera/track', String, latch=True, queue_size=10).publish(data)
    print("auto camera track callback")
def autocameraKeepCallback(data):
    print("auto camera keep callback")
    rospy.Publisher('/autocamera/keep', String, latch=True, queue_size=10).publish(data)
def autocameraFindToolsCallback(data):
    print("auto camera find callback")
    rospy.Publisher('/autocamera/find_tools', Empty, latch=True, queue_size=10).publish(data)
def autocameraInnerZoomCallback(data):
    print("auto camera inner zoom callback")
    rospy.Publisher('/autocamera/inner_zoom_value', Int16, latch=True, queue_size=10).publish(data)
def autocameraOuterZoomCallback(data):
    print("auto camera outer zoom callback")
    rospy.Publisher('/autocamera/outer_zoom_value', Int16, latch=True, queue_size=10).publish(data)

#--------------------------------------------------------
# Clutch and Move Callbacks
#--------------------------------------------------------
def clutchAndMoveRunCallback(data):
    print("clutch and move callbacks")
    rospy.Publisher('/clutch_and_move/run', Bool, latch=True, queue_size=10).publish(data)

#--------------------------------------------------------
# Joystick Callbacks
#--------------------------------------------------------
def joystickRunCallback(data):
    print("Joystick callbacks")
    rospy.Publisher('/joystick/run', Bool, latch=True, queue_size=10).publish(data)

#--------------------------------------------------------
# Bleeding Detection Callbacks
#--------------------------------------------------------
def bleedingDetectionRunCallback(data):
    print("Bleeding callbacks")
    rospy.Publisher('/bleeding_detection/run', String, latch=True, queue_size=10).publish(data)

#--------------------------------------------------------
# dvrk Callbacks
#--------------------------------------------------------

def home(data):
    print("dvrk home")
    rospy.Publisher('/dvrk/console/home', Empty, latch=True, queue_size=1).publish(Empty())
def powerOff(data):
    print("dvrk power off")
    rospy.Publisher('/dvrk/console/power_off', Empty, latch=True, queue_size=1).publish(Empty())
def reset(data):
    print("dvrk reset")
    q_ecm = [0.0, 0.0, 0.0, 0.0]
    q_psm1 = [0.12544035007602872, 0.2371651265674347, 0.13711766733000003, 0.8391791538250665, -0.12269957678936552, -0.14898520116918784, -0.17461480669754448]
    q_psm2 = [-0.01502071544036667, -0.050506672997428295, 0.14912649789000001, -0.9888977734730169, -0.18391272868428285, -0.05774053780206659, -0.17461480669754453]
    q_mtml = [0.0867019358531589, 0.008250772814637434, 0.1410445179152299, -1.498627346290218, 0.0740159621884837, -0.15691383983958546, 0.00592127680054577, 0.0]
    q_mtmr = [0.13146490673506123, -0.06150289811827064, 0.16527587983749847, 1.5291786517226071, 0.28422129480377745, 0.14211064740188872, 0.05329149120491193, 0.0]
    r_ecm  = __hw_ecm__.move_joint_list(q_ecm,[0,1,2,3], interpolate=True)
    r_psm1 = __hw_psm1__.move_joint_list(q_psm1, interpolate=True)
    r_psm2 = __hw_psm2__.move_joint_list(q_psm2, interpolate=True)
    r_mtml = __hw_mtml__.move_joint_list( q_mtml, interpolate=True)
    r_mtmr = __hw_mtmr__.move_joint_list(q_mtmr, interpolate=True)
    
def saveCurrentEcmPositionAs(data):
    print("Save Current ECM Position still in progress")
def gotoCurrentEcmPositionAs(data):
    print("Go To Current ECM Position still in progress")
    
def initialize():

    rospy.init_node('assistant_bridge', anonymous=False)

    #--------------------------------------------------------
    # Autocamera Callbacks
    #--------------------------------------------------------
    rospy.Subscriber("/assistant/autocamera/run", Bool, autocameraRunCallback)
    rospy.Subscriber("/assistant/autocamera/track", String, autocameraTrackCallback)
    rospy.Subscriber("/assistant/autocamera/keep", String, autocameraKeepCallback)
    rospy.Subscriber("/assistant/autocamera/find_tools", Empty, autocameraFindToolsCallback)
    rospy.Subscriber("/assistant/autocamera/inner_zoom_value", Float32, autocameraInnerZoomCallback)
    rospy.Subscriber("/assistant/autocamera/outer_zoom_value", Float32, autocameraOuterZoomCallback)

    #--------------------------------------------------------
    # Clutch and Move Callbacks
    #--------------------------------------------------------
    rospy.Subscriber("/assistant/clutch_and_move/run", Bool, clutchAndMoveRunCallback)

    #--------------------------------------------------------
    # Joystick Callbacks
    #--------------------------------------------------------
    rospy.Subscriber("/assistant/joystick/run", Bool, joystickRunCallback)

    #--------------------------------------------------------
    # Bleeding Detection Callbacks
    #--------------------------------------------------------
    rospy.Subscriber("/assistant/bleeding_detection/run", Bool, bleedingDetectionRunCallback)

    #--------------------------------------------------------
    # dvrk Callbacks
    #--------------------------------------------------------
    rospy.Subscriber("/assistant/home", Empty, home)
    rospy.Subscriber("/assistant/power_off", Empty, powerOff)
    rospy.Subscriber("/assistant/reset", Empty, reset)
    rospy.Subscriber("/assistant/save_ecm_position", Int16, saveCurrentEcmPositionAs)
    rospy.Subscriber("/assistant/goto_ecm_position", Int16, gotoCurrentEcmPositionAs)



    # spin() simply keeps python from exiting until this node is stopped
    rospy.spin()

if __name__ == '__main__':
    rospy.loginfo("Running dvrk assistant bridge")
    try:
        initialize()
    except rospy.ROSInterruptException:
        pass
