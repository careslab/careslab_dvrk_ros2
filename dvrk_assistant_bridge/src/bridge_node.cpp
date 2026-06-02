#include <ros/ros.h>
#include <std_msgs/Empty.h>
#include <std_msgs/String.h>
#include <std_msgs/Bool.h>
#include <std_msgs/Float32.h>
#include <sensor_msgs/JointState.h>
#include <std_msgs/Int16.h>
#include <boost/shared_ptr.hpp>

/* bridge2dvrk
 *std_msgs
 * Bridges between a dvrk assistant commands and the actual hardware
 *
 * Publish:   dvrk and dvrk algorithms
 * Subscribe: /assistant/*
 *
 */
class bridge2dvrk
{
public:
    bridge2dvrk();

private:
    void autocameraRunCallback(const std_msgs::Bool::ConstPtr &msg);
    void autocameraTrackCallback(const std_msgs::String::ConstPtr &msg);
    void autocameraKeepCallback(const std_msgs::String::ConstPtr &msg);
    void autocameraFindToolsCallback(const std_msgs::Empty::ConstPtr &msg);
    void autocameraInnerZoomCallback(const std_msgs::Float32::ConstPtr &msg);
    void autocameraOuterZoomCallback(const std_msgs::Float32::ConstPtr &msg);

    void clutchAndMoveRunCallback(const std_msgs::Bool::ConstPtr &msg);

    void bleedingDetectionRunCallback(const std_msgs::Bool::ConstPtr &msg);

    //DVRK Specific controls
    void saveCurrentEcmPositionAs(const std_msgs::Int16::ConstPtr &msg);
    void gotoCurrentEcmPositionAs(const std_msgs::Int16::ConstPtr &msg);

    void home(const std_msgs::Empty::ConstPtr &msg);
    void powerOff(const std_msgs::Empty::ConstPtr &msg);

    // ROS objects
    ros::NodeHandle mNodeHandle;
    std::map<std::string, ros::Subscriber> mSubscriberMap;
    std::map<std::string, sensor_msgs::JointState> mSavedEcmPositionsMap;
    ros::Subscriber point_sub_;
};

// Constructor
//   Set up publisher and subscriber
bridge2dvrk::bridge2dvrk()
{
    /*****SUBSCRIBER SETUP******/

    //-----------Autocamera-----------------
    //Bool: *True or *False
    mSubscriberMap["autocamera_run"] = mNodeHandle.subscribe("/assistant/autocamera/run", 100, &bridge2dvrk::autocameraRunCallback, this);
    //String: *Right, *Left, or *Middle
    mSubscriberMap["autocamera_track"] = mNodeHandle.subscribe("/assistant/autocamera/track", 100, &bridge2dvrk::autocameraTrackCallback, this);
    //String: *Right, *Left, or *Middle
    mSubscriberMap["autocamera_keep"] = mNodeHandle.subscribe("/assistant/autocamera/keep", 100, &bridge2dvrk::autocameraKeepCallback, this);
    //Empty:
    mSubscriberMap["autocamera_find_tools"] = mNodeHandle.subscribe("/assistant/autocamera/find_tools", 100, &bridge2dvrk::autocameraFindToolsCallback, this);
    //Float32:
    mSubscriberMap["autocamera_inner_zoom_value"] = mNodeHandle.subscribe("/assistant/autocamera/inner_zoom_value", 100, &bridge2dvrk::autocameraInnerZoomCallback, this);
    //Float32:
    mSubscriberMap["autocamera_outer_zoom_value"] = mNodeHandle.subscribe("/assistant/autocamera/outer_zoom_value", 100, &bridge2dvrk::autocameraOuterZoomCallback, this);


    //-----------Clutch and Move-----------------
    //Bool: *True or *False
    mSubscriberMap["clutch_and_move_run"] = mNodeHandle.subscribe("/assistant/clutch_and_move/run", 100, &bridge2dvrk::clutchAndMoveRunCallback, this);

    //-----------Bleeding Detection-----------------
    //Bool: *True or *False
    mSubscriberMap["bleed_run"] = mNodeHandle.subscribe("/assistant/bleeding_detection/run", 100, &bridge2dvrk::bleedingDetectionRunCallback, this);

    //-----------DVRK Specific Functions-----------------
    //Int16 with save position name
    mSubscriberMap["save_ecm_position"] = mNodeHandle.subscribe("/assistant/save_ecm_position", 100, &bridge2dvrk::saveCurrentEcmPositionAs, this);
    //Int16 with save go to name
    mSubscriberMap["goto_ecm_position"] = mNodeHandle.subscribe("/assistant/goto_ecm_position", 100, &bridge2dvrk::gotoCurrentEcmPositionAs, this);
    //Empty:
    mSubscriberMap["home"] = mNodeHandle.subscribe("/assistant/home", 100, &bridge2dvrk::home, this);
    //Empty:
    mSubscriberMap["power_off"] = mNodeHandle.subscribe("/assistant/power_off", 100, &bridge2dvrk::powerOff, this);
}

