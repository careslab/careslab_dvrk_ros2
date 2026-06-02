#include <memory>
#include <string>
#include <unordered_map>

#include "rclcpp/rclcpp.hpp"
#include "rclcpp/qos.hpp"
#include "sensor_msgs/msg/joint_state.hpp"
#include "std_msgs/msg/bool.hpp"
#include "std_msgs/msg/empty.hpp"
#include "std_msgs/msg/float32.hpp"
#include "std_msgs/msg/int16.hpp"
#include "std_msgs/msg/string.hpp"

/* bridge2dvrk
 *std_msgs
 * Bridges between a dvrk assistant commands and the actual hardware
 *
 * Publish:   dvrk and dvrk algorithms
 * Subscribe: /assistant/*
 *
 */
class Bridge2Dvrk : public rclcpp::Node
{
public:
    Bridge2Dvrk();

private:
    void autocameraRunCallback(const std_msgs::msg::Bool::SharedPtr msg);
    void autocameraTrackCallback(const std_msgs::msg::String::SharedPtr msg);
    void autocameraKeepCallback(const std_msgs::msg::String::SharedPtr msg);
    void autocameraFindToolsCallback(const std_msgs::msg::Empty::SharedPtr msg);
    void autocameraInnerZoomCallback(const std_msgs::msg::Float32::SharedPtr msg);
    void autocameraOuterZoomCallback(const std_msgs::msg::Float32::SharedPtr msg);

    void clutchAndMoveRunCallback(const std_msgs::msg::Bool::SharedPtr msg);

    void bleedingDetectionRunCallback(const std_msgs::msg::Bool::SharedPtr msg);

    //DVRK Specific controls
    void saveCurrentEcmPositionAs(const std_msgs::msg::Int16::SharedPtr msg);
    void gotoCurrentEcmPositionAs(const std_msgs::msg::Int16::SharedPtr msg);

    void home(const std_msgs::msg::Empty::SharedPtr msg);
    void powerOff(const std_msgs::msg::Empty::SharedPtr msg);
    void ecmJointStateCallback(const sensor_msgs::msg::JointState::SharedPtr msg);

    rclcpp::QoS latchedQos() const
    {
        return rclcpp::QoS(rclcpp::KeepLast(10)).reliable().transient_local();
    }

    template <typename T>
    void publishLatched(const typename rclcpp::Publisher<T>::SharedPtr &publisher,
                       const T &msg)
    {
        publisher->publish(msg);
    }

    rclcpp::Subscription<std_msgs::msg::Bool>::SharedPtr sub_autocamera_run_;
    rclcpp::Subscription<std_msgs::msg::String>::SharedPtr sub_autocamera_track_;
    rclcpp::Subscription<std_msgs::msg::String>::SharedPtr sub_autocamera_keep_;
    rclcpp::Subscription<std_msgs::msg::Empty>::SharedPtr sub_autocamera_find_tools_;
    rclcpp::Subscription<std_msgs::msg::Float32>::SharedPtr sub_autocamera_inner_zoom_;
    rclcpp::Subscription<std_msgs::msg::Float32>::SharedPtr sub_autocamera_outer_zoom_;
    rclcpp::Subscription<std_msgs::msg::Bool>::SharedPtr sub_clutch_and_move_run_;
    rclcpp::Subscription<std_msgs::msg::Bool>::SharedPtr sub_bleeding_detection_run_;
    rclcpp::Subscription<std_msgs::msg::Int16>::SharedPtr sub_save_ecm_position_;
    rclcpp::Subscription<std_msgs::msg::Int16>::SharedPtr sub_goto_ecm_position_;
    rclcpp::Subscription<std_msgs::msg::Empty>::SharedPtr sub_home_;
    rclcpp::Subscription<std_msgs::msg::Empty>::SharedPtr sub_power_off_;
    rclcpp::Subscription<sensor_msgs::msg::JointState>::SharedPtr sub_ecm_joint_state_;

    rclcpp::Publisher<std_msgs::msg::Bool>::SharedPtr pub_autocamera_run_;
    rclcpp::Publisher<std_msgs::msg::String>::SharedPtr pub_autocamera_track_;
    rclcpp::Publisher<std_msgs::msg::String>::SharedPtr pub_autocamera_keep_;
    rclcpp::Publisher<std_msgs::msg::Empty>::SharedPtr pub_autocamera_find_tools_;
    rclcpp::Publisher<std_msgs::msg::Float32>::SharedPtr pub_autocamera_inner_zoom_;
    rclcpp::Publisher<std_msgs::msg::Float32>::SharedPtr pub_autocamera_outer_zoom_;
    rclcpp::Publisher<std_msgs::msg::Bool>::SharedPtr pub_clutch_and_move_run_;
    rclcpp::Publisher<std_msgs::msg::Bool>::SharedPtr pub_bleeding_detection_run_;
    rclcpp::Publisher<std_msgs::msg::Empty>::SharedPtr pub_home_;
    rclcpp::Publisher<std_msgs::msg::Empty>::SharedPtr pub_power_off_;

