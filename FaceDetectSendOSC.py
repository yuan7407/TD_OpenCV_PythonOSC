import numpy as np
import cv2
import argparse

from pythonosc import osc_message_builder
from pythonosc import udp_client

#https://github.com/Itseez/opencv/blob/master/data/haarcascades/haarcascade_frontalface_default.xml
face_cascade = cv2.CascadeClassifier('haarcascade_frontalface_default.xml')

FaceisDetected = 0
FacePositionX = 0
countImg = 0

cap = cv2.VideoCapture(0)
while 1:
    FaceisDetected = 0
    if __name__ == "__main__":
      parser = argparse.ArgumentParser()
      parser.add_argument("--ip", default="localhost", #change IP address here 改你的IP地址
          help="The ip of the OSC server")
      parser.add_argument("--port", type=int, default=5005, #change your port here 改你的端口
          help="The port the OSC server is listening on")
      args = parser.parse_args()

      client = udp_client.SimpleUDPClient(args.ip, args.port)

    ret, img = cap.read() # capture camera image signal 读取摄像头信号
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, 1.3, 5)

    for (x,y,w,h) in faces:
        FaceisDetected = 1
        countImg = countImg + 1
        #cv2.rectangle(img,(x,y),(x+w,y+h),(255,0,0),2)
        roi_gray = gray[y:y+h, x:x+w]
        roi_color = img[y:y+h, x:x+w]

        FacePositionX = x
        print(FacePositionX)
        #for (ex,ey,ew,eh) in eyes:
    #cv2.rectangle(roi_color,(ex,ey),(ex+ew,ey+eh),(0,255,0),2)  ##This will draw a rectangle when face is detected. 在识别到的人脸上面画一个矩形。
    #cv2.imwrite('Photo_' + str(countImg) + '.png',img)  ##This will save an array of the face images. 保存为识别到的人脸图片序列
    cv2.imwrite('1.png',img)
    cv2.imshow('img',img)

    client.send_message("/FaceisDetected", int(FaceisDetected)) ## Send osc message 把脸部检测的信号发送给TD
    client.send_message("/FPosX", int(FacePositionX)) ## Send osc message 把脸部的位置信号发送给TD

    ## Must be an int/float, the variable FacePositionX is not an int. 同时要注意把数值转化为整数型
    #time.sleep(0.1)
    print(args)

    k = cv2.waitKey(30) & 0xff
    if k == 27:
        break

cap.release()
cv2.destroyAllWindows()
