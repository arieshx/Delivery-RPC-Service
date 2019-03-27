#coding=utf-8
import os
import re
import codecs
import inspect
import numpy as np

# detect_result是识别的结果，img_width和img_height分别是原始图片的宽度和高度，img_type是指图片的类型是'161','162','163'还是'164'
# 最新提取出的特征是 x,y,w,h,length,has_PCD,class_name,x_y,w_h,digital_percent,digital_num,youxiangongsi_num,shengshixianqujiedao_num
def parse(detect_result, img_width, img_height, img_type):
    result = []
    
    for dr in detect_result:
        feature = [0] * 13
        feature[0] = 1.0 * dr['area'][0] / img_width
        feature[1] = 1.0 * dr['area'][1] / img_height
        feature[2] = 1.0 * (dr['area'][2]-dr['area'][0]) / img_width
        feature[3] = 1.0 * (dr['area'][3]-dr['area'][1]) / img_height
        feature[4] = 1.0 * len(dr['text']) / 10
        # feature[5] = 1 if re.match(r'\d+$',dr['text']) else 0
        for pcd in pcds:
            if pcd in dr['text']:
                feature[5] = 1
                break
        
        feature[6] = predict_type[dr['predict_type']]
        feature[7] = feature[0]/(1+feature[1])
        feature[8] = feature[2]/(feature[3])
        digital_percent, digital_num = get_digital_info(dr['text'])
        feature[9] = digital_percent
        feature[10] = digital_num
        youxiangongsi_num = get_has_youxingongsi_num(dr['text'])
        feature[11] = youxiangongsi_num
        shengshixianqujiedao_num = get_has_shengshixianqujiedao_num(dr['text'])
        feature[12] = shengshixianqujiedao_num
        result.append(feature)

    return np.asarray(result)


def get_digital_info(content):
    """
    通过文本内容得到其中的数字个数和数字占百分比
    :param content:
    :return:
    """
    content = str(content)
    content = content.decode('utf-8')
    int_num = 0
    for _ in content:
        if _.isdigit():
            int_num+=1
    char_num = len(content)
    if char_num==0:
        int_percent = 0
    else:
        int_percent = int_num*1./char_num
    return int_percent, int_num

def get_has_youxingongsi_num(content):
    """
    根据内容确定是不是含有有限公司的字样
    :param content:
    :return:
    """
    content = str(content)
    content = content.decode('utf-8')
    care_list = [u'有', u'限', u'公', u'司']
    youxiangongsi_num = 0
    for _ in content:
        if _ in care_list:
            youxiangongsi_num+=1
    return youxiangongsi_num

def get_has_shengshixianqujiedao_num(content):
    """
    根据内容，给出是否拥有地址关键字的数目
    :param content:
    :return:
    """
    content = str(content)
    content = content.decode('utf-8')
    care_list = ['省', '市', '自治区', '市辖区', '市', '自治州', '地区', '盟', '区', '县', '自治县', '林区', '旗', '自治旗', '街道办事处', '街道', '办事处', '乡', '苏木', '镇', '农场', '监狱', '区公所', '居委会', '村委会', '嘎查', '社区']
    care_list = [_.decode('utf-8') for _ in care_list]
    shengshixianqujiedao_num = 0
    for _ in care_list:
        if _ in content:
            shengshixianqujiedao_num+=1
    return shengshixianqujiedao_num
detect_result = [{"detect":
    {"y2": 397.0, "x2": 580.0, "score": 0.2071559727191925, "x3": 479.0, "y1": 352.0, "y0": 352.0, "x0": 479.0, "x1": 580.0, "y3": 397.0},
   "area": [469, 352, 580, 399],
   "text": "北京",
   "predict_type": "leibie",
   "predict_score": 0.5388677865314488,
   "ocr_prob": [0.175474]},{"detect":
    {"y2": 397.0, "x2": 580.0, "score": 0.2071559727191925, "x3": 479.0, "y1": 352.0, "y0": 352.0, "x0": 479.0, "x1": 580.0, "y3": 397.0},
   "area": [412, 353, 511, 429],
   "text": "1234",
   "predict_type": "leibie",
   "predict_score": 0.5388677865314488,
   "ocr_prob": [0.175474]}]

head, tail = os.path.split(inspect.getfile(inspect.currentframe()))
pcds = codecs.open('%s/randomAddress.txt' % head, 'r', 'utf-8').read().split()
predict_type = {
    'province':1,
    'city':2,
    'address':3,
    'town':4,
    'name':5,
    'shouji':6,
    'dianhua':7,
    'number':8,
    'leibie':9,
    'gou':10,
    'ERROR':11,
    'area':12,
    'street':13
}

# print parse(detect_result, 100, 100, '161')
