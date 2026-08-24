'''!
@author : Shahab Eslamian
@contact: shahab.eslamian@wayne.edu
'''

from __future__ import division
from turtle import forward
from __common_imports__ import *

import sys
import rclpy
import xacro
import re
import pdb
import os
import geometry_msgs
import cv2
import tf2_ros
import numpy as np
from scipy.spatial.transform import Rotation as ScipyRotation
from rclpy.node import Node
from urdf_kdl_utils import forward_kinematics, pos_rot_to_homo_mat, to_homo_mat, to_pos_euler


class Autocamera:
    """!
        A class for autonomous manipulation of the camera arm in the da Vinci Standard 
        surgical robot
    """
    DEBUG = False # Print debug messages?

    def __init__(self):
        """!
            Class initialization function
        """
        print("Starting autocamera algorithm node")
        if not rclpy.ok():
            rclpy.init(args=None)
        self._node = Node('autocamera_algorithm')

        self.method_number = 1
        self.z = 0.0
        self.deadzone_margin_3d = .15
        self.tools_in_view = 2
        
        self.deadzone_3d = [{'x':-1, 'y':-1}, {'x':-1, 'y':1}, {'x':1, 'y':1}, {'x':1, 'y':-1}]
        
        # ECM to World transform
        self.__T_ecm__ = None
        
        self.psm1_kin = get_psm1_chain()      
        self.ecm_kin = get_ecm_chain()
        self.psm2_kin = get_psm2_chain()
        
        self.zoom_percentage = 1
        
        self.tool_timer = {'last_psm1_pos':None, 'last_psm2_pos':None, 'psm1_stay_start_time':0, 'psm2_stay_start_time':0, 'psm1_stationary_duration':0, 'psm2_stationary_duration':0}
        
        self.keepPos = None;
        self.keepSet = False;
        
        self.last_midpoint = None
        self.midpoint_time = 0
        self.pan_tilt_deadzone_radius = .001
        self.distance_to_midpoint = None
        
        #These parameters determine the distance (in pixels?) between tools for zoom 
        self.zoom_deadzone_radius = .2
        self.zoom_innerzone_radius = .1
        self.zones_times = {'inner_zone':0, 'outer_zone':0} # Keep track of how long the tools are in each of these 2 zones
        
        self.zoom_level_positions = {'l1':None, 'r1':None, 'l2':None, 'r2':None, 'lm':None, 'rm':None}
        self.logerror("autocamera_initialized")

        #Reenu added below lines for dvrk_safety(psm_safety)
        self.psm1_pos_transformed = self._node.create_publisher(Point, '/autocamera/PSM1/transformed_position', 1)
        self.psm2_pos_transformed = self._node.create_publisher(Point, '/autocamera/PSM2/transformed_position', 1)
           
    def set_keep_pos(self, tool, joint):
        kinematics = lambda name: self.psm1_kin if name == 'psm1' else self.psm2_kin if name == 'psm2' else self.ecm_kin 
        clean_joints = {}
        try:
            joint_names = joint.keys()
            for j in joint_names:
                clean_joints[j] = self.extract_positions(joint[j], j, kinematics(j))

            if tool == 'right':
                self.keepPos,_ = self.psm1_kin.FK(clean_joints['psm1'].position)
                self.keepSet = True;
            elif tool == 'left':
                self.keepPos,_ = self.psm2_kin.FK(clean_joints['psm2'].position)
                self.keepSet = True;
            elif tool == 'middle':
                self.keepSet = False;

            print(self.keepSet)

        except Exception as e:
            self._node.get_logger().error(str(e))
            output_msg = joint['ecm']
    #         output_msg.name = ['outer_yaw', 'outer_pitch', 'insertion', 'outer_roll']
    #         output_msg.position = [joint['ecm'].position[x] for x in [0,1,5,6]]
            return
        
        return


        
    def logerror(self, msg, debug = False):
        if self.DEBUG or debug:
            self._node.get_logger().error(str(msg))
            
    def dotproduct(self, v1, v2):
        return sum((a*b) for a, b in zip(v1, v2))
    
    def length(self, v):
        return math.sqrt(self.dotproduct(v, v))
    
    def angle(self, v1, v2):
        return math.acos(self.dotproduct(v1, v2) / (self.length(v1) * self.length(v2)))
      
    def column(self, matrix, i):
        return [row[i] for row in matrix]
    
    def find_rotation_matrix_between_two_vectors(self, a,b):
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
        
        
    def extract_positions(self, joint, arm_name, joint_kin=None):
        
        arm_name = arm_name.lower()
        
        if arm_name=="ecm": joint_kin = self.ecm_kin
        elif arm_name =="psm1" : joint_kin = self.psm1_kin
        elif arm_name =="psm2" : joint_kin = self.psm2_kin
                
        pos = []

        new_joint = JointState()
        for i in range(len(joint.position)):
            pos.append(joint.position[i])

        new_joint.position = pos
        return new_joint
                
    def add_marker(self, pose, name, color=[1,0,1], type=Marker.SPHERE, scale = [.02,.02,.02], points=None, frame = "world"):
        vis_pub = self._node.create_publisher(Marker, name, 10)
        marker = Marker()
        marker.header.frame_id = frame
        marker.header.stamp = self._node.get_clock().now().to_msg()
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
            r = self.find_rotation_matrix_between_two_vectors([1,0,0], [0,0,1])
            rot = pose[0:3,0:3] * r
            pose2 = np.matrix(np.identity(4))
            pose2[0:3,0:3] = rot
            pose2[0:3,3] = np.asarray(pose[0:3,3]).reshape(-1, 1)
            # Convert homogeneous matrix to position + quaternion using scipy
            rotation_matrix = np.array(pose2[0:3, 0:3])
            position = np.array(pose2[0:3, 3]).flatten()
            quat = ScipyRotation.from_matrix(rotation_matrix).as_quat()
            quat_pose = (position, quat)
            
            marker.pose.position.x = quat_pose[0][0]
            marker.pose.position.y = quat_pose[0][1]
            marker.pose.position.z = quat_pose[0][2]
            marker.pose.orientation.x = quat_pose[1][0]
            marker.pose.orientation.y = quat_pose[1][1] 
            marker.pose.orientation.z = quat_pose[1][2]
            marker.pose.orientation.w = quat_pose[1][3] 
            
        marker.scale.x = float(scale[0])
        marker.scale.y = float(scale[1])
        marker.scale.z = float(scale[2])
        marker.color.a = 0.5
        marker.color.r = float(color[0])
        marker.color.g = float(color[1])
        marker.color.b = float(color[2])
        
        
        
        vis_pub.publish(marker)
        
    
    def point_towards_midpoint(self, clean_joints, psm1_pos, psm2_pos, key_hole,ecm_pose, cam_info, pos_track):
        if pos_track == 'left':
            mid_point = psm2_pos
            if self.keepSet:
                mid_point = (psm2_pos + self.keepPos)/2
        elif pos_track == 'right':
            mid_point = psm1_pos
            if self.keepSet:
                mid_point = (psm1_pos+self.keepPos)/2
        else:
            mid_point = (psm1_pos + psm2_pos)/2
            if self.keepSet:
                mid_point = (psm1_pos + psm2_pos + self.keepPos)/3

