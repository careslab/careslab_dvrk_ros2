import os
import cv2
import math
import time
import rclpy
import rosbag2_py
import cv_bridge
import numpy as np
import image_geometry
from rclpy.node import Node

from arm import arm as robot
from kdl_parser_py import urdf
import PyKDL
from std_msgs.msg import Bool, String, Empty, Float32
from sensor_msgs.msg import JointState, CameraInfo, Image, CompressedImage, Joy
from geometry_msgs.msg import PoseStamped, Pose, Wrench, Quaternion, PolygonStamped, Point32, Point
from visualization_msgs.msg import Marker
from types import NoneType
# from hrl_geom import pose_converter
# from hrl_geom.pose_converter import PoseConv
from math import acos, atan2, cos, pi, sin
from numpy import array, cross, dot, float64, hypot, zeros, rot90
from numpy.linalg import norm
from ament_index_python.packages import get_package_share_directory

import xacro


_marker_node = None
model_dir = os.path.join(get_package_share_directory('dvrk_model'), 'urdf')

def _get_marker_node():
    global _marker_node
    if _marker_node is None:
        if not rclpy.ok():
            rclpy.init(args=None)
        _marker_node = Node('autocamera_common_imports')
    return _marker_node

def add_marker(pose, name, color=[1,0,1], type=Marker.SPHERE, scale = [.02,.02,.02], points=None, frame = "world"):
        marker_node = _get_marker_node()
        vis_pub = marker_node.create_publisher(Marker, name, 10)
        marker = Marker()
        marker.header.frame_id = frame
        marker.header.stamp = marker_node.get_clock().now().to_msg()
        marker.ns = "my_namespace"
        marker.id = 0
        marker.type = type
        marker.action = Marker.ADD
        
        if type == Marker.LINE_LIST:
            for point in points:
                p = Point()
                p.x = point[0]
                p.y = point[1]
                p.z = point[2]
                marker.points.append(p)
        else:
            r = find_rotation_matrix_between_two_vectors([1,0,0], [0,0,1])
            rot = pose[0:3,0:3] * r
            pose2 = np.matrix(np.identity(4))
            pose2[0:3,0:3] = rot
            pose2[0:3,3] = pose[0:3,3]
            quat_pose = PoseConv.to_pos_quat(pose2)
            
            marker.pose.position.x = quat_pose[0][0]
            marker.pose.position.y = quat_pose[0][1]
            marker.pose.position.z = quat_pose[0][2]
            marker.pose.orientation.x = quat_pose[1][0]
            marker.pose.orientation.y = quat_pose[1][1] 
            marker.pose.orientation.z = quat_pose[1][2]
            marker.pose.orientation.w = quat_pose[1][3] 
            
        marker.scale.x = scale[0]
        marker.scale.y = scale[1]
        marker.scale.z = scale[2]
        marker.color.a = .5
        marker.color.r = color[0]
        marker.color.g = color[1]
        marker.color.b = color[2]
        
        
        
        vis_pub.publish(marker)
        

def find_rotation_matrix_between_two_vectors(a,b):
        """!
            Returns a rotation matrix between vectors a and b
            @param a : A vector
            @param b : A vector
            @return R : A 3x3 rotation matrix
        """
        a = np.array(a).reshape(1,3)[0].tolist()
        b = np.array(b).reshape(1,3)[0].tolist()
        
        vector_orig = a / norm(a)
        vector_fin = b / norm(b)
                     
        # The rotation axis (normalised).
        axis = cross(vector_orig, vector_fin)
        axis_len = norm(axis)
        if axis_len != 0.0:
            axis = axis / axis_len
    
        # Alias the axis coordinates.
        x = axis[0]
        y = axis[1]
        z = axis[2]
    
        # The rotation angle.
        angle = acos(dot(vector_orig, vector_fin))
    
        # Trig functions (only need to do this maths once!).
        ca = cos(angle)
        sa = sin(angle)
        R = np.identity(3)
        # Calculate the rotation matrix elements.
        R[0,0] = 1.0 + (1.0 - ca)*(x**2 - 1.0)
        R[0,1] = -z*sa + (1.0 - ca)*x*y
        R[0,2] = y*sa + (1.0 - ca)*x*z
        R[1,0] = z*sa+(1.0 - ca)*x*y
        R[1,1] = 1.0 + (1.0 - ca)*(y**2 - 1.0)
        R[1,2] = -x*sa+(1.0 - ca)*y*z
        R[2,0] = -y*sa+(1.0 - ca)*x*z
        R[2,1] = x*sa+(1.0 - ca)*y*z
        R[2,2] = 1.0 + (1.0 - ca)*(z**2 - 1.0)
        
        R = np.matrix(R)
        return R 
    
def distance(a, b):
    return math.sqrt( sum([ (i-j)**2 for i,j in zip(a,b)]) )

def get_psm1_chain():
    psm1_urdf_path = os.path.join(model_dir, 'Classic', 'PSM1.urdf.xacro')
    print(f"Loading PSM1 from: {psm1_urdf_path}")
    xml_string = xacro.process_file(psm1_urdf_path, mappings={'arm': 'psm1'}).toxml()
    
    with open(os.path.join(os.path.dirname(__file__), '../../psm1_xml.xml'), 'w') as f:
        f.write(xml_string)
        
    ok, psm1_tree = urdf.treeFromString(xml_string)
    psm1_kin = psm1_tree.getChain("world", "psm1_tool_tip_link")
    return psm1_kin         

def get_psm2_chain():
    psm2_urdf_path = os.path.join(model_dir, 'Classic', 'PSM2.urdf.xacro')
    print(f"Loading PSM2 from: {psm2_urdf_path}")
    xml_string = xacro.process_file(psm2_urdf_path, mappings={'arm': 'psm2'}).toxml()
    
    with open(os.path.join(os.path.dirname(__file__), '../../psm2_xml.xml'), 'w') as f:
        f.write(xml_string)
        
    ok, psm2_tree = urdf.treeFromString(xml_string)
    psm2_kin = psm2_tree.getChain("world", "PSM2_tool_wrist_caudier_ee_link")
    return psm2_kin  

def get_ecm_chain():
    ecm_urdf_path = os.path.join(model_dir, 'Classic', 'ecm.urdf.xacro')
    print(f"Loading ECM from: {ecm_urdf_path}")
    xml_string = xacro.process_file(ecm_urdf_path, mappings={'arm': 'ecm'}).toxml()
    
    with open(os.path.join(os.path.dirname(__file__), '../../ecm_xml.xml'), 'w') as f:
        f.write(xml_string)
        
    ok, ecm_tree = urdf.treeFromString(xml_string)
    ecm_kin = ecm_tree.getChain("world", "ecm_end_link")
    return ecm_kin
        