// Callback function for the run
void bridge2dvrk::autocameraRunCallback(const std_msgs::Bool::ConstPtr &msg)
{
    mNodeHandle.advertise<std_msgs::Bool>("/autocamera/run", 10, true).publish(msg);
}
// Callback function for the track
void bridge2dvrk::autocameraTrackCallback(const std_msgs::String::ConstPtr &msg)
{
    mNodeHandle.advertise<std_msgs::String>("/autocamera/track", 10, true).publish(msg);
}
// Callback function for the keep
void bridge2dvrk::autocameraKeepCallback(const std_msgs::String::ConstPtr &msg)
{
    mNodeHandle.advertise<std_msgs::String>("/autocamera/keep", 10,  true).publish(msg);
}
// Callback function for the find_tools
void bridge2dvrk::autocameraFindToolsCallback(const std_msgs::Empty::ConstPtr &msg)
{
    mNodeHandle.advertise<std_msgs::Empty>("/autocamera/find_tools", 10, true).publish(msg);
}
// Callback function for the inner_zoom_value
void bridge2dvrk::autocameraInnerZoomCallback(const std_msgs::Float32::ConstPtr &msg)
{
    mNodeHandle.advertise<std_msgs::Float32>("/autocamera/inner_zoom_value", 10,true).publish(msg);
}
// Callback function for the outer_zoom_value
void bridge2dvrk::autocameraOuterZoomCallback(const std_msgs::Float32::ConstPtr &msg)
{
   mNodeHandle.advertise<std_msgs::Float32>("/autocamera/outer_zoom_value", 10,true).publish(msg);
}


// Callback function for the run
void bridge2dvrk::clutchAndMoveRunCallback(const std_msgs::Bool::ConstPtr &msg)
{
    mNodeHandle.advertise<std_msgs::Bool>("/clutch_and_move/run", 10, true).publish(msg);
}

// Callback function for the run
void bridge2dvrk::bleedingDetectionRunCallback(const std_msgs::Bool::ConstPtr &msg)
{
    mNodeHandle.advertise<std_msgs::Bool>("/bleeding_detection/run", 10, false).publish(msg);
}


void bridge2dvrk::home(const std_msgs::Empty::ConstPtr &msg)
{
    mNodeHandle.advertise<std_msgs::Empty>("/dvrk/console/home", 10, true).publish(msg);
}
void bridge2dvrk::powerOff(const std_msgs::Empty::ConstPtr &msg)
{
    mNodeHandle.advertise<std_msgs::Empty>("/dvrk/console/power_off", 10, true).publish(msg);
}

void bridge2dvrk::saveCurrentEcmPositionAs(const std_msgs::Int16::ConstPtr &msg)
{
    //This smart ptr and subsequent waitForMessage allows you to get data once without a subscriber
    boost::shared_ptr<sensor_msgs::JointState const> sharedPtr;
    sensor_msgs::JointState js;

    //Get joint angles from the simulation
    sharedPtr  = ros::topic::waitForMessage<sensor_msgs::JointState>("/dvrk_ecm/joint_states", ros::Duration(1));
    if (sharedPtr == NULL)
    {
        ROS_INFO("No Current Joint angle messages received");
    }
    else
    {
        js = *sharedPtr;
        mSavedEcmPositionsMap[std::to_string(msg->data)] = js; 
    }

}
void bridge2dvrk::gotoCurrentEcmPositionAs(const std_msgs::Int16::ConstPtr &msg)
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
}

int main(int argc, char **argv)
{
    ROS_INFO_STREAM("Running dvrk assistant bridge!!");
    ros::init(argc, argv, "assistant_bridge");
    bridge2dvrk b;

    ros::spin();
}