#         diff = clean_joints['psm1'].position[2] - clean_joints['psm2'].position[2]
#         if diff > 0:
#             mid_point = (psm1_pos * (1+np.abs(diff)/1) + psm2_pos)/2
#         elif diff < 0:
#             mid_point = (psm1_pos + psm2_pos * (1+np.abs(diff)/1) )/2
#         else:
#             mid_point = (psm1_pos + psm2_pos)/2
#             
#         l1,l2,lm, r1,r2,rm = self.find_2d_tool_coordinates_in_3d(cam_info, clean_joints)




#         if np.linalg.norm(mid_point-self.last_midpoint) <  self.pan_tilt_deadzone_radius:
#             mid_point = self.last_midpoint
#         self.logerror("Distance is " + np.linalg.norm(mid_point-self.last_midpoint).__str__(), debug=True)
#         mid_point = ecm_pose[0:3,3] - np.array([0,0,.01]).reshape(3,1)
        self.add_marker(to_homo_mat([mid_point, [0,0,0]]), '/marker_subscriber',color=[1,0,0], scale=[0.047/5,0.047/5,0.047/5])
        self.add_marker(to_homo_mat([key_hole,[0,0,0]]), '/keyhole_subscriber',[0,0,1])
        self.add_marker(ecm_pose, '/current_ecm_pose', [1,0,0], Marker.ARROW, scale=[.1,.005,.005])
        temp = clean_joints['ecm'].position
        b,_ = forward_kinematics(self.ecm_kin, [temp[0],temp[1],.14,temp[3]])
        
        # find the equation of the line that goes through the key_hole and the 
        # mid_point
        ab_vector = (mid_point-key_hole)
        ecm_current_direction = b-key_hole 
        self.add_marker(ecm_pose, '/midpoint_to_keyhole', [0,1,1], type=Marker.LINE_LIST, scale = [0.005, 0.005, 0.005], points=[b, key_hole])
        
        self.add_marker(to_homo_mat([ab_vector,[0,0,0]]), '/ab_vector',[0,1,0], type=Marker.ARROW)
        r = self.find_rotation_matrix_between_two_vectors(ecm_current_direction, ab_vector)
        
        # Distance from keyhole to midpoint
        m = math.sqrt(ab_vector[0]**2 + ab_vector[1]**2 + ab_vector[2]**2) # ab_vector's length
        if self.last_midpoint is None:
            self.last_midpoint = m
            self.distance_to_midpoint = m
            
        # insertion joint length
        
        if self.method_number == 1:
            l = math.sqrt( (ecm_pose[0,3]-key_hole[0])**2 + (ecm_pose[1,3]-key_hole[1])**2 + (ecm_pose[2,3]-key_hole[2])**2)
        elif self.method_number == 2:
            # use the distance_to_midpoint variable to keep the distance to midpoint the same instead of keeping
            # the distance to keyhole consistent
            
            # distance_to_midpoint shouldn't be greater than the distance of the keyhole to the midpoint
            if self.distance_to_midpoint > m:
                self.distance_to_midpoint = m
            if self.distance_to_midpoint is None:
                l = math.sqrt( (ecm_pose[0,3]-key_hole[0])**2 + (ecm_pose[1,3]-key_hole[1])**2 + (ecm_pose[2,3]-key_hole[2])**2)
            else:
                l = m - self.distance_to_midpoint
                
            if l < 0.0:
                l = 0.0
                
