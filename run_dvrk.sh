#!/bin/bash
gnome-terminal -- roslaunch autocamera test_hardware.launch &&
gnome-terminal -- rosrun dvrk_autocamera autocamera_control_node.py &&
gnome-terminal -- rosrun dvrk_assistant_bridge bridge
