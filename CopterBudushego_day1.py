
import rospy
import math
import numpy as np
import cv2

from cv_bridge import CvBridge
from clover import srv
from std_srvs.srv import Trigger
from sensor_msgs.msg import Image

from nti_arrow import detect_arr
from helpers import *

rospy.init_node('flight')
image_pub = rospy.Publisher('Detect', Image,queue_size = 2)
get_telemetry = rospy.ServiceProxy('get_telemetry', srv.GetTelemetry)
navigate = rospy.ServiceProxy('navigate', srv.Navigate)
navigate_global = rospy.ServiceProxy('navigate_global', srv.NavigateGlobal)
set_position = rospy.ServiceProxy('set_position', srv.SetPosition)
set_velocity = rospy.ServiceProxy('set_velocity', srv.SetVelocity)
set_attitude = rospy.ServiceProxy('set_attitude', srv.SetAttitude)
set_rates = rospy.ServiceProxy('set_rates', srv.SetRates)
land = rospy.ServiceProxy('land', Trigger)
bridge = CvBridge()

size = 0.5

takeoff(size)
fly(1.2, 1.2)
img = bridge.imgmsg_to_cv2(rospy.wait_for_message('main_camera/image_raw', Image), 'bgr8')
try:
    ret = detect_arr(img)
except:
    print("oops")
    ret = 'x'
image_pub.publish(bridge.cv2_to_imgmsg(img,'bgr8'))
if   ret == 'r':
    print("Sector C reqired")
elif ret == 'l':
    print("Sector D reqired")
elif ret == 'd':
    print("Sector B reqired")
elif ret == 'u':
    print("Sector A reqired")
else:
    print("None")
fly()
land()
#cv2.waitKey(10000)
#cv2.destroyAllWindows()

