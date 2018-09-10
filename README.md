# Face Detection Function in Python for TouchDesigner

[![Software License](https://img.shields.io/badge/license-MIT-brightgreen.svg)](LICENSE)

## 用途 Usage

Face Detection Function in Python for Touchdesigner.
Touchdesigner itself doesn't have the function of developing face detection for camera.
When you don't have Kinect or RealSense at hand, you can consider using your PC/labtop's own camera as the input method of TouchDesigner.
Python combines the OpenCV library to implement simple face recognition and pass data to TD via OSC.

一个通过Python实现TD的面部识别功能的小工具。
Touchdesigner本身并没有针对摄像头来开发人脸识别的功能，当你手头没有Kinect、RealSense的时候可以考虑用你电脑本身的摄像头作为TouchDesigner的输入方式。
Python结合OpenCV库实现简易的人脸识别后，通过OSC将数据传给TD。

## 安装 Installation

Operating environment: Python 3.7 64-bit, TouchDesigner 099
* After installing Python, use the built-in pip to install the libraries we need:

运行环境：Python 3.7 64位、 TouchDesigner 099
* 安装完Python，利用自带的pip安装我们所需要的几个库：

```bash
$ pip install numpy
$ pip install argparse
$ pip install opencv-python
$ pip install python-osc
```

## 运行 Operation

* In your IDE, Modify the IP address and port of this machine or LAN (ipconfig /all)
* Run the file, cmd should refresh the location, address, port.
* Open the .toe file or create a new .toe file, create an OSCin OP, modify the corresponding IP address and port, and you should have received the face data.


* 在IDE中修改本机或局域网内其他主机的IP地址（可通过ipconfig /all 查询）和Port端口
* 运行文件，命令提示行中此时会不断刷新Face的位置、地址、端口。
```bash
$ python FaceDetectSendOSC.py
```
* 打开.toe文件或新建一个TD文件，创建一个OSCin的OP，修改对应的IP地址和端口，此时应该已经接收到摄像头数据。