    sensor_msgs::msg::JointState::SharedPtr last_ecm_joint_state_;
    std::unordered_map<std::string, sensor_msgs::msg::JointState> saved_ecm_positions_map_;
};

// Constructor
//   Set up publisher and subscriber
Bridge2Dvrk::Bridge2Dvrk()
    : Node("assistant_bridge")
{
    auto input_qos = rclcpp::QoS(rclcpp::KeepLast(100));

    pub_autocamera_run_ = create_publisher<std_msgs::msg::Bool>("/autocamera/run", latchedQos());
    pub_autocamera_track_ = create_publisher<std_msgs::msg::String>("/autocamera/track", latchedQos());
    pub_autocamera_keep_ = create_publisher<std_msgs::msg::String>("/autocamera/keep", latchedQos());
    pub_autocamera_find_tools_ = create_publisher<std_msgs::msg::Empty>("/autocamera/find_tools", latchedQos());
    pub_autocamera_inner_zoom_ = create_publisher<std_msgs::msg::Float32>("/autocamera/inner_zoom_value", latchedQos());
    pub_autocamera_outer_zoom_ = create_publisher<std_msgs::msg::Float32>("/autocamera/outer_zoom_value", latchedQos());
    pub_clutch_and_move_run_ = create_publisher<std_msgs::msg::Bool>("/clutch_and_move/run", latchedQos());
    pub_bleeding_detection_run_ = create_publisher<std_msgs::msg::Bool>("/bleeding_detection/run", latchedQos());
    pub_home_ = create_publisher<std_msgs::msg::Empty>("/dvrk/console/home", latchedQos());
    pub_power_off_ = create_publisher<std_msgs::msg::Empty>("/dvrk/console/power_off", latchedQos());

    sub_autocamera_run_ = create_subscription<std_msgs::msg::Bool>(
        "/assistant/autocamera/run", input_qos,
        std::bind(&Bridge2Dvrk::autocameraRunCallback, this, std::placeholders::_1));
    sub_autocamera_track_ = create_subscription<std_msgs::msg::String>(
        "/assistant/autocamera/track", input_qos,
        std::bind(&Bridge2Dvrk::autocameraTrackCallback, this, std::placeholders::_1));
    sub_autocamera_keep_ = create_subscription<std_msgs::msg::String>(
        "/assistant/autocamera/keep", input_qos,
        std::bind(&Bridge2Dvrk::autocameraKeepCallback, this, std::placeholders::_1));
    sub_autocamera_find_tools_ = create_subscription<std_msgs::msg::Empty>(
        "/assistant/autocamera/find_tools", input_qos,
        std::bind(&Bridge2Dvrk::autocameraFindToolsCallback, this, std::placeholders::_1));
    sub_autocamera_inner_zoom_ = create_subscription<std_msgs::msg::Float32>(
        "/assistant/autocamera/inner_zoom_value", input_qos,
        std::bind(&Bridge2Dvrk::autocameraInnerZoomCallback, this, std::placeholders::_1));
    sub_autocamera_outer_zoom_ = create_subscription<std_msgs::msg::Float32>(
        "/assistant/autocamera/outer_zoom_value", input_qos,
        std::bind(&Bridge2Dvrk::autocameraOuterZoomCallback, this, std::placeholders::_1));
    sub_clutch_and_move_run_ = create_subscription<std_msgs::msg::Bool>(
        "/assistant/clutch_and_move/run", input_qos,
        std::bind(&Bridge2Dvrk::clutchAndMoveRunCallback, this, std::placeholders::_1));
    sub_bleeding_detection_run_ = create_subscription<std_msgs::msg::Bool>(
        "/assistant/bleeding_detection/run", input_qos,
        std::bind(&Bridge2Dvrk::bleedingDetectionRunCallback, this, std::placeholders::_1));
    sub_save_ecm_position_ = create_subscription<std_msgs::msg::Int16>(
        "/assistant/save_ecm_position", input_qos,
        std::bind(&Bridge2Dvrk::saveCurrentEcmPositionAs, this, std::placeholders::_1));
    sub_goto_ecm_position_ = create_subscription<std_msgs::msg::Int16>(
        "/assistant/goto_ecm_position", input_qos,
        std::bind(&Bridge2Dvrk::gotoCurrentEcmPositionAs, this, std::placeholders::_1));
    sub_home_ = create_subscription<std_msgs::msg::Empty>(
        "/assistant/home", input_qos,
        std::bind(&Bridge2Dvrk::home, this, std::placeholders::_1));
    sub_power_off_ = create_subscription<std_msgs::msg::Empty>(
        "/assistant/power_off", input_qos,
        std::bind(&Bridge2Dvrk::powerOff, this, std::placeholders::_1));
    sub_ecm_joint_state_ = create_subscription<sensor_msgs::msg::JointState>(
        "/dvrk_ecm/joint_states", rclcpp::QoS(rclcpp::KeepLast(10)),
        std::bind(&Bridge2Dvrk::ecmJointStateCallback, this, std::placeholders::_1));
}