#             print('self.distance_to_midpoint = {}\n'.format(self.distance_to_midpoint))
        # Equation of the line that passes through the midpoint of the tools and the key hole
        x = lambda t: key_hole[0] + ab_vector[0] * t
        y = lambda t: key_hole[1] + ab_vector[1] * t
        z = lambda t: key_hole[2] + ab_vector[2] * t
        
        t = l/m
        
        new_ecm_position = np.array([x(t), y(t), z(t)])

        ecm_pose[0:3,0:3] =  r* ecm_pose[0:3,0:3]     #Row 0-3 and column 0-3 for a 3x3 rotation matrix
        ecm_pose[0:3,3] = new_ecm_position            #Entire fourth column (position vector)
        self.add_marker(ecm_pose, '/target_ecm_pose', [0,0,1], Marker.ARROW, scale=[.1,.005,.005])
        output_msg = clean_joints['ecm']
        
        p = None  # Initialize p to None before try block
        try:
            p = self.ecm_kin.inverse(ecm_pose, q_guess=output_msg.position, min_joints=None, max_joints=None, maxiter=10000,eps=.001)
            
        except Exception as e:
            self._node.get_logger().error('error')
        if p is not None:  
            p[3] = 0
            output_msg.position = p
        else:
            print("Autocamera Inverse Failure ")
        
