#!/usr/bin/env python2

"""
Collect data as the robot drives around the object
"""

import cv2
import os
from cv_bridge import CvBridge

from drive_ngon import ShapeDriver

from PIL import Image as PImage
import matplotlib.pyplot as plt
import numpy as np
import pandas
import csv

import rospy
from sensor_msgs.msg import Image, LaserScan
from std_msgs.msg import String
from tf.transformations import euler_from_quaternion, rotation_matrix, quaternion_from_matrix
from geometry_msgs.msg import Pose, Twist, Vector3
from nav_msgs.msg import Odometry
from visualization_msgs.msg import Marker

from scar_core.point_dumper import PointDumper

class dataCollector:

    def __init__(self):

        #Robot properities
        self.linVector = Vector3(x=0.0, y=0.0, z=0.0)
        self.angVector = Vector3(x=0.0, y=0.0, z=0.0)

        self.x = 0
        self.y = 0
        self.theta = 0
        self.ranges = []
        self.img = []

        self.bridge = CvBridge()

        self.data_path = "/tmp/"
        
        #ROS
        self.pub = rospy.Publisher('/cmd_vel', Twist, queue_size=2)
        self.vizPub = rospy.Publisher('/visualization_marker', Marker, queue_size=10)
        rospy.init_node('data_collection')
        rospy.Subscriber("/scan", LaserScan, self.checkLaser)
        rospy.Subscriber("/odom", Odometry, self.setLocation)
        rospy.Subscriber('/camera/image_raw', Image, self.setImage)


    def publishVelocity(self, linX, angZ):
        """
        Publishes velocities to make the robot move

        linX is a floating point between 0 and 1 to control the robot's x linear velocity
        angZ is a floating point between 0 and 1 to control the robot's z angular velocity
        """
        if self.debugOn: print("publishing")

        self.linVector.x = linX
        self.angVector.z = angZ
        self.pub.publish(Twist(linear=self.linVector, angular=self.angVector))


    def checkLaser(self, scan):
    	"""
		Pulls laser scan data
    	"""
    	self.ranges = scan.ranges




    def setLocation(self, odom):
        """
        Convert pose (geometry_msgs.Pose) to a (x, y, theta) tuple
        Constantly being called as it is the callback function for this node's subscription

        odom is Neato ROS' nav_msgs/Odom msg composed of pose and orientation submessages
        """

        pose = odom.pose.pose
        orientation_tuple = (pose.orientation.x,
                                pose.orientation.y,
                                pose.orientation.z,
                                pose.orientation.w)
        angles = euler_from_quaternion(orientation_tuple)
        self.x = pose.position.x
        self.y = pose.position.y
        self.theta = angles[2]
        return (pose.position.x, pose.position.y, angles[2])


    def setImage(self, img):

        img = self.bridge.imgmsg_to_cv2(img, desired_encoding="bgr8")
        #img = PImage.open(img)
        img = cv2.resize(img, (160, 120), interpolation=cv2.INTER_AREA)
        self.img = img

        
    def run(self):
        pd = PointDumper(viz=True)
    	#driver = ShapeDriver(10,.25)
    	#driver.run()

        filename = os.path.join(self.data_path, 'data.csv')
    	f = open(filename, "w+")
    	f.write("x,y,theta,scan\n")
    	count = 0
    	while not rospy.is_shutdown():
    		if (not len(self.ranges)==0) and (not self.img.size==0):
                        # online visualization
                        pd.proc_frame(self.x, self.y, self.theta, self.ranges)
	    		line = str(self.x)+","+str(self.y)+","+str(self.theta)+","+str(self.ranges)[1:-1]+"\n"
	    		f.write(line)

	    		fileNum = self.data_path+"img" +str(count) +".png"
	    		cv2.imwrite(fileNum,self.img)
	    		count += 1

	    		self.ranges=[]


if __name__ == "__main__":
	dc = dataCollector()
	dc.run()
