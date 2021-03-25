# -*- coding: utf-8 -*-
import cv2
import numpy as np
"""
Created on Tue Mar 23 08:20:40 2021

@author: Danila
"""

def detect_arr(img):
    imgHSV = cv2.cvtColor(img,cv2.COLOR_BGR2HSV) #convert to hsv
    mask = cv2.inRange(imgHSV,(0,0,0),(255,255,50)) #find black
    #cv2.imshow("mask",mask)
    cnts = cv2.findContours(mask,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE) #find contours
    cnts = cnts[1] 
    best_id = -1 
    best_val = 0
    for x in range(len(cnts)):
        xc,yc,w,h = cv2.boundingRect(cnts[x])
       
        if(w == 0 or h == 0):
            continue
        mind = min(w,h)
        maxd = max(w,h)
        #print(mind > 3 , maxd/mind > 1.7, maxd/mind, cv2.contourArea(cnts[x]) / (w*h))
        #find objects , looking like arrows in shape (sides of bounding rectangles)
        if(mind > 3 and maxd/mind > 1.3 and maxd/mind < 3 and cv2.contourArea(cnts[x]) / (w*h) > 0.1):
            img = cv2.rectangle(img,(xc,yc),(xc + w,yc + h),(0,255,255),2)
            if(cv2.contourArea(cnts[x]) > best_val): #find the largest
                print(mind,maxd/mind,cv2.contourArea(cnts[x]) / (w*h))
                best_val = cv2.contourArea(cnts[x])
                best_id = x
    
    if(best_id == -1):
        return "n"
    xc,yc,w,h = cv2.boundingRect(cnts[best_id])
    img = cv2.rectangle(img,(xc,yc),(xc + w,yc + h),(0,255,0),2) #draw a bounding rectangle
    #mask_t = mask[yc:yc+h,xc:xc + w]
    #cut off the sides
    if(w < h):
        mask_t = mask[yc:yc+h,int(xc+(w*0.25)):int(xc+(w*0.75))]
    else:
        mask_t = mask[int(yc+(h*0.25)):int(yc+(h*0.75)),xc:xc + w]
    
    nz = np.nonzero(mask_t)
    dir_y = -int((np.mean(nz[0]) - (len(mask_t)/2))*10)
    dir_x = -int((np.mean(nz[1]) - (len(mask_t[0])/2))*10)
    print(dir_x,dir_y)
    #estimate direction using empty space in front
    cv2.line(img,(xc,yc),(xc + dir_x,yc + dir_y),(255,0,0),5)
    #cv2.imshow("obj",mask_t)
    #cv2.imshow("img",img)
    if(abs(dir_x) > abs(dir_y)):
        if(dir_x > 0):
            print()
            return "r"
        else:
            return "l"
    else:
        if(dir_y > 0):
            return "d"
        else:
            return "u"

