import cv2
import numpy as np
def nothing(x):
    pass
#cap = cv2.VideoCapture(1)
cv2.namedWindow("controls")
cv2.createTrackbar("h", "controls",0,255,nothing)
cv2.createTrackbar("s", "controls",0,255,nothing)
cv2.createTrackbar("v", "controls",0,255,nothing)
cv2.createTrackbar("H", "controls",0,255,nothing)
cv2.createTrackbar("S", "controls",0,255,nothing)
cv2.createTrackbar("V", "controls",0,255,nothing)
while cv2.waitKey(1) != ord('q'):
    names = ["Clover.jpg"]
    for i in range(len(names)):
        img = cv2.resize(cv2.imread(names[i]), (64, 64))
        img2 = cv2.cvtColor(img,cv2.COLOR_BGR2HSV)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        img2 = np.stack([img2[:,:,0],clahe.apply(img2[:,:,1]),clahe.apply(img2[:,:,2])],axis = 2)

        mask = cv2.inRange(img2,np.array((cv2.getTrackbarPos('h','controls'),cv2.getTrackbarPos('s','controls'),cv2.getTrackbarPos('v','controls')),np.uint8),np.array((cv2.getTrackbarPos('H','controls'),cv2.getTrackbarPos('S','controls'),cv2.getTrackbarPos('V','controls')),np.uint8))
        cv2.imshow("mask" + str(i),mask)
        img = cv2.bitwise_and(img, img,mask= mask)
        cv2.imshow("img" + str(i),img)
        cv2.imshow("imgc" + str(i),cv2.cvtColor(img2,cv2.COLOR_HSV2BGR))
#cap.release()
cv2.destroyAllWindows()

