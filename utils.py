# coding=utf-8

import time
import json
import re
import sys
import cv2
import base64
import numpy as np
import urllib
import codecs
from PIL import Image
from StringIO import StringIO
from settings import logger

if sys.getdefaultencoding() != 'utf-8':
    reload(sys)
    sys.setdefaultencoding('utf-8')
    
nations = codecs.open('database/nation.txt', 'r', 'utf-8')
nation = ''
for n in nations:
    nation = nation + n.strip() + '|'
    if len(n.strip()) > 2:
        nation = nation + n.strip()[:-1] + '|'
nation = nation[:-1]

def quHouzui(name):
    if len(name) > 1:
        return re.sub(r'(省|市|(维吾尔|壮族|回族|)自治区|区|地区)|(\B(%s)*(自治州|盟|县|自治县|自治旗|矿区|特区|特别行政区))()$'%(nation), '', name)
    else:
        return name


LIST_province   = [i['name'] for i in json.loads(open('database/provinces.json', 'r').read())]
LIST_city       = [i['name'] for i in json.loads(open('database/cities.json', 'r').read())]
LIST_area       = [i['name'] for i in json.loads(open('database/areas.json', 'r').read())]
LIST_street     = [i['name'] for i in json.loads(open('database/streets.json', 'r').read())]

LIST_province   = LIST_province + [quHouzui(i) for i in LIST_province]
LIST_city       = LIST_city + [quHouzui(i) for i in LIST_city]
LIST_area       = LIST_area + [quHouzui(i) for i in LIST_area]

# print(LIST_province)
def process_text_classify(image, data_detect, text_model, mapping_dict, area_code, FLAG_vis):
    """ direct process text_classify, return, not parse
    """

    LIST_out_text = list()
    DICT_res = dict()
    for name in data_detect:
        inst = data_detect[name]
        inst['text'] = inst['text'].decode('utf-8')
        x0, y0, x1, y1 = inst['rect'][0], inst['rect'][1] + 0, inst['rect'][2], inst['rect'][3] + 0
        # 这两行我测试时只有这样子才能正常run，c是预测出来的类别，val表示预测出来的分数，
        # c = text_model.predict(' '.join(list(inst['text'])))
        # val = c.dec_values[str(c)]
        # 志伦哥改成这一句是什么原因呢
        c, val = text_model.predict(' '.join(list(inst['text'])))
        predict_type = mapping_dict[str(c)]

        # -----------------------------------
        # check 省、市、县（区）、街道
        # -----------------------------------
        if   inst['text'] in LIST_area:     predict_type = 'area'
        elif inst['text'] in LIST_city:     predict_type = 'city'
        elif inst['text'] in LIST_province: predict_type = 'province'
        elif inst['text'] in LIST_street:   predict_type = 'street'

        # -----------------------------------
        # 判断电话、手机、数字等
        # -----------------------------------
        if predict_type in ['shouji', 'dianhua']:
            if inst['text'].isdigit() == False:
                predict_type = 'ERROR'

        # -----------------------------------
        # 最后相关 post-processing 输出
        # -----------------------------------
        if u'室' in inst['text']:
            predict_type = 'address'

        if inst['text'] == 'gou':
            predict_type, val = 'gou', '1.0'

        # print inst['text'], predict_type, val, inst['rect']
        inst['text_type'] = predict_type
        inst['text_prob'] = val



        # -----------------------------------
        # area parsing 与位置组合
        # -----------------------------------
        x0, y0, x1, y1 = inst['rect'][0], inst['rect'][1] + 0, inst['rect'][2], inst['rect'][3] + 0
        rect = [x0, y0, x1, y1]
        to_add_text = '%s#@#%s' % (y0 + x0, inst['text'])
        prob_list = inst['prob']
        detect_info = inst['detect']
        res_inst = (to_add_text, rect, prob_list, detect_info, predict_type, val)
        LIST_out_text.append({'text': inst['text'], 'ocr_prob': prob_list, 'area': rect, 'detect': detect_info, 'predict_type': predict_type, 'predict_score': val})
    # 一张图的分类结果，再用规则过滤
    h, w = image.shape[0:2]
    # 对163图的强规则过滤
    if area_code == '163':
        # 若一张图出现了两个都分类为名字，那么看是否有一个出现了分错的情况，根据位置。
        dict_name = list()
        for _ in LIST_out_text:
            if _['predict_type'] == 'name':
                dict_name.append(_)
        if len(dict_name) > 1:
            for _ in dict_name:
                center_x = (_['area'][0]+_['area'][2])/2
                center_y = (_['area'][1]+_['area'][3])/2
                if center_y > 0.5*h:
                    # 出现逻辑不合理的分类结果，将这一个分类结果改为error，得分改为-1
                    for one_text in LIST_out_text:
                        if one_text['text'] == _['text']:
                            one_text['predict_type'] = 'ERROR'
                            one_text['predict_score'] = -1
                            break
                    else:
                        continue
        else:
            pass
    return LIST_out_text


def _str_to_img_base64(str_image, FLAG_color=False):
    """ convert base64 string to image
    """
    image = np.array(Image.open(StringIO(base64.b64decode(str_image))))
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)  # color space bug, fix
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


def _url_to_image(url):
    """ download the image, convert it to a NumPy array and to OpenCV format
    """
    resp = urllib.urlopen(url)
    image = np.asarray(bytearray(resp.read()), dtype="uint8")
    image = cv2.imdecode(image, cv2.IMREAD_COLOR)  # save color images
    return image


def _data_convert_image(data):
    """ standard image read and load online version
    """
    TIME_start = time.time()
    if isinstance(data, (str, unicode)):
        if data.startswith(('http:', 'https:')):
            logger.info('image url: %s' % (data))
            image = _url_to_image(data)
        elif data.endswith(('.jpg', '.png')):
            data = data.replace('\\', '/')
            logger.info('image filepath: %s' % (data))
            image = cv2.imread(data)
        elif isinstance(data, str) or isinstance(data, unicode):  # add base 64
            logger.info('image base64')
            image = _str_to_img_base64(data)
        else:
            logger.info('image data')
            image = _img_to_str_base64(data)
    else:
        image = data

    if len(image.shape) == 2: image = cv2.cvtColor(image, cv2.COLOR_GRAY2RGB)
    assert len(image.shape) == 3
    logger.info('image download cost %s' % (time.time() - TIME_start))
    return image


def IoU(Reframe, GTframe, FLAG_percent=False):
    """ 自定义函数，计算两矩形 IOU，传入为均为矩形对角线，（x,y）  坐标。
    """
    x1 = Reframe[0]
    y1 = Reframe[1]
    width1 = Reframe[2] - Reframe[0]
    height1 = Reframe[3] - Reframe[1]

    x2 = GTframe[0]
    y2 = GTframe[1]
    width2 = GTframe[2] - GTframe[0]
    height2 = GTframe[3] - GTframe[1]

    endx = max(x1+width1,x2+width2)
    startx = min(x1,x2)
    width = width1+width2-(endx-startx)

    endy = max(y1+height1,y2+height2)
    starty = min(y1,y2)
    height = height1+height2-(endy-starty)

    if width <=0 or height <= 0:
        ratio = 0 # 重叠率为 0
        ratio_re = 0
        ratio_gt = 0
    else:
        Area = width*height; # 两矩形相交面积
        Area1 = width1*height1 
        Area2 = width2*height2
        ratio = Area*1./(Area1+Area2-Area)
        ratio_re = Area * 1.0 / Area1
        ratio_gt = Area * 1.0 / Area2

    if FLAG_percent:
        return ratio, ratio_re, ratio_gt
    else:
        return ratio
