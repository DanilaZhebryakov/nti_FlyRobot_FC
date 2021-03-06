#imports
import rospy
import math
import cv2
from cv_bridge import CvBridge
from clover import srv
from std_srvs.srv import Trigger
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
from pyzbar import pyzbar
from graph import bfs
from nti_arrow_1 import detect_arr
from sensor_msgs.msg import Range
rospy.init_node('flightqr')

#service proxy
get_telemetry = rospy.ServiceProxy('get_telemetry', srv.GetTelemetry)
navigate = rospy.ServiceProxy('navigate', srv.Navigate)
navigate_global = rospy.ServiceProxy('navigate_global', srv.NavigateGlobal)
set_position = rospy.ServiceProxy('set_position', srv.SetPosition)
set_velocity = rospy.ServiceProxy('set_velocity', srv.SetVelocity)
set_attitude = rospy.ServiceProxy('set_attitude', srv.SetAttitude)
set_rates = rospy.ServiceProxy('set_rates', srv.SetRates)
land = rospy.ServiceProxy('land', Trigger)

bridge = CvBridge()
qr = ''
qr_debug = rospy.Publisher("Detect", Image, queue_size=1)
alt = ''

#helpers
def fly(x=0, y=0, z=1.2, speed=0.5, frame_id='aruco_map', auto_arm=False, tolerance=0.2):
    navigate(x=x, y=y, z=z, speed=speed, frame_id=frame_id, auto_arm=auto_arm)

    while not rospy.is_shutdown():
        telem = get_telemetry(frame_id='navigate_target')
        if math.sqrt(telem.x ** 2 + telem.y ** 2 + telem.z ** 2) < tolerance:
            break
        rospy.sleep(0.2)


def takeoff():
    navigate(x=0, y=0, z=1.2, speed=0.2, frame_id='body', auto_arm=True)
    rospy.sleep(6)

#qr code detector
def image_callback(data):
    global qr
    cv_image = bridge.imgmsg_to_cv2(data, 'bgr8')
    #qr_debug.publish(bridge.cv2_to_imgmsg(cv_image, 'bgr8'))
    barcodes = pyzbar.decode(cv_image)
    for barcode in barcodes:
        b_data = barcode.data.encode("utf-8")
        qr = b_data.split()
        (x, y, w, h) = barcodes[0].rect
        cv2.rectangle(cv_image, (x, y), (x + w, y + h), (180, 105, 255), 3)
        qr_debug.publish(bridge.cv2_to_imgmsg(cv_image, 'bgr8'))
#unused
"""
def range_callback(msg):        
    global alt
    alt = msg.range
    
    if alt < 0.6:   
        land()
        rospy.sleep(2)
        takeoff()
        rospy.sleep(5)
"""
        
        



image_sub = rospy.Subscriber('main_camera/image_raw_throttled', Image, image_callback, queue_size=1)
#take off and fly to code
takeoff()
fly(0.4, 0.8, z=0.5)
#wait callback to detect and decode code
while qr == '':
    rospy.sleep(0.2)
collums_coordinats = qr[:-3]
#read the code data to variables
X = float(qr[-3])
Y = float(qr[-2])
n = float(qr[-1])
obs = []
factor = 10
#read column data
for i in range(0, len(collums_coordinats), 2):
    print("Column area x=" + str(collums_coordinats[i]) + ", y=" + str(collums_coordinats[i + 1]))
    obs.append([[float(collums_coordinats[i])*factor,float(collums_coordinats[i + 1])*factor],0.5*factor])
print("Navigate area x= " + str(X) + ", y=" + str(Y)) 
print("Order number: " + str(n))

#compute array for navigation and avoidance using  breadth-first search
m = bfs([int(X*factor),int(Y*factor)],obs)

#fly to arrow using found array
xc = 2
yc = 2
while(m[xc][yc][0] >= 0):
    xc,yc = m[xc][yc][0],m[xc][yc][1]
    fly(xc/factor,yc/factor)
if(m[xc][yc][0] == -1):
    print("oops")
fly(X, Y, 0.6)
fly(X, Y, 1.2)


img = bridge.imgmsg_to_cv2(rospy.wait_for_message('main_camera/image_raw', Image), 'bgr8')
try:
    ret = 'n'
    cnt_a = 0
    while(ret == 'n'  and  cnt_a < 100):#detect arrow. retry if failed up to 100 times
        img = bridge.imgmsg_to_cv2(rospy.wait_for_message('main_camera/image_raw', Image), 'bgr8')
        ret = detect_arr(img)
        cnt_a+= 1
        
except:
    print("oops")
    ret = 'x'
#publish to topic
qr_debug.publish(bridge.cv2_to_imgmsg(img,'bgr8'))
#print sector and fly to it
if   ret == 'r':
    print("Sector B reqired")
    navigate(x=0, y=-2, z=0, speed = 0.2, frame_id='body')
    print(str(n) + " delivered in sector B")
elif ret == 'l':
    print("Sector A reqired")
    navigate(x=0, y=2, z=0,speed = 0.2,frame_id='body')
    print(str(n) + " delivered in sector A")
elif ret == 'd':
    print("Sector D reqired")
    navigate(x=-3, y=0, z=0,speed = 0.2,frame_id='body')
    print(str(n) + " delivered in sector D")
elif ret == 'u':
    print("Sector C reqired")
    navigate(x=2, y=0, z=0,speed = 0.2, frame_id='body')
    print(str(n) + " delivered in sector C")
else:
    print("None")
#wait to reach destination (detect by rangefinder)
while(rospy.wait_for_message('rangefinder/range', Range).range > 0.6):
    pass

land()
rospy.sleep(5)
print('toff')
#go back
takeoff()
fly(0, 0)
land()
