# -*- coding: utf-8
# ----------------------------------------
# Automatic Pass Percent test in Deppon
# ----------------------------------------
# 2018/08

import cv2, glob
import zerorpc
import os, sys
import numpy as np
import json
import time, shutil, base64
import requests
from termcolor import colored

def _str_to_img_base64(str_image, FLAG_color=False):
    """ convert base64 string to image
    """
    image = np.array(Image.open(StringIO(base64.b64decode(str_image))))
    if len(image.shape) == 3 and FLAG_color: return image
    if len(image.shape) == 2 and FLAG_color: return cv2.cvtColor(image, cv2.COLOR_GRAY2RGB)
    if len(image.shape) == 3 and FLAG_color == False: return cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
    if len(image.shape) == 2 and FLAG_color == False: return image


def _img_to_str_base64(image):
    """ convert image to base64 string 
    """
    img_encode = cv2.imencode('.jpg', image)[1]    
    img_base64 = base64.b64encode(img_encode)
    return img_base64



def IoU(Reframe, GTframe):
    """ 自定义函数，计算两矩形 IOU，传入为均为矩形对角线，（x,y）  坐标。
    """
    x1 = Reframe[0];
    y1 = Reframe[1];
    width1 = Reframe[2] - Reframe[0];
    height1 = Reframe[3] - Reframe[1];

    x2 = GTframe[0];
    y2 = GTframe[1];
    width2 = GTframe[2] - GTframe[0];
    height2 = GTframe[3] - GTframe[1];

    endx = max(x1+width1,x2+width2);
    startx = min(x1,x2);
    width = width1+width2-(endx-startx);

    endy = max(y1+height1,y2+height2);
    starty = min(y1,y2);
    height = height1+height2-(endy-starty);

    if width <=0 or height <= 0:
        ratio = 0 # 重叠率为 0 
    else:
        Area = width*height; # 两矩形相交面积
        Area1 = width1*height1; 
        Area2 = width2*height2;
        ratio = Area*1./(Area1+Area2-Area);
    # return IOU
    return ratio #,Reframe,GTframe



NUM_total = 0
NUM_pass  = 0


URL_request = 'http://manhattanic.hexin.im/image/getList?_limit=50000&_page=11'
data = json.loads(requests.get(URL_request).text)['data']

for inst in data:
    image_path = inst['url']
    uid = inst['uid']
    if '_163.jpg' not in image_path: continue


    print '*' * 50
    print image_path
    NUM_total += 1

    # check image type, 161, 162, 163, 164
    detect_res = inst['detectResult']
    deppon_res = inst['depponOcrResult']
    if detect_res is None: continue

    # print vis two result
    print '-' * 30
    for name in sorted(deppon_res.keys()):
        if name in ['isReturn', 'waybillNo']: continue
        print name, deppon_res[name]

    print '-' * 30
    for name in sorted(detect_res.keys()):
        if type(detect_res[name]) == dict:
            print name, detect_res[name]['text']
        else:
            print name, detect_res[name]
    print '-' * 30

    # check values
    FLAG_pass = 1
    for name in deppon_res.keys():
        # 164 badcase
        if name in ['collectionAccount', 'packageFeeCanvas', 'refundType', 'codAmount', 'accountName']: continue
        if name in ['returnReason', 'waybillNo']: continue
        if name == 'isReturn': continue

        # check if two result is eqaul
        if type(detect_res[name]) == int:
            if detect_res[name] != deppon_res[name]:
                FLAG_pass = 0
                print '%s\t%s\t%s' % (name, detect_res[name], deppon_res[name])
        
        elif type(detect_res[name]) == dict:
            if type(deppon_res[name]) == int:
                if detect_res[name]['text'] != str(deppon_res[name]):
                    FLAG_pass = 0
                    print '%s\t%s\t%s' % (name, detect_res[name]['text'], deppon_res[name])

            else:
                if detect_res[name]['text'] != deppon_res[name]:
                    FLAG_pass = 0
                    print '%s\t%s\t%s' % (name, detect_res[name]['text'], deppon_res[name])

    if FLAG_pass == 1: NUM_pass += 1

# stat final outputs
print '*' * 50
print NUM_pass, NUM_total, 1.0 * NUM_pass/NUM_total