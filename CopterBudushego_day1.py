#import
import rospy
import math
import numpy as np
import cv2

from cv_bridge import CvBridge
from clover import srv
from std_srvs.srv import Trigger
from sensor_msgs.msg import Image

#service proxy
rospy.init_node('flight')
image_pub = rospy.Publisher('Detect', Image)
get_telemetry = rospy.ServiceProxy('get_telemetry', srv.GetTelemetry)
navigate = rospy.ServiceProxy('navigate', srv.Navigate)
navigate_global = rospy.ServiceProxy('navigate_global', srv.NavigateGlobal)
set_position = rospy.ServiceProxy('set_position', srv.SetPosition)
set_velocity = rospy.ServiceProxy('set_velocity', srv.SetVelocity)
set_attitude = rospy.ServiceProxy('set_attitude', srv.SetAttitude)
set_rates = rospy.ServiceProxy('set_rates', srv.SetRates)
land = rospy.ServiceProxy('land', Trigger)

number = 3
size = 0.5
bridge = CvBridge()

#helpers
def fly(x=0, y=0, z=1, speed=0.2, frame_id='aruco_map', auto_arm=False,
        tolerance=0.2):
    navigate(x=x, y=y, z=z, speed=speed, frame_id=frame_id, auto_arm=auto_arm)

    while not rospy.is_shutdown():
        telem = get_telemetry(frame_id='navigate_target')
        if math.sqrt(telem.x ** 2 + telem.y ** 2 + telem.z ** 2) < tolerance:
            break
        rospy.sleep(0.2)


def takeoff():
    navigate(x=0, y=0, z=0.5 + size, speed=0.2, frame_id='body', auto_arm=True)
    rospy.sleep(6)

#arrow detection function
def detect_arr(img):
    #detect black by color (V < 50 in HSV)
    imgHSV = cv2.cvtColor(img,cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(imgHSV,(0,0,0),(255,255,50))
    #cv2.imshow("mask",mask)
    cnts = cv2.findContours(mask,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE) #find contours
    cnts = cnts[1] #WARNING version difference
    best_id = -1
    best_val = 0
    for x in range(len(cnts)):
        #find contours, looking like arrows (using shape of bounding rectangle and fitting it (to avoid detecting long lines))
        xc,yc,w,h = cv2.boundingRect(cnts[x])
        if(w == 0 or h == 0):
            continue
        mind = min(w,h)
        maxd = max(w,h)
        #print(mind > 3 , maxd/mind > 1.7, maxd/mind, cv2.contourArea(cnts[x]) / (w*h))
        if(mind > 3 and maxd/mind > 1.7 and maxd/mind < 3 and cv2.contourArea(cnts[x]) / (w*h) > 0.3):
            img = cv2.rectangle(img,(xc,yc),(xc + w,yc + h),(0,255,255),2) #debug: draw bounds of all contours
            if(cv2.contourArea(cnts[x]) > best_val):#find the largest detected
                best_val = cv2.contourArea(cnts[x])
                best_id = x
    xc,yc,w,h = cv2.boundingRect(cnts[best_id])
    if(best_id == -1):
        return "none"
    img = cv2.rectangle(img,(xc,yc),(xc + w,yc + h),(0,255,0),2) #draw rectangle
   #mask_t = mask[yc:yc+h,xc:xc + w]
    
    if(w < h):#cut off the sides of an arrow to get rid of empty spaces
        mask_t = mask[yc:yc+h,int(xc+(w*0.25)):int(xc+(w*0.75))]
    else:
        mask_t = mask[int(yc+(h*0.25)):int(yc+(h*0.75)),xc:xc + w]
    nz = np.nonzero(mask_t)
    dir_y = -int((np.mean(nz[0]) - (len(mask_t)/2))*10)
    dir_x = -int((np.mean(nz[1]) - (len(mask_t[0])/2))*10)#detect direction using white spaces in front
    
    print(dir_x,dir_y)
    cv2.line(img,(xc,yc),(xc + dir_x,yc + dir_y),(255,0,0),5)
    #cv2.imshow("obj",mask_t)
    #image_pub.publish(bridge.cv2_to_imgmsg(img, 'bgr8'))
    #cv2.imshow("img",img)
    if(abs(dir_x) > abs(dir_y)):
        if(dir_x > 0):
            print()
            return "Sector C reqired"
        else:
            return "Sector D reqired"
    else:
        if(dir_y > 0):
            return "Sector B reqired"
        else:
            return "Sector A reqired"
#main program
takeoff()
fly(1.2, 1.2)
print(detect_arr(bridge.imgmsg_to_cv2(rospy.wait_for_message('main_camera/image_raw', Image), 'bgr8')))
fly()
land()
#cv2.waitKey(10000)
#cv2.destroyAllWindows()

