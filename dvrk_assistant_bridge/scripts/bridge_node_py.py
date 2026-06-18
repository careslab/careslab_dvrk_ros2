#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, DurabilityPolicy, ReliabilityPolicy
from std_msgs.msg import String, Bool, Empty, Float32, Int16
# from arm import arm as robot

#--------------------------------------------------------
# GLOBAL VALUES
#--------------------------------------------------------
# __hw_ecm__ = robot('ECM')
# __hw_psm1__ = robot('PSM1')
# __hw_psm2__ = robot('PSM2')
# __hw_mtml__ = robot('MTML')
# __hw_mtmr__ = robot('MTMR')
__arms_homed__ = False

class AssistantBridge(Node):
    def __init__(self):
        super().__init__('assistant_bridge')
        
        # ROS 2 equivalent of ROS 1 latch=True
        latch_qos = QoSProfile(
            depth=10,
            durability=DurabilityPolicy.TRANSIENT_LOCAL,
            reliability=ReliabilityPolicy.RELIABLE
        )
        
        #--------------------------------------------------------
        # Publishers
        #--------------------------------------------------------
        self.pub_autocamera_run = self.create_publisher(Bool, '/autocamera/run', latch_qos)
        self.pub_autocamera_track = self.create_publisher(String, '/autocamera/track', latch_qos)
        self.pub_autocamera_keep = self.create_publisher(String, '/autocamera/keep', latch_qos)
        self.pub_autocamera_find = self.create_publisher(Empty, '/autocamera/find_tools', latch_qos)
        self.pub_autocamera_inner_zoom = self.create_publisher(Int16, '/autocamera/inner_zoom_value', latch_qos)
        self.pub_autocamera_outer_zoom = self.create_publisher(Int16, '/autocamera/outer_zoom_value', latch_qos)
        
        self.pub_clutch_move_run = self.create_publisher(Bool, '/clutch_and_move/run', latch_qos)
        self.pub_joystick_run = self.create_publisher(Bool, '/joystick/run', latch_qos)
        self.pub_bleeding_run = self.create_publisher(String, '/bleeding_detection/run', latch_qos)
        
        # Small depth profile for console signals
        system_qos = QoSProfile(depth=1, durability=DurabilityPolicy.TRANSIENT_LOCAL)
        self.pub_dvrk_home = self.create_publisher(Empty, '/system/home', latch_qos)
        self.pub_dvrk_power_off = self.create_publisher(Empty, '/system/power_off', 10)

        #--------------------------------------------------------
        # Subscribers
        #--------------------------------------------------------
        # Autocamera
        self.create_subscription(Bool, "/assistant/autocamera/run", self.autocameraRunCallback, 10)
        self.create_subscription(String, "/assistant/autocamera/track", self.autocameraTrackCallback, 10)
        self.create_subscription(String, "/assistant/autocamera/keep", self.autocameraKeepCallback, 10)
        self.create_subscription(Empty, "/assistant/autocamera/find_tools", self.autocameraFindToolsCallback, 10)
        # Note: Changed subscriber types below to Int16 to match publisher payload logic
        self.create_subscription(Int16, "/assistant/autocamera/inner_zoom_value", self.autocameraInnerZoomCallback, 10)
        self.create_subscription(Int16, "/assistant/autocamera/outer_zoom_value", self.autocameraOuterZoomCallback, 10)

        # Clutch and Move
        self.create_subscription(Bool, "/assistant/clutch_and_move/run", self.clutchAndMoveRunCallback, 10)

        # Joystick
        self.create_subscription(Bool, "/assistant/joystick/run", self.joystickRunCallback, 10)

        # Bleeding Detection (Note: Changed subscriber type to String to match publisher logic)
        self.create_subscription(String, "/assistant/bleeding_detection/run", self.bleedingDetectionRunCallback, 10)

        # dvrk Console Configuration
        print("subscriptions")
        self.create_subscription(Empty, "/assistant/dvrk_home", self.home, 10)
        self.create_subscription(Empty, "/assistant/dvrk_off", self.powerOff, 10)
        self.create_subscription(Empty, "/assistant/reset", self.reset, 10)
        self.create_subscription(Int16, "/assistant/save_ecm_position", self.saveCurrentEcmPositionAs, 10)
        self.create_subscription(Int16, "/assistant/goto_ecm_position", self.gotoCurrentEcmPositionAs, 10)

        self.get_logger().info("Running dvrk assistant bridge")

    #--------------------------------------------------------
    # Autocamera Callbacks
    #--------------------------------------------------------
    def autocameraRunCallback(self, data):
        self.get_logger().info("auto camera run callback")
        self.pub_autocamera_run.publish(data)

    def autocameraTrackCallback(self, data):
        self.get_logger().info("auto camera track callback")
        self.pub_autocamera_track.publish(data)

    def autocameraKeepCallback(self, data):
        self.get_logger().info("auto camera keep callback")
        self.pub_autocamera_keep.publish(data)

    def autocameraFindToolsCallback(self, data):
        self.get_logger().info("auto camera find callback")
        self.pub_autocamera_find.publish(data)

    def autocameraInnerZoomCallback(self, data):
        self.get_logger().info("auto camera inner zoom callback")
        self.pub_autocamera_inner_zoom.publish(data)

    def autocameraOuterZoomCallback(self, data):
        self.get_logger().info("auto camera outer zoom callback")
        self.pub_autocamera_outer_zoom.publish(data)

    #--------------------------------------------------------
    # Clutch and Move Callbacks
    #--------------------------------------------------------
    def clutchAndMoveRunCallback(self, data):
        self.get_logger().info("clutch and move callbacks")
        self.pub_clutch_move_run.publish(data)

    #--------------------------------------------------------
    # Joystick Callbacks
    #--------------------------------------------------------
    def joystickRunCallback(self, data):
        self.get_logger().info("Joystick callbacks")
        self.pub_joystick_run.publish(data)

    #--------------------------------------------------------
    # Bleeding Detection Callbacks
    #--------------------------------------------------------
    def bleedingDetectionRunCallback(self, data):
        self.get_logger().info("Bleeding callbacks")
        self.pub_bleeding_run.publish(data)

    #--------------------------------------------------------
    # dvrk Callbacks
    #--------------------------------------------------------
    def home(self, data):
        print("home", flush=True)
        self.get_logger().info("dvrk home")
        self.pub_dvrk_home.publish(Empty())

    def powerOff(self, data):
        self.get_logger().info("dvrk power off")
        self.pub_dvrk_power_off.publish(Empty())

    def reset(self, data):
        self.get_logger().info("dvrk reset")
        q_ecm = [0.0, 0.0, 0.0, 0.0]
        q_psm1 = [0.12544035007602872, 0.2371651265674347, 0.13711766733000003, 0.8391791538250665, -0.12269957678936552, -0.14898520116918784, -0.17461480669754448]
        q_psm2 = [-0.01502071544036667, -0.050506672997428295, 0.14912649789000001, -0.9888977734730169, -0.18391272868428285, -0.05774053780206659, -0.17461480669754453]
        q_mtml = [0.0867019358531589, 0.008250772814637434, 0.1410445179152299, -1.498627346290218, 0.0740159621884837, -0.15691383983958546, 0.00592127680054577, 0.0]
        q_mtmr = [0.13146490673506123, -0.06150289811827064, 0.16527587983749847, 1.5291786517226071, 0.28422129480377745, 0.14211064740188872, 0.05329149120491193, 0.0]
        
        # Accessing global hardware configurations safely
        # __hw_ecm__.move_joint_list(q_ecm, [0,1,2,3], interpolate=True)
        # __hw_psm1__.move_joint_list(q_psm1, interpolate=True)
        # __hw_psm2__.move_joint_list(q_psm2, interpolate=True)
        # __hw_mtml__.move_joint_list(q_mtml, interpolate=True)
        # __hw_mtmr__.move_joint_list(q_mtmr, interpolate=True)
        
    def saveCurrentEcmPositionAs(self, data):
        self.get_logger().info("Save Current ECM Position still in progress")

    def gotoCurrentEcmPositionAs(self, data):
        self.get_logger().info("Go To Current ECM Position still in progress")


def main(args=None):
    rclpy.init(args=args)
    node = AssistantBridge()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()