#         self.last_midpoint = mid_point
        return output_msg
    
    def find_2d_tool_coordinates_in_3d(self, cam_info, clean_joints):
        if cam_info is not None:
            psm1_kin_to_wrist = KDLKinematics(self.psm1_robot, self.psm1_robot.links[0].name, self.psm1_robot.links[-5].name)
            T1W = psm1_kin_to_wrist.forward(clean_joints['psm1'].position)
            
            psm2_kin_to_wrist = KDLKinematics(self.psm2_robot, self.psm2_robot.links[0].name, self.psm2_robot.links[-5].name)
            T2W = psm2_kin_to_wrist.forward(clean_joints['psm2'].position)
            
            TEW = self.ecm_kin.forward(clean_joints['ecm'].position)
            TEW_inv = np.linalg.inv(TEW)
            T1W_inv = np.linalg.inv(T1W)
            T2W_inv = np.linalg.inv(T2W)
            
            mid_point = (T1W[0:4,3] + T2W[0:4,3])/2
            p1 = T1W[0:4,3]
            p2 = T2W[0:4,3]
            
            T2E = TEW_inv * T2W
    
    #         ig = image_geometry.PinholeCameraModel()
            ig = image_geometry.StereoCameraModel()
            
            ig.fromCameraInfo(cam_info['right'], cam_info['left'])
            
            # Format in fakecam.launch:  x y z  yaw pitch roll [fixed-axis rotations: x(roll),y(pitch),z(yaw)]
            # Format for PoseConv.to_homo_mat:  (x,y,z)  (roll, pitch, yaw) [fixed-axis rotations: x(roll),y(pitch),z(yaw)]
            r = PoseConv.to_homo_mat( [ (0.0, 0.0, 0.0), (0.0, 0.0, 1.57079632679) ])
            r_inv = np.linalg.inv(r);
            
#             r = np.linalg.inv(r)
            self.logerror( r.__str__())
            