// Callback function for the run
void Bridge2Dvrk::autocameraRunCallback(const std_msgs::msg::Bool::SharedPtr msg)
{
    publishLatched(pub_autocamera_run_, *msg);
}
// Callback function for the track
void Bridge2Dvrk::autocameraTrackCallback(const std_msgs::msg::String::SharedPtr msg)
{
    publishLatched(pub_autocamera_track_, *msg);
}
// Callback function for the keep
void Bridge2Dvrk::autocameraKeepCallback(const std_msgs::msg::String::SharedPtr msg)
{
    publishLatched(pub_autocamera_keep_, *msg);
}
// Callback function for the find_tools
void Bridge2Dvrk::autocameraFindToolsCallback(const std_msgs::msg::Empty::SharedPtr msg)
{
    publishLatched(pub_autocamera_find_tools_, *msg);
}
// Callback function for the inner_zoom_value
void Bridge2Dvrk::autocameraInnerZoomCallback(const std_msgs::msg::Float32::SharedPtr msg)
{
    publishLatched(pub_autocamera_inner_zoom_, *msg);
}
// Callback function for the outer_zoom_value
void Bridge2Dvrk::autocameraOuterZoomCallback(const std_msgs::msg::Float32::SharedPtr msg)
{
   publishLatched(pub_autocamera_outer_zoom_, *msg);
}


// Callback function for the run
void Bridge2Dvrk::clutchAndMoveRunCallback(const std_msgs::msg::Bool::SharedPtr msg)
{
    publishLatched(pub_clutch_and_move_run_, *msg);
}

// Callback function for the run
void Bridge2Dvrk::bleedingDetectionRunCallback(const std_msgs::msg::Bool::SharedPtr msg)
{
    publishLatched(pub_bleeding_detection_run_, *msg);
}


void Bridge2Dvrk::home(const std_msgs::msg::Empty::SharedPtr msg)
{
    publishLatched(pub_home_, *msg);
}
void Bridge2Dvrk::powerOff(const std_msgs::msg::Empty::SharedPtr msg)
{
    publishLatched(pub_power_off_, *msg);
}

void Bridge2Dvrk::ecmJointStateCallback(const sensor_msgs::msg::JointState::SharedPtr msg)
{
    last_ecm_joint_state_ = msg;
}

void Bridge2Dvrk::saveCurrentEcmPositionAs(const std_msgs::msg::Int16::SharedPtr msg)
{
    if (!last_ecm_joint_state_) {
        RCLCPP_WARN(get_logger(), "No /dvrk_ecm/joint_states received yet; cannot save position");
        return;
    }
    saved_ecm_positions_map_[std::to_string(msg->data)] = *last_ecm_joint_state_;
    RCLCPP_INFO(get_logger(), "Saved ECM position with id %d", msg->data);
}

void Bridge2Dvrk::gotoCurrentEcmPositionAs(const std_msgs::msg::Int16::SharedPtr msg)
{

//     """Move the arm to the end vector by passing the trajectory generator.

//         :param end_joint: the list of joints in which you should conclude movement
//         :returns: true if you had succesfully move
//         :rtype: Bool"""
// #         rospy.loginfo(rospy.get_caller_id() + ' -> starting move joint direct')
//         if (self.__check_input_type(end_joint, [list,float])):
//             if not self.__dvrk_set_state('DVRK_POSITION_JOINT'):
//                 return False
//             # go to that position directly
//             joint_state = JointState()
//             joint_state.position[:] = end_joint
//             self.set_position_joint_publisher.publish(joint_state)
//
//self.__full_ros_namespace+ '/set_position_joint
    (void)msg;
    RCLCPP_WARN(get_logger(), "gotoCurrentEcmPositionAs is not implemented yet in ROS2 bridge");
}

int main(int argc, char **argv)
{
    rclcpp::init(argc, argv);
    auto node = std::make_shared<Bridge2Dvrk>();
    RCLCPP_INFO(node->get_logger(), "Running dvrk assistant bridge");
    rclcpp::spin(node);
    rclcpp::shutdown();
    return 0;
}
