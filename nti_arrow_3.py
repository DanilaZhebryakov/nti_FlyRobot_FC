# -*- coding: utf-8 -*-
import cv2
import numpy as np
"""
Created on Tue Mar 23 08:20:40 2021

@author: Danila
"""

def detect_arr(img):
    #get mask for arrow of any of neded colors
    imgHSV = cv2.cvtColor(img,cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(imgHSV,(0,0,0),(255,255,50))#black
    mask = cv2.bitwise_or(mask,cv2.inRange(imgHSV,(10,70,20),(60,255,255)))#yellow
    mask = cv2.bitwise_or(mask,cv2.inRange(imgHSV,(80,60,30),(150,255,210)))#blue
    mask = cv2.bitwise_or(mask,cv2.inRange(imgHSV,(0,70,20),(20,255,255)))#red
    mask = cv2.bitwise_or(mask,cv2.inRange(imgHSV,(160,70,20),(190,255,255)))#another red (due to HSV)
    
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
    img = cv2.rectangle(img,(xc,yc),(xc + w,yc + h),(180,105,255),2) #draw bounding rectangle
    #mask_t = mask[yc:yc+h,xc:xc + w]
    
    if(w < h):#ct off the edges
        mask_t = mask[yc:yc+h,int(xc+(w*0.25)):int(xc+(w*0.75))]
    else:
        mask_t = mask[int(yc+(h*0.25)):int(yc+(h*0.75)),xc:xc + w]
    nz = np.nonzero(mask_t)
    
    dir_y = -int((np.mean(nz[0]) - (len(mask_t)/2))*10)#detect direction
    dir_x = -int((np.mean(nz[1]) - (len(mask_t[0])/2))*10)
    
    print(dir_x,dir_y)
    cv2.line(img,(xc,yc),(xc + dir_x,yc + dir_y),(255,0,0),5)
    #cv2.imshow("obj",mask_t)
    
    #get HSV image of arrow and count colors in it
    img_t = imgHSV[yc:yc+h,xc:xc + w]
    cnt_r = np.count_nonzero(cv2.bitwise_or(cv2.inRange(img_t,(0,70,20),(20,255,255)),cv2.inRange(img_t,(160,70,20),(190,255,255))))
    cnt_b = np.count_nonzero(cv2.inRange(img_t,(80,60,30),(150,255,210)))
    cnt_y = np.count_nonzero(cv2.inRange(img_t,(10,70,20),(60,255,255)))
    cnt_k = np.count_nonzero(cv2.inRange(img_t,(0,0,0),(255,255,50)))
    cnt_m = max(cnt_r,cnt_b,cnt_y,cnt_k)
    col = 'n'
    
    #find maximum color
    if(cnt_b == cnt_m):
        col = 'b'
    elif(cnt_r == cnt_m):
        col = 'r'
    elif(cnt_y == cnt_m):
        col = 'y'
    elif(cnt_k == cnt_m):
        col = 'k'
    #cv2.imshow("img",img)
    
    #return direction and color
    if(abs(dir_x) > abs(dir_y)):
        if(dir_x > 0):
            return "r",col
        else:
            return "l",col
    else:
        if(dir_y > 0):
            return "d",col
        else:
            return "u",col
"""
img = cv2.imread("image.jpeg")
print(detect_arr(img))
cv2.waitKey(10000)
cv2.destroyAllWindows()
"""
