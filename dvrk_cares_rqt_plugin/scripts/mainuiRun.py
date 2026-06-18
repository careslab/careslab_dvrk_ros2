#!/usr/bin/env python

from tempfile import TemporaryFile
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.uic import loadUi

from mainui import Ui_MainWindow
import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, DurabilityPolicy
from std_msgs.msg import String, Float32, Bool, Int16, Empty
import threading

class MainGUIConnections(QtWidgets.QMainWindow):
    def __init__(self,ui):
        super(MainGUIConnections, self).__init__()
        self.ui = ui
        
        if not rclpy.ok():
            rclpy.init()
        
        self.node = Node("GUI_beacon")
        
        self.executor = rclpy.executors.SingleThreadedExecutor()
        self.executor.add_node(self.node)
        self.thread = threading.Thread(target=self.executor.spin, daemon=True)
        self.thread.start()
        
        latch_qos = QoSProfile(
            depth=1,
            durability=DurabilityPolicy.TRANSIENT_LOCAL
        )
        
        self.pubDict = {}
        self.pubDict["autocamRun"] = self.node.create_publisher(
            Bool, "/assistant/autocamera/run", 10
        )
        self.pubDict["autocamTrack"] = self.node.create_publisher(
            String, "/assistant/autocamera/track", 10
        )
        self.pubDict["home"] = self.node.create_publisher(
            Empty, "/assistant/dvrk_home", 10
        )
        
        self.pubDict["dvrk_on"] = self.node.create_publisher(
            Empty, "/assistant/dvrk_on", latch_qos
        )
        self.pubDict["dvrk_off"] = self.node.create_publisher(
            Empty, "/assistant/dvrk_off", latch_qos
        )
        self.ConnectGUISetUpROS()

    def ConnectGUISetUpROS(self):
        # Configure button clicks
        self.ui.powerOnBtn.clicked.connect(self.powerOnBtnCallback)
        self.ui.powerOffBtn.clicked.connect(self.powerOffBtnCallback)
        self.ui.homeBtn.clicked.connect(self.homeBtnCallback)
        self.ui.AutocameraRadioBtn.toggled.connect(self.autocameraRadioCallback)
        self.ui.TrackRight.clicked.connect(self.TrackRightCallback)
        self.ui.TrackLeft.clicked.connect(self.TrackLeftCallback)
        print('Setup and linked all GUI elements')

    # Callback Functions
    def autocameraRadioCallback(self):
        try:
            if self.ui.AutocameraRadioBtn.isChecked():
                self.pubDict["autocamRun"].publish(Bool(True))
                self.ui.TrackRight.setVisible(True)
                self.ui.TrackLeft.setVisible(True)
                alert = QtWidgets.QMessageBox()
                alert.setText('Turning on autocamera')
                alert.exec_()
            else:
                self.ui.TrackRight.setVisible(False)
                self.ui.TrackLeft.setVisible(False)
                self.pubDict["autocamRun"].publish(Bool(False))
        except Exception:
            print('Error autocamera callback')

    def TrackRightCallback(self):
        try:
            self.pubDict["autocamTrack"].publish("right")
        except Exception:
            print('Error TrackRight callback')
            
    def TrackLeftCallback(self):
        try:
            self.pubDict["autocamTrack"].publish("left")
        except Exception:
            print('Error TrackLeft callback')
            

    def powerOnBtnCallback(self):
        try:
            self.pubDict["dvrk_on"] .publish(Empty())
            self.ui.powerOffBtn.setEnabled(True)
            self.ui.homeBtn.setEnabled(True)
            self.ui.SimulationRadioBtn.setEnabled(True)
            self.ui.HardwareRadioBtn.setEnabled(True)
            self.ui.TeleopRadioBtn.setEnabled(True)
            self.ui.AutocameraRadioBtn.setEnabled(True)
            self.ui.ClutchNMoveRadioBtn.setEnabled(True)
            self.ui.JoystickCtrlRadioBtn.setEnabled(True)
            self.ui.OculusRadioBtn.setEnabled(True)
            self.ui.ClutchlessRadioBtn.setEnabled(True)
            alert = QtWidgets.QMessageBox()
            alert.setText('Turning on daVinci')
            alert.exec_()
        except Exception:
            print('Error turning on')

    def powerOffBtnCallback(self):
        try:
            self.pubDict["dvrk_off"] .publish(Empty())
            self.ui.powerOffBtn.setEnabled(False)
            self.ui.homeBtn.setEnabled(False)
            self.ui.SimulationRadioBtn.setEnabled(False)
            self.ui.HardwareRadioBtn.setEnabled(False)
            self.ui.TeleopRadioBtn.setEnabled(False)
            self.ui.AutocameraRadioBtn.setEnabled(False)
            self.ui.ClutchNMoveRadioBtn.setEnabled(False)
            self.ui.JoystickCtrlRadioBtn.setEnabled(False)
            self.ui.OculusRadioBtn.setEnabled(False)
            self.ui.ClutchlessRadioBtn.setEnabled(False)
            alert = QtWidgets.QMessageBox()
            alert.setText('Turning off daVinci')
            alert.exec_()
        except Exception:
            print('Error turning off')
            
    def homeBtnCallback(self):
        try:
            self.pubDict["home"].publish(Empty())
        except Exception:
            print('Error home button callback')
        
if __name__ == '__main__':
    import sys
    app = QtWidgets.QApplication(sys.argv)
    # create an empty dialog box
    Dialog = QtWidgets.QMainWindow()
    # instance of GUI dialog
    ui = Ui_MainWindow()
    # setup the GUI
    ui.setupUi(Dialog)
    #instance of the MainGUI connection class
    mgui = MainGUIConnections(ui)
    # show the dialgo
    Dialog.show()
    # run until exit
    sys.exit(app.exec_())