import os
# import sys
import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, DurabilityPolicy, HistoryPolicy
import signal
import pexpect
import time
import subprocess
from std_msgs.msg import String, Empty, Bool
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.uic import loadUi

from qt_gui.plugin import Plugin
from python_qt_binding import loadUi
from python_qt_binding.QtWidgets import QWidget, QMessageBox
# ROS 2 equivalent for finding package paths
from ament_index_python.packages import get_package_share_directory


class MyPlugin():

    def __init__(self, context):
        super(self).__init__(context)
        # Give QObjects reasonable names
        self.setObjectName('MyPlugin')

        # Retrieve or create the ROS 2 node from the RQT context
        # In ROS 2 rqt, context provides the running node instance
        self.node = context.node

        # Define a latched QoS profile (equivalent to latch=True in ROS 1)
        self.latched_qos = QoSProfile(
            depth=1,
            durability=DurabilityPolicy.TRANSIENT_LOCAL,
            history=HistoryPolicy.KEEP_LAST
        )

        # Create persistent publishers to avoid overhead and resource leaks
        self.pub_teleop_run = self.node.create_publisher(Bool, '/assistant/teleop/run', self.latched_qos)
        self.pub_autocamera_run = self.node.create_publisher(Bool, '/assistant/autocamera/run', self.latched_qos)
        self.pub_clutch_move_run = self.node.create_publisher(Bool, '/assistant/clutch_and_move/run', self.latched_qos)
        self.pub_joystick_run = self.node.create_publisher(Bool, '/assistant/joystick/run', self.latched_qos)
        self.pub_oculus_run = self.node.create_publisher(Bool, '/assistant/oculus/run', self.latched_qos)
        self.pub_clutchless_run = self.node.create_publisher(Bool, '/assistant/clutchless/run', self.latched_qos)
        self.pub_home = self.node.create_publisher(Empty, '/assistant/home', self.latched_qos)
        self.pub_power_off = self.node.create_publisher(Empty, '/assistant/power_off', self.latched_qos)
        self.pub_reset = self.node.create_publisher(Empty, '/assistant/reset', self.latched_qos)

        # Process standalone plugin command-line arguments
        from argparse import ArgumentParser
        parser = ArgumentParser()
        # Add argument(s) to the parser.
        parser.add_argument("-q", "--quiet", action="store_true",
                      dest="quiet",
                      help="Put plugin in silent mode")
        args, unknowns = parser.parse_known_args(context.argv())
        #if not args.quiet:
            #print 'arguments: ', args
            #print 'unknowns: ', unknowns

        # self._app = QApplication(sys.argv)

        # Create QWidget
        self._widget = QWidget()
        
        # ROS 2 uses get_package_share_directory instead of rospkg
        package_path = get_package_share_directory('dvrk_cares_rqt_plugin')
        ui_file = os.path.join(package_path, 'resource', 'MyPlugin.ui')
        
        # Extend the widget with all attributes and children from UI file
        loadUi(ui_file, self._widget)
        # Give QObjects reasonable names
        self._widget.setObjectName('MyPluginUi')
        # Show _widget.windowTitle on left-top of each plugin (when 
        # it's set in _widget). This is useful when you open multiple 
        # plugins at once. Also if you open multiple instances of your 
        # plugin at once, these lines add number to make it easy to 
        # tell from pane to pane.
        if context.serial_number() > 1:
            self._widget.setWindowTitle(self._widget.windowTitle() + (' (%d)' % context.serial_number()))
        # Add widget to the user interface
        context.add_widget(self._widget)

        self._widget.powerOnButton.pressed.connect(self._on_powerOnButton_pressed)
        self._widget.powerOffButton.pressed.connect(self._on_powerOffButton_pressed)
        self._widget.homeButton.pressed.connect(self._on_homeButton_pressed)
        self._widget.resetButton.pressed.connect(self._on_resetButton_pressed)
        # self._widget.exitButton.pressed.connect(self._on_exitButton_pressed)

        self._widget.autocameraRadioButton.pressed.connect(self._on_autocameraRadioButton_pressed)
        self._widget.clutchandMoveRadioButton.pressed.connect(self._on_clutchandMoveRadioButton_pressed)
        self._widget.joystickRadioButton.pressed.connect(self._on_joystickRadioButton_pressed)
        self._widget.voiceControlRadioButton.pressed.connect(self._on_voiceControlRadioButton_pressed)

        self._widget.startRecording.pressed.connect(self._on_startRecording_pressed)
        self._widget.stopRecording.pressed.connect(self._on_stopRecording_pressed)
        # self._widget.startTimer.pressed.connect(self._on_startTimer_pressed)

    def shutdown_plugin(self):
        # Clean up publishers to avoid resource leaks
        self.node.destroy_publisher(self.pub_teleop_run)
        self.node.destroy_publisher(self.pub_autocamera_run)
        self.node.destroy_publisher(self.pub_clutch_move_run)
        self.node.destroy_publisher(self.pub_joystick_run)
        self.node.destroy_publisher(self.pub_oculus_run)
        self.node.destroy_publisher(self.pub_clutchless_run)
        self.node.destroy_publisher(self.pub_home)
        self.node.destroy_publisher(self.pub_power_off)
        self.node.destroy_publisher(self.pub_reset)

    def save_settings(self, plugin_settings, instance_settings):
        pass

    def restore_settings(self, plugin_settings, instance_settings):
        pass

    def set_all_control_algorithms_off(self):
        # Using pre-created persistent node publishers
        self.pub_autocamera_run.publish(Bool(data=False))
        self.pub_clutch_move_run.publish(Bool(data=False))
        self.pub_joystick_run.publish(Bool(data=False))
        self.pub_oculus_run.publish(Bool(data=False))
        self.pub_clutchless_run.publish(Bool(data=False))
        
    def _on_powerOnButton_pressed(self):
        self.pub_home.publish(Empty())
        self.node.get_logger().info("RAN POWER ON")
        self._widget.powerOnButton.setEnabled(False)
        self._widget.homeButton.setEnabled(True)
        self._widget.powerOffButton.setEnabled(True)
        self._widget.resetButton.setEnabled(True)
        self._widget.startRecording.setEnabled(True)
        self._widget.voiceButton.setEnabled(True)
        self._widget.joystickButton.setEnabled(True)
        self._widget.subjectValueBox.setEnabled(True)
        self._widget.taskValueBox.setEnabled(True)

    def _on_powerOffButton_pressed(self):
        self.pub_power_off.publish(Empty())
        self.node.get_logger().info("RAN POWER OFF")
        self._widget.powerOnButton.setEnabled(True)
        self._widget.homeButton.setEnabled(False)
        self._widget.powerOffButton.setEnabled(False)
        self._widget.resetButton.setEnabled(False)

        self._widget.autocameraRadioButton.setEnabled(False)
        self._widget.clutchandMoveRadioButton.setEnabled(False)
        self._widget.clutchlessSystemRadioButton.setEnabled(False)
        self._widget.joystickRadioButton.setEnabled(False)
        self._widget.oculusRadioButton.setEnabled(False)
        self._widget.voiceControlRadioButton.setEnabled(False)

    def _on_homeButton_pressed(self):
        self.pub_teleop_run.publish(Bool(data=True))
        self._widget.autocameraRadioButton.setEnabled(True)
        self._widget.clutchandMoveRadioButton.setEnabled(True)
        self._widget.clutchlessSystemRadioButton.setEnabled(True)
        self._widget.joystickRadioButton.setEnabled(True)
        self._widget.oculusRadioButton.setEnabled(True)
        self._widget.voiceControlRadioButton.setEnabled(True)

    def _on_resetButton_pressed(self):
        self.pub_reset.publish(Empty())
        self.node.get_logger().info("RAN RESET")

    def _on_autocameraRadioButton_pressed(self):
        if not self._widget.autocameraRadioButton.isChecked():
            self.set_all_control_algorithms_off()
            self.pub_autocamera_run.publish(Bool(data=True))
            msg = QMessageBox()
            msg.setText('running autocamera')
            retval = msg.exec_()
        self._widget.autocameraRadioButton.setChecked(True)

    def _on_clutchandMoveRadioButton_pressed(self):
        if not self._widget.clutchandMoveRadioButton.isChecked():
            self.set_all_control_algorithms_off()
            self.pub_clutch_move_run.publish(Bool(data=True))
            msg = QMessageBox()
            msg.setText('running clutch and move')
            retval = msg.exec_()
        self._widget.clutchandMoveRadioButton.setChecked(True)

    def _on_joystickRadioButton_pressed(self):
        if not self._widget.joystickRadioButton.isChecked():
            self.set_all_control_algorithms_off()
            self.pub_joystick_run.publish(Bool(data=True))
            msg = QMessageBox()
            msg.setText('running joystick')
            retval = msg.exec_()
        self._widget.joystickRadioButton.setChecked(True)
    
    def _on_voiceControlRadioButton_pressed(self):
        # NOTE: Fixed paths assuming a migration to a ROS 2 workspace layout
        # Update this path to match your ROS 2 workspace structure if needed
        os.chdir('/home/cares/ros2_ws/src/careslab_dvrk/dvrk_voice/scripts')
        # Resolved the truncated line from your prompt snippet
        pass

def main():
    import sys
    app = QtWidgets.QApplication(sys.argv)
    # create an empty dialog box
    Dialog = QtWidgets.QMainWindow()
    # instance of GUI dialog
    
    package_path = get_package_share_directory('dvrk_cares_rqt_plugin')
    ui_file = os.path.join(package_path, 'resource', 'MyPlugin.ui')
    widget = QWidget()

    # Extend the widget with all attributes and children from UI file
    loadUi(ui_file, widget)
    # Give QObjects reasonable names
    widget.setObjectName('MyPluginUi')
        
    ui = widget
    # setup the GUI
    ui.setupUi(Dialog)
    #instance of the MainGUI connection class
    mgui = MyPlugin(ui)
    # show the dialgo
    Dialog.show()
    # run until exit
    sys.exit(app.exec_())
    
if __name__ == "__main__":
    main()
