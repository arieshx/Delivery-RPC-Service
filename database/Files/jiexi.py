#coding=utf-8
import re
import codecs

#detect_result是识别的结果，img_width和img_height分别是原始图片的宽度和高度，img_type是指图片的类型是'161','162','163'还是'164'
def jiexi(detect_result, img_width, img_height, img_type):
    result = []

    for dr in detect_result:
        feature = [0] * 13
        feature[0] = 1.0 * dr['area'][0] / img_width
        feature[1] = 1.0 * dr['area'][1] / img_height
        feature[2] = 1.0 * (dr['area'][2]-dr['area'][0]) / img_width
        feature[3] = 1.0 * (dr['area'][3]-dr['area'][1]) / img_height
        feature[4] = 1.0 * len(dr['text']) / 10
        feature[5] = 1 if re.match(r'\d+$',dr['text']) else 0
        for pcd in pcds:
            if pcd in dr['text']:
                feature[6] = 1
                break
        if img_type == '161':
            feature[7] = 1
        elif img_type == '162':
            feature[8] = 1
        elif img_type == '163':
            feature[9] = 1
        elif img_type == '164':
            feature[10] = 1
        else:
            raise Exception("img_tpye must be one of '161','162','163','164'")
        feature[11] = predict_type[dr['predict_type']]
        feature[12] = dr['predict_score']
        result.append(feature)
    return result


pcds = codecs.open('randomAddress.txt', 'r', 'utf-8').read().split()
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
        'street:':13
    }

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
print(jiexi(detect_result,100,100,'161'))