#             rotate_vector = lambda x: (r * np.array([ [x[0]], [x[1]], [x[2]], [1] ]) )[0:3,3]
             
            l1, r1 = ig.project3dToPixel( ( r_inv * TEW_inv * T1W )[0:3,3]) # tool1 left and right pixel positions
            l2, r2 = ig.project3dToPixel( ( r_inv * TEW_inv * T2W )[0:3,3]) # tool2 left and right pixel positions
            lm, rm = ig.project3dToPixel( ( r_inv * TEW_inv * mid_point)[0:3,0]) # midpoint left and right pixel positions
    #         add_100 = lambda x : (x[0] *.5 + cam_info.width/2, x[1])
    #         l1 = add_100(l1)
    #         l2 = add_100(l2)
    #         lm = add_100(lm)
    
            self.zoom_level_positions = {'l1':l1, 'r1':r1, 'l2':l2, 'r2':r2, 'lm':lm, 'rm':rm}    

            test1_l, test1_r = ig.project3dToPixel( [1,0,0])
            test2_l, test2_r = ig.project3dToPixel( [0,0,1])
            self.logerror('\ntest1_l = ' + test1_l.__str__() + '\ntest2_l = ' + test2_l.__str__() )
            mp = ( int(l1[0]+l2[0])/2, int(l1[1] + l2[1])/2)
            
        return l1,l2,lm, r1,r2,rm   
    
    def zoom_fitness(self, cam_info, mid_point, inner_margin, deadzone_margin, tool_point):
        x = cam_info.width; y = cam_info.height
    #     mid_point = [x/2, y/2]
        
        # if tool in inner zone
        if abs(tool_point[0]-mid_point[0]) <= inner_margin * x/2 and abs(tool_point[1] - mid_point[1]) < inner_margin * y/2:
            r = inner_margin  - max([abs(tool_point[0]-mid_point[0])/(x/2),abs(tool_point[1] - mid_point[1])/(y/2)])
            return r
        # if tool in deadzone
        elif abs(tool_point[0]-mid_point[0]) <= deadzone_margin * x/2 and abs(tool_point[1] - mid_point[1]) < deadzone_margin * y/2:
            return 0
        #if tool in outer zone
        elif abs(tool_point[0]-mid_point[0]) <= x/2 and abs(tool_point[1] - mid_point[1]) <  y/2:
            return -min( [ abs(min([abs(tool_point[0] - x), tool_point[0]])/(x/2) - deadzone_margin),  abs(min([abs(tool_point[1] - y), tool_point[1]])/(y/2) - deadzone_margin)])
        else:
            return -.1
        
    # radius is a percentage of the width of the screen
    def zoom_fitness2(self, cam_info, mid_point, tool_point, tool_point2, radius, deadzone_radius):
        r = radius * cam_info.width # r is in pixels
        dr = deadzone_radius * cam_info.width # dr is in pixels
        
        tool_in_view = lambda tool, safespace : \
        tool[0] > safespace or tool[1] > safespace or tool_point[0] < (cam_info.width-safespace) or \
        tool[1] < (cam_info.height-safespace)
        dist = lambda a,b : norm( [i-j for i,j in zip(a,b)] )
    
        self.logerror(dist(tool_point, tool_point2))
        now = time.time()
        zoom_time_threshold = .1 # was .3
        
        tools_are_stationary = False
        
        if self.tool_timer['psm1_stationary_duration'] > zoom_time_threshold and self.tool_timer['psm2_stationary_duration'] > zoom_time_threshold:
            # print(self.tool_timer['psm1_stationary_duration'])
            tools_are_stationary = True     
        
        # Inner zone
        if dist(tool_point, mid_point) < abs(r): # the tool's distance from the mid_point < r
            print("inner zone")
            print(tools_are_stationary)
            d =  abs(r) - dist(tool_point, mid_point)
            # return positive value
            if self.zones_times['inner_zone'] > 0:
                print("first if")
                if (now - self.zones_times['inner_zone'] > zoom_time_threshold) and tools_are_stationary:
                    print(now - self.zones_times['inner_zone'])
                    return 0.001 # * d/abs(r) # in meters
            else:
                self.zones_times['inner_zone'] = time.time()
                self.zones_times['outer_zone'] = 0
        # Outer zone 
        elif dist(tool_point, mid_point) > abs(r + dr): #  the tool's distance from the mid_point < r
            d = dist(tool_point, mid_point) - abs(r + dr)
            # return a negative value
            if self.zones_times['outer_zone'] > 0:
                if (now - self.zones_times['outer_zone']) > zoom_time_threshold and tools_are_stationary:
                    return -0.001 # * d/abs(dr) # in meters
            else:
                self.zones_times['outer_zone'] = time.time()
                self.midpoint_time = time.time()
                self.zones_times['inner_zone'] = 0
                
#         elif not tool_in_view(tool_point, 20) or not tool_in_view(tool_point2, 20):
#             return -0.001
        else: # Dead zone
            self.zones_times['outer_zone'] = 0
            self.zones_times['inner_zone'] = 0
            return 0
        return 0
    
    
    def unrectify_point(self, point, camera):
        left_ray = camera.left.projectPixelTo3dRay(point)
        
        t_vec = [0,0,0]
        cv2.Rodrigues( camera.left.R)
    
    
    def get_2d_point_from_3d_point_relative_to_world_rf(self, cam_info, TEW_inv, point):
        b = np.matrix( [ [-1, 0, 0], [0,1,0], [0,0,-1]])
    #     point[0:3]  = b * point[0:3]
        
        
        P = np.array(cam_info.P).reshape(3,4)
        m = TEW_inv * point
        u,v,w = P * m
        x = u/w
        y = v/w  
        Width = 640; Height = 480
        x = x * .5 + .5 * Width;
        y = y *.5 + .5 * Height
        return ( x,y )
                 
    def find_zoom_level(self, msg, cam_info, clean_joints):
        if cam_info is not None:
            psm1_kin_to_wrist = KDLKinematics(self.psm1_robot, self.psm1_robot.links[0].name, self.psm1_robot.links[-1].name)
            T1W = psm1_kin_to_wrist.forward(clean_joints['psm1'].position)
            
            psm2_kin_to_wrist = KDLKinematics(self.psm2_robot, self.psm2_robot.links[0].name, self.psm2_robot.links[-1].name)
            T2W = psm2_kin_to_wrist.forward(clean_joints['psm2'].position)
            
            TEW = self.ecm_kin.forward(clean_joints['ecm'].position)
            TEW_inv = np.linalg.inv(TEW)
            T1W_inv = np.linalg.inv(T1W)
            T2W_inv = np.linalg.inv(T2W)
            
            mid_point = (T1W[0:4,3] + T2W[0:4,3])/2
            p1 = T1W[0:4,3]
            p2 = T2W[0:4,3]
            
            T2E = TEW_inv * T2W
    
    #         ig = image_geometry.PinholeCameraModel()
            ig = image_geometry.StereoCameraModel()
            
            ig.fromCameraInfo(cam_info['right'], cam_info['left'])
            
            # Format in fakecam.launch:  x y z  yaw pitch roll [fixed-axis rotations: x(roll),y(pitch),z(yaw)]
            # Format for PoseConv.to_homo_mat:  (x,y,z)  (roll, pitch, yaw) [fixed-axis rotations: x(roll),y(pitch),z(yaw)]
            r = PoseConv.to_homo_mat( [ (0.0, 0.0, 0.0), (0.0, 0.0, 1.57079632679) ])
            r_inv = np.linalg.inv(r);
            
