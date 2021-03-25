#import
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
from nti_arrow_3 import detect_arr
from sensor_msgs.msg import Range
from clover.srv import SetLEDEffect
import time

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
set_effect = rospy.ServiceProxy('led/set_effect', SetLEDEffect)


telemetry = get_telemetry(frame_id='aruco_map')
bridge = CvBridge()
qr = ''
qr_debug = rospy.Publisher("Detect", Image, queue_size=1)
alt = ''
f = open('Report.txt', 'w')
#helpers
def fly(x=0, y=0, z=1.2, speed=0.5, frame_id='aruco_map', auto_arm=False, tolerance=0.2):
    #print(x, y)
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
    cv_image = bridge.imgmsg_to_cv2(data, 'bgr8')#get image
    #qr_debug.publish(bridge.cv2_to_imgmsg(cv_image, 'bgr8'))
    barcodes = pyzbar.decode(cv_image)#decode
    for barcode in barcodes:
        b_data = barcode.data.encode("utf-8")#get data
        qr = b_data.split()
        (x, y, w, h) = barcodes[0].rect
        cv2.rectangle(cv_image, (x, y), (x + w, y + h), (180, 105, 255), 3)#draw bounds
        qr_debug.publish(bridge.cv2_to_imgmsg(cv_image, 'bgr8'))
    f.write(str(telemetry)) #this is telemetry

#unused      
def range_callback(msg):        
    global alt
    alt = msg.range
    
    if alt < 1:   
        land()
        rospy.sleep(2)
        takeoff()
        rospy.sleep(5)
#.
        
        



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
    #detect arrow. retry if failed
    while(ret == 'n'  and  cnt_a < 100):
        img = bridge.imgmsg_to_cv2(rospy.wait_for_message('main_camera/image_raw', Image), 'bgr8')
        ret = detect_arr(img)
        cnt_a+= 1
        
except:
    print("oops")
    ret = 'x'
#publish to topic
qr_debug.publish(bridge.cv2_to_imgmsg(img,'bgr8'))
#go to needed sector
fly(X, Y, 1.3)
fly(X, Y, 0.6)
rospy.sleep(1)
fly(X, Y, 1.2)
rospy.sleep(2)
#detect arrow direction and color
img = bridge.imgmsg_to_cv2(rospy.wait_for_message('main_camera/image_raw', Image), 'bgr8')
try:
    ret = 'n'
    col = 'n'
    cnt_a = 0
    while(ret == 'n'  and  cnt_a < 100):#detect arrow. retry if failed up to 100 times
        img = bridge.imgmsg_to_cv2(rospy.wait_for_message('main_camera/image_raw', Image), 'bgr8')
        ret,col = detect_arr(img)
        cnt_a+= 1
        
except:
    #error handling
    print("oops")
    ret = 'x'
    col = 'x'
#print(col)
tumbsize = 0.2
fly_h = 1.2
#light LED
if(col == 'r'):
    set_effect(r=255, g=0, b=0)
    print("Red")
elif(col == 'y'):
    set_effect(r=255, g=255, b=0)
    print("Yellow")
elif(col == 'b'):
    set_effect(r=0, g=0, b=255)
    print("Blue")
elif(col == 'k'):
    set_effect(r=255, g=255, b=255)
    print("Black")

rospy.sleep(5)
fly(X, Y, fly_h)
set_effect(r=0, g=0, b=0)
qr_debug.publish(bridge.cv2_to_imgmsg(img,'bgr8'))
#print sector and fly to it
if   ret == 'r':
    print("Sector B reqired")
    navigate(x=0, y=-2, z=0, speed = 0.2, frame_id='body')
elif ret == 'l':
    print("Sector A reqired")
    navigate(x=0, y=2, z=0,speed = 0.2,frame_id='body')
elif ret == 'd':
    print("Sector D reqired")
    navigate(x=-3, y=0, z=0,speed = 0.2,frame_id='body')
elif ret == 'u':
    print("Sector C reqired")
    navigate(x=2, y=0, z=0,speed = 0.2, frame_id='body')
else:
    print("None")
#wait to reach destination (detect by rangefinder) and a bit more, not to fall off,then land
while(fly_h - rospy.wait_for_message('rangefinder/range', Range).range < tumbsize):
    pass
rospy.sleep(1)
land()
#output message
s = ""
s += str(int(n)) + " delivered in sector "
if   ret == 'r':
    s += "B"
elif ret == 'l':
    s += "A"
elif ret == 'd':
    s += "D"
elif ret == 'u':
    s += "C"

rospy.sleep(15)
print(s)
#go back. avoidance like first
takeoff()

m = bfs([0,0],obs)
pos = get_telemetry(frame_id='aruco_map')
xc = min(max(0,int(pos.x * factor)), 39)
yc = min(max(0,int(pos.y * factor)), 29)
while(m[xc][yc][0] >= 0):
    xc,yc = m[xc][yc][0],m[xc][yc][1]
    fly(xc/factor,yc/factor)
if(m[xc][yc][0] == -1):
    print("oops")

#land and print message
fly(0, 0)
land()
start_time = time.time() - start_time
s = str(n) + " delivered in sector "
if   ret == 'r':
    s += "B"
elif ret == 'l':
    s += "A"
elif ret == 'd':
    s += "D"
elif ret == 'u':
    s += "C"

#print(str(start_time))
print(s + " for " + str(start_time // 60) + " mins," + str(start_time % 60) + "secs")
print("Stop recording report")
f.close()


