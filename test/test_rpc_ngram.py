# -*- coding: utf-8

import cv2, glob
import zerorpc
import os, sys
import numpy as np
import json
import time, shutil, base64
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



ngram_check = zerorpc.Client()
ngram_check.connect("tcp://192.168.1.7:12101") # ngram check
query = u'主持召开党内外人群座谈会'
query = u'广东省深圳市宝安区石岩镇塘头第三工业区12折9'
query = u'江苏省'
query = u'广西壮族自治区南宁市安阳县中华镇中华'
query = u'浙江省安吉县天黄坪镇马吉工业区188号'
query = u'安吉盛0竹木开发有限'
query = u'高新产业园区庆南道西92号'
query = u'338510'
query = u'太板大道195号(建哈哈公交站上行100'
query = u'广东省深圳市宝安区石岩镇塘头第三工业区12栋2'
query = u'交通路金士地汽车城二期14号'
query = u'北京市北京市平谷区夏各庄夏兴园'
query = u'宁徽合肥市德州大道东陈青石化厅小区1幢'
query = u'深信服科技'
query = u'上海上海市普际区武宁路300弄10-311'
query = u'罗勇宏'
query = u'深圳市宝安区石岩社区宏发佳特利高新园'
query = u'湖南省邵阳市新邵县货码街宝源大楼1单'
query = u'安徽省合肥市高新区天智路19号原创动'

res = ngram_check.post_check(query)
final_str =''
for index, char in enumerate(query):
    if res['data']['analysis'].has_key(str(index)):
        final_str += colored(query[index],'red') + str(res['data']['analysis'][str(index)]['errtype'])
    else: final_str += char
print final_str

# query = 'children are of2ten busier adults for they have to attend some good classes suc'
# res = ngram_check.post_check(query, None, 'en')
# eng_str = ''
# print res['data']['analysis'][0]
# # for index, char in enumerate(query):
# #     if res['data']['analysis'].has_key(str(index)):
# #         final_str += colored(query[index],'red') + str(res['data']['analysis'][str(index)]['errtype'])
# #     else: final_str += char
# # print final_str