#             r = np.linalg.inv(r)
            self.logerror( r.__str__())
            
#             rotate_vector = lambda x: (r * np.array([ [x[0]], [x[1]], [x[2]], [1] ]) )[0:3,3]
             
            self.add_marker(T2W, '/left_arm', scale=[.002,.002,.002])
            
            
            l1, r1 = ig.project3dToPixel( ( r_inv * TEW_inv * T1W )[0:3,3]) # tool1 left and right pixel positions
            l2, r2 = ig.project3dToPixel( ( r_inv * TEW_inv * T2W )[0:3,3]) # tool2 left and right pixel positions
            lm, rm = ig.project3dToPixel( ( r_inv * TEW_inv * mid_point)[0:3,0]) # midpoint left and right pixel positions
    #         add_100 = lambda x : (x[0] *.5 + cam_info.width/2, x[1])
    #         l1 = add_100(l1)
    #         l2 = add_100(l2)
    #         lm = add_100(lm)

            self.zoom_level_positions = {'l1':l1, 'r1':r1, 'l2':l2, 'r2':r2, 'lm':lm, 'rm':rm}    

            test1_l, test1_r = ig.project3dToPixel( [1,0,0])
            test2_l, test2_r = ig.project3dToPixel( [0,0,1])
            self.logerror('\ntest1_l = ' + test1_l.__str__() + '\ntest2_l = ' + test2_l.__str__() )
    #         logerror('xm=%f,'%lm[0] +  'ym=%f'%lm[1])
            
            msg.position[3] = 0
#             zoom_percentage = self.zoom_fitness(cam_info=cam_info['left'], mid_point=lm, inner_margin=.20,
#                                             deadzone_margin_3d= .70, tool_point= l1)
             
            mp = ( int(l1[0]+l2[0])/2, int(l1[1] + l2[1])/2)
            zoom_percentage = self.zoom_fitness2(cam_info['left'], mid_point=mp, tool_point=l1, 
                                            tool_point2=l2, radius=self.zoom_innerzone_radius, deadzone_radius=self.zoom_deadzone_radius)
            self.zoom_percentage = zoom_percentage
#             print("zoom_percentage = {} ".format(zoom_percentage))
            
