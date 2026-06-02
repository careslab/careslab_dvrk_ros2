#!/usr/bin/env python3

import cv2
import numpy as np
import rospy
from std_msgs.msg import Float64

class BlinkDetector:
    def __init__(self, video_source):
        rospy.init_node('blink_publisher', anonymous=True)
        self.blink_publisher = rospy.Publisher('/safety/blink_rate', Float64, queue_size=10)
        self.cap = cv2.VideoCapture(video_source)
        self.cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('M', 'J', 'P', 'G')) 
        self.scale = 0.5
        self.font = cv2.FONT_HERSHEY_SIMPLEX
        self.org = (50, 50)
        self.fontScale = 1
        self.font_color = (0, 0, 0)
        self.thickness = 2  
        self.tracker = cv2.TrackerCSRT.create()
        self.backup = cv2.TrackerCSRT.create()
        ret, frame = self.cap.read()
        frame = self.rescale(frame, self.scale)
        box = cv2.selectROI(frame, False)
        self.tracker.init(frame, box)
        self.backup.init(frame, box)
        cv2.destroyAllWindows()
        self.width = 75
        self.height = 60
        self.blinks = 0
        self.blink_thresh = 100 # previously 80
        self.blink_trigger = True

    def tup(self, p):
        return (int(p[0]), int(p[1]))

    def get_center(self, box):
        x, y = box[:2]
        x += box[2] / 2.0
        y += box[3] / 2.0
        return [x, y]

    def rescale(self, img, scale):
        h, w = img.shape[:2]
        return cv2.resize(img, (int(w * scale), int(h * scale)))

    def process_frame(self, frame):
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        _, s, _ = cv2.split(hsv)
        return s

    def draw_rectangles(self, frame, box, center):
        tl = [center[0] - self.width, center[1] - self.height]
        br = [center[0] + self.width, center[1] + self.height]
        tl = self.tup(tl)
        br = self.tup(br)
        p1 = self.tup([box[0], box[1]])
        p2 = self.tup([box[0] + box[2], box[1] + box[3]])
        cv2.rectangle(frame, p1, p2, (255, 0, 0), 3)
        cv2.rectangle(frame, tl, br, (0, 255, 0), 3)
        cv2.circle(frame, self.tup(center), 6, (0, 0, 255), -1)

    def run(self):
        while not rospy.is_shutdown():
            ret, frame = self.cap.read()
            if not ret:
                break
            frame = self.rescale(frame, self.scale)
            channel = self.process_frame(frame)
            ret, box = self.tracker.update(frame)
            if ret:
                center = self.get_center(box)
                self.draw_rectangles(frame, box, center)
                tl = self.tup([center[0] - self.width, center[1] - self.height])
                br = self.tup([center[0] + self.width, center[1] + self.height])
                ave = np.mean(channel[tl[1]:br[1], tl[0]:br[0]])
                print(ave)
                if ave < self.blink_thresh and self.blink_trigger:
                    self.blinks += 1
                    self.blink_trigger = False
                    self.blink_publisher.publish(Float64(self.blinks))
                    rospy.loginfo("Published: + str{self.blinks}")
                if ave >= self.blink_thresh:
                    self.blink_trigger = True
                frame = cv2.putText(frame, "Blinks:" + str(self.blinks), self.org, self.font, self.fontScale, 
                                    self.font_color, self.thickness, cv2.LINE_AA)
            cv2.imshow("Frame", frame)
            if cv2.waitKey(1) == ord('q'):
                break
        rospy.spin()

if __name__ == "__main__":
    #video_source = 2
    video_source = "/home/cares/catkin_ws/src/careslab_dvrk_safety/Blink_10secs.mp4"
    blink_detector = BlinkDetector(video_source)
    blink_detector.run()