#             # Temporary
#             if self.method_number == 2: 
#                 zoom_percentage = 0
        
            msg.position[2] =  msg.position[2] + zoom_percentage 
            if msg.position[2] < 0 : # minimum 0
                msg.position[2] = 0.00
            elif msg.position[2] > .15: # maximum .23
                msg.position[2] = .15
                
            self.distance_to_midpoint -= zoom_percentage
            
            # Set the minimum and maximum value for distance_to_midpoint
            if self.distance_to_midpoint < .05:
                self.distance_to_midpoint = .05
            elif self.distance_to_midpoint > .20:
                self.distance_to_midpoint = .20
        return msg   
    
    def project_to_3d(self, x_lim, y_lim, z, cam_info):
        """!
            Returns x,y,z values for a point on the field of view based on the depth
            
            @param x_lim : a value between -1 and 1 that determines the horizontal place on the screen
            @param y_lim : a value between -1 and 1 that determines the vertical place on the screen 
            @param z : the depth, the distance from the camera end-effector
            @param cam_info : the stereo camera parameters
            
            @return x,y,z
        """
        x_lim *= (1-self.deadzone_margin_3d)
        y_lim *= (1-self.deadzone_margin_3d)
        
        cam = cam_info['left']
        fx = float(cam.k[0])
        fy = float(cam.k[4])
        cx = float(cam.k[2])
        cy = float(cam.k[5])
        
        # Validate camera parameters to avoid division by zero
        if fx == 0 or fy == 0 or np.isnan(fx) or np.isnan(fy):
            self._node.get_logger().warn("Invalid camera intrinsics: fx or fy is zero or NaN")
            return x_lim, y_lim, z
        
        fov_x = 2 * np.arctan(cy/fy)
        fov_y = 2 * np.arctan(cx/fx)
        
        x = cx * z * x_lim / fx
        y = cy * z * y_lim / fy
        
        return float(x), float(y), float(z)
    
    def find_tool_relation_to_3d_deadzone(self, cam_info, tool_position):
        """!
            Returns whether the tool is inside or outside the deadzone, and a vector 
            that shows the distance between the tool and the deadzone
            
            @param cam_info : The stereo camera parameter object
            @tool_position : The 3d coordinates of the tool
            
            @return "inside" or "outside"
            @return v : A vector showing the distance between the deadzone and the tool
        """
        
        p = lambda n : self.project_to_3d(self.deadzone_3d[n]['x'], self.deadzone_3d[n]['y'], tool_position[2], cam_info)

        bottom_left = p(0)
        top_left = p(1)
        top_right = p(2)
        bottom_right = p(3)
        
        # A helper function to make things easier
        f = lambda p1, p2: self.find_distance_between_point_and_line(tool_position, p1,p2)
        
        distances = {'left':f( bottom_left, top_left), 'top': f(top_left, top_right), 'right': f(top_right, bottom_right), 'bottom': f(bottom_right, bottom_left)}
        
        #print("distances = {}\n".format( distances))
        
        return distances
            

    def find_angle_between_3_points(self, corner, point1, point2):
        dist = lambda a,b : norm( [float(i)-float(j) for i,j in zip(a,b)] )
        a = dist(corner, point1)
        b = dist(corner, point2)
        c = dist(point1, point2) 
        return np.arccos( (a**2 + b**2 - c**2)/( 2 *a*b))
                
    def find_distance_between_point_and_line(self, point, line_point1, line_point2):
        dist = lambda a,b : norm( [float(i)-float(j) for i,j in zip(a,b)] )
        
        angle = self.find_angle_between_3_points(line_point2, point, line_point1)
        
        return np.sin(angle) * dist( point, line_point1 ) 
                    
    def track_tool_times(self, joints):
        tool_movement_threshold = 0.001
        if self.zoom_percentage != 0:
            tool_movement_threshold = 0.005
            
        if self.tool_timer['last_psm1_pos'] is None:
            self.tool_timer['last_psm1_pos'] = joints['psm1'].position
            self.tool_timer['psm1_stay_start_time'] = time.time()
        else:
            # If the tool has moved
            if not (np.linalg.norm( np.array(self.tool_timer['last_psm1_pos'])- np.array(joints['psm1'].position)) <tool_movement_threshold):
                self.tool_timer['psm1_stay_start_time'] = time.time()
                self.tool_timer['psm1_stationary_duration'] = 0
            else: # If the tool hasn't moved
                self.tool_timer['psm1_stationary_duration'] = time.time() - self.tool_timer['psm1_stay_start_time']
            self.tool_timer['last_psm1_pos'] = joints['psm1'].position
                
        if self.tool_timer['last_psm2_pos'] is None:
            self.tool_timer['last_psm2_pos'] = joints['psm2'].position
            self.tool_timer['psm2_stay_start_time'] = time.time()
        else:
            # If the tool has moved
            if not (np.linalg.norm(np.array(self.tool_timer['last_psm2_pos'])- np.array(joints['psm2'].position)) <tool_movement_threshold):
                self.tool_timer['psm2_stay_start_time'] = time.time()
                self.tool_timer['psm2_stationary_duration'] = 0
            else: # If the tool hasn't moved
                self.tool_timer['psm2_stationary_duration'] = time.time() - self.tool_timer['psm2_stay_start_time']
            self.tool_timer['last_psm2_pos'] = joints['psm2'].position
    
    def compute_viewangle(self, joint, cam_info, pos_track):
        kinematics = lambda name: self.psm1_kin if name == 'psm1' else self.psm2_kin if name == 'psm2' else self.ecm_kin 
        clean_joints = {}
        # TODO fix error when running control node
        try:
            joint_names = joint.keys()
            for j in joint_names:
                clean_joints[j] = self.extract_positions(joint[j], j, kinematics(j))
        
            key_hole, _ = forward_kinematics(self.ecm_kin, [0, 0, 0, 0]) # The position of the keyhole, is the end-effector's
            psm1_pos,_ =   forward_kinematics(self.psm1_kin, clean_joints['psm1'].position)
            psm2_pos,_ = forward_kinematics(self.psm2_kin, clean_joints['psm2'].position)
            # psm1_pose = self.psm1_kin.forward(clean_joints['psm1'].position)
            ecm_pos, ecm_rot = forward_kinematics(self.ecm_kin, clean_joints['ecm'].position)
            ecm_pose = pos_rot_to_homo_mat(ecm_pos, ecm_rot)


            #Reenu added below lines for dvrk_safety(psm_safety)

            psm1_pos_trans = Point()
            psm1_pos_trans.x = psm1_pos[0]
            psm1_pos_trans.y = psm1_pos[1]
            psm1_pos_trans.z = psm1_pos[2]

            psm2_pos_trans = Point()
            psm2_pos_trans.x = psm2_pos[0]
            psm2_pos_trans.y = psm2_pos[1]
            psm2_pos_trans.z = psm2_pos[2]

            self.psm1_pos_transformed.publish(psm1_pos_trans)
            self.psm2_pos_transformed.publish(psm2_pos_trans)


        except Exception as e:
            self._node.get_logger().error(str(e))
            output_msg = joint['ecm']
    #         output_msg.name = ['outer_yaw', 'outer_pitch', 'insertion', 'outer_roll']
    #         output_msg.position = [joint['ecm'].position[x] for x in [0,1,5,6]]
            return output_msg
        
        #print("tool 1 : \n")
        self.find_tool_relation_to_3d_deadzone(cam_info, psm1_pos)
        
        #print("tool 2 : \n")
        #self.find_tool_relation_to_3d_deadzone(cam_info, psm2_pos)
        
        output_msg = clean_joints['ecm']
        
        gripper= max( [ abs(joint['psm1'].position[-1]), abs(joint['psm2'].position[-1])] ) < math.pi/8
    #     rospy.logerr('psm1 gripper = ' + joint['psm1'].position[-1].__str__() + 'gripper = ' + gripper.__str__())
        
        # Track when the tools are stationary
        self.track_tool_times(clean_joints)
        if gripper == gripper or gripper != gripper: # luke was here
            output_msg = self.point_towards_midpoint(clean_joints, psm1_pos, psm2_pos, key_hole, ecm_pose, cam_info, pos_track)
#             output_msg.position =list( np.array(output_msg.position) + ( -np.array(output_msg.position)+ np.array(goal_joints.position)) *.0001)
            output_msg = self.find_zoom_level(output_msg, cam_info, clean_joints)
            pass
        
        if len(output_msg.name) > 4:
            output_msg.name = ['outer_yaw', 'outer_pitch', 'insertion', 'outer_roll']
        if len(output_msg.position) >= 7:
            output_msg.position = [output_msg.position[x] for x in [0,1,5,6]]
            
            
        self.logerror(output_msg.__str__())
        return output_msg
    
    
