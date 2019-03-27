# -*- coding: utf-8
# ------------------------------------------
# convet json to deppon data
# ------------------------------------------

# 1. string check RULEs. 例如电话号码、省市县、客户编码等各类字段检查
# 2. position RULEs
# 3. 


import cv2, glob
import zerorpc
import os, sys, itertools
import numpy as np
import json, zbar, io
import time, shutil, base64, re
from PIL import Image
# import util_draw_cn as util_render


# ----------------------------------
# load area database, 省市县数据库
# ----------------------------------
LIST_province   = [i['name'] for i in json.loads(open('database/provinces.json', 'r').read())]
LIST_city       = [i['name'] for i in json.loads(open('database/cities.json', 'r').read())]
LIST_area       = [i['name'] for i in json.loads(open('database/areas.json', 'r').read())]
LIST_street     = [i['name'] for i in json.loads(open('database/streets.json', 'r').read())]

LIST_province   = LIST_province + [i.replace(u'省', '') for i in LIST_province if u'省' in i] + [u'内蒙', u'北京', u'天津', u'上海', u'重庆']
LIST_city       = LIST_city + [i.replace(u'市', '') for i in LIST_city if u'市' in i]
LIST_area       = LIST_area + [i.replace(u'区', '') for i in LIST_area if u'区' in i]

def IoU(Reframe, GTframe):
    """ 自定义函数，计算两矩形 IOU，传入为均为矩形对角线，（x,y） 坐标。
        frame: x0, y0, x1, y1
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

    # 如在区域内部，则认为完全是该区域内容, set ratio = 1.0
    if (GTframe[0] <= Reframe[0] <= Reframe[2] <= GTframe[2]) and (GTframe[1] <= Reframe[1] <= Reframe[3] <= GTframe[3]):
        ratio = 1.0

    return ratio


# ------------------------------------------
# check rules
# ------------------------------------------

# def rule_money(text):
#     """
#     只能录入数字，四舍五入，保留整数；录入的值超过20000，人工审核
#     """

def rule_custom_number(text):
    """
    字母必须大写，有“-”必须录入
    常见格式：
    以4开头的九位纯数字（4xxxxxxxx）
    以5开头的九位纯数字（5xxxxxxxx）
    以6开头的九位纯数字（6xxxxxxxx）
    六位纯数字
    4位数字（4092）

    八位数字-六位数字（20110215-059349）
    八位数字-八位数字（20110215-05934918）
    八位数字-三位数字-四位数字（20100121-139-3775）

    F开头的数字（F2015043009210740）
    E开头的数字（E201702157899130）
    S开头的八位数字-八位数字（S20140809-80649077）

    4位数字_一位数字（0006_2）
    """

    if text[0] in ['4', '5', '6'] and len(text) == 9 and text.isdigit(): return True
    if len(text) in [4, 6] and text.isdigit(): return True

    if text.count('-') == 1:
        prev_num = text.split('-')[0]
        next_num = text.split('-')[1]
        if len(prev_num) == 8 and len(next_num) in [6, 8] and prev_num.isdigit() and next_num.isdigit(): return True

    if text.count('-') == 2:
        prev_num = text.split('-')[0]
        midd_num = text.split('-')[1]
        last_num = text.split('-')[2]
        if len(prev_num) == 8 and len(midd_num) == 3 and len(last_num) == 4 and prev_num.isdigit() and midd_num.isdigit() and last_num.isdigit(): return True

    if text[0] in ['F', 'E'] and text[1 : ].isdigit(): return True
    if text[0] == 'S' and text.count('-') == 1:
        text = text[1 : ]
        if text.split('-')[0].isdigit() and text.split('-')[1].isdigit() and len(text.split('-')[0]) == 8 and len(text.split('-')[1]) == 8: return True

    if text.count('_') == 1 and text.split('_')[0].isdigit() and len(text.split('_')[0]) == 4 and text.split('_')[1].isdigit() and len(text.split('_')[1]) == 1: return True
    return False

# print rule_custom_number('412345678')
# print rule_custom_number('4120345678')
# print rule_custom_number('4120')
# print rule_custom_number('412345')

# print rule_custom_number('20110215-059349')
# print rule_custom_number('201102215-059349')
# print rule_custom_number('20110215-0593459')
# print rule_custom_number('20110215-05934918')
# print rule_custom_number('20110215-0593498')
# print rule_custom_number('20100121-139-3775')
# print rule_custom_number('201002121-139-3775')

# print rule_custom_number('F2015043009210740')
# print rule_custom_number('F20150430A09210740')
# print rule_custom_number('E201702157899130')
# print rule_custom_number('E201702157A899130')
# print rule_custom_number('S20140809-80649077')
# print rule_custom_number('S201403809-80649077')

# print rule_custom_number('0006_2')
# print rule_custom_number('00062_2')



def rule_phone_numbers(text):
    """
    1、电话号码只能输入纯数字，不允许出现汉字，英文字母等其他字符；
    2、电话中的符号“-”不可省略，最多出现两个，不能位于首尾，也不能连续输入；其他符号均不支持；
    3、电话号码最多20个字符
    Test: 02131350166, 021-31350166, 02-31356166, 021-3135013366666, 021-31350166-01等
    """
    if len(text) > 20: return False

    if '-' in text:
        if text.count('-') > 2: return False
        if text.index('-') == 0: return False
        if '--' in text: return False
        text = text.replace('-', '')
    
    return text.isdigit()

# print rule_phone_numbers('02131350166')
# print rule_phone_numbers('021-31350166')
# print rule_phone_numbers('02-31356166')
# print rule_phone_numbers('021-3135013366666')
# print rule_phone_numbers('021-31350166-01')
# print rule_phone_numbers('0213135汉0166')
# print rule_phone_numbers('02131-3?50166')
# print rule_phone_numbers('021-31350166-01k')
# print rule_phone_numbers('021--3135016601')
# print rule_phone_numbers('-021-3135016601')
# print rule_phone_numbers('021-3135019999999966-01')


def detect_barcode(image):
    """ detect barcode position in image
    """

    image_top = image[0 : int(image.shape[0] * 0.3), :, :]
    data = cv2.imencode('.jpg', image_top)[1].tostring()
    scanner = zbar.ImageScanner()
    scanner.parse_config('enable')
    pil = Image.open(io.BytesIO(data)).convert('L')
    width, height = pil.size
    raw = pil.tobytes()
    image_top = zbar.Image(width, height, 'Y800', raw)
    scanner.scan(image_top)
    result = [(symbol.type, symbol.data) for symbol in image_top]

    if len(result) > 0:
        for res in result:
            print res
            print res.type, res.data, res.quality, res.position


def init_layout(FILE_template):
    """ init guxiang's template json
    """
    DATA_layout = json.loads(open(FILE_template, 'r').read())
    LIST_template_area = list()
    with open('layout_readme.txt', 'w') as o:
        for name in DATA_layout:
            for inst in DATA_layout[name]['items']:
                inst['code'] = name
                LIST_template_area.append(inst)
                print >> o, ('%s\t%s' % (inst['key'], inst['name'])).encode('utf-8')
    return LIST_template_area


def init_deppon_layout():
    """ init cut-off deppon layout
    """
    DICT_template_area = dict()
    for area_name in ['161', '162', '163', '164']:
        DICT_template_area[area_name] = list()
        for area_inst in json.loads(open('database/layout/%s.json' % area_name, 'r').read())['items']:
            DICT_template_area[area_name].append(area_inst)
    return DICT_template_area


DICT_template_area = init_deppon_layout()
def process_text_classify(image, data_detect, text_model, mapping_dict, area_code, FLAG_vis):
    """ direct process text_classify, return, not parse
    """

    """
    # Merge address to parse
    # 更新 template area，将 pos 结果映射上去
    h, w, _ = image.shape
    for idx, inst in enumerate(DICT_template_area[area_code]):
        x0, y0, x1, y1 = int(w * inst['area'][0]), int(h * inst['area'][1]), int(w * inst['area'][2]), int(h * inst['area'][3])
        DICT_template_area[area_code][idx]['pos'] = [x0, y0, x0 + x1, y0 + y1]
        y0 += 30
        x1 -= 10
        cv2.rectangle(image, (x0, y0), (x1 + x0, y1 + y0), (255, 0, 0), 2)
    """
    
    LIST_out_text = list()
    DICT_res = dict()
    for name in data_detect:
        inst = data_detect[name]
        inst['text'] = inst['text'].decode('utf-8')
        x0, y0, x1, y1 = inst['rect'][0], inst['rect'][1] + 0, inst['rect'][2], inst['rect'][3] + 0
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
        # print inst['text'], predict_type, '*****'

        """
        if predict_type in ['city', 'province', 'area']:
            name = {'city': 'rcCityName', 'area': 'rcDistName', 'province': 'rcProvName'}[predict_type]

        elif predict_type in ['shouji', 'dianhua'] and inst['text'].isdigit():
            if area_code == 161:
                name = 'deliveryCustomerPhone'
            elif area_code == 163:
                name = 'receiveCustomerPhone'
        
        elif predict_type in ['address']:
            if area_code == 161:
                name = 'deliveryCustomerAddress'
            elif area_code == 163:
                name = 'receiveCustomerAddress'

        else:
            # 判断 detect rect 与 block area 是否重合，且有几块与 blocks 相邻
            # max area, 最可能重合所属题区域
            LIST_IoU = [IoU(rect, i['pos']) for i in DICT_template_area[area_code]]
            rect_idx = np.argmax(LIST_IoU)
            name = DICT_template_area[area_code][rect_idx]['key']

            # 如区域判断是这类地址，但
            if name in ['rcCityName', 'rcProvName', 'rcDistName']:
                if predict_type in ['address']:
                    name = 'receiveCustomerAddress'
                elif predict_type in ['shouji', 'dianhua']:
                    name = 'receiveCustomerPhone'
                elif predict_type in ['name']:
                    name = 'receiveCustomerName'

        if DICT_res.has_key(name) == False: DICT_res[name] = []
        DICT_res[name].append(res_inst)
        """

    """
    # ----------------------------------------
    # merge all result into one string
    # ----------------------------------------
    # 根据表格每个字段名，如包含多条（行）信息，对 text, area, prob_val 进行组合
    print '-' * 50
    for name in sorted(DICT_res.keys()):

        text = ''
        text_area = list()
        text_prob = list()
        text_detect = list()
        for s in sorted(DICT_res[name]):
            text += s[0].split('#@#')[1]
            text_area.append(s[1])
            text_prob.extend(s[2])
            text_detect.append(s[3])

        # 结合模型，判断 text string 类型，电话、姓名、地址等
        c, val = text_model.predict(' '.join(list(text)))
        predict_type = mapping_dict[str(c)]

        DICT_merge_res[name]        = text
        DICT_merge_res_area[name]   = {'text': text, 'text_area': text_area, 'text_prob': text_prob, 'text_detect': text_detect, 'model_type': predict_type, 'model_prob': val}
        if DICT_merge_res[name] == '': del DICT_merge_res[name]
        if DICT_merge_res_area[name]['text'] == '': del DICT_merge_res_area[name]
        print name, text
    """
    
    DICT_merge_res = dict()
    DICT_merge_res_area = dict()
    # return DICT_merge_res, DICT_merge_res_area, LIST_out_text
    return LIST_out_text



def process(image, data_detect, text_model, mapping_dict, FLAG_vis):
    """ main function to align data to template
    """

    h, w, _ = image.shape
    if FLAG_vis: image_merge = image.copy()
    DICT_res = {'receiveDetailAddress': [], 'deliveryCustomerAddress': [], 'deliveryCustomerName': [], 'deliveryCustomerPhone': [], 'receiveCustomerPhone': []}

    # 更新 template area，将 pos 结果映射上去
    for idx, inst in enumerate(LIST_template_area):
        x0, y0, x1, y1 = int(w * inst['area'][0]), int(h * inst['area'][1]), int(w * inst['area'][2]), int(h * inst['area'][3])
        # add 50 px padding with depon and us
        if h <= 925: 
            y0 = y0 - 55
            y1 = y1 - 55
        LIST_template_area[idx]['pos'] = [x0, y0, x0 + x1, y0 + y1]


    # 遍历理论结果与实际检测，将结果赋予到模板上
    for inst in data_detect:
        x0, y0, x1, y1 = inst['rect'][0], inst['rect'][1] + 0, inst['rect'][2], inst['rect'][3] + 0

        # 判断 detect rect 与 block area 是否重合，且有几块与 blocks 相邻
        # max area, 最可能重合所属题区域
        rect = [x0, y0, x1, y1]
        prob_list = inst['prob']
        detect_info = inst['detect']
        LIST_IoU = [IoU(rect, i['pos']) for i in LIST_template_area]
        rect_idx = -1
        rect_val = np.max(LIST_IoU)

        # 判断条件：内容完全在 rect 内，或者，相交面积大于一定比例
        if rect_val >= 0.05:

            rect_idx = np.argmax(LIST_IoU)
            none_zero = np.nonzero(LIST_IoU)[0]
            render_text = LIST_template_area[rect_idx]['name'] + ': ' + inst['text'].decode('utf-8')
            to_add_text = '%s#@#%s' % (y0, inst['text'])

            # save text to order layout
            name = LIST_template_area[rect_idx]['key']
            if DICT_res.has_key(name) == False: DICT_res[name] = []

            # ----------------------------------------
            # update template with rules
            # ----------------------------------------
            # 结合模型，判断 text string 类型，电话、姓名、地址等，因为有时机打会录入错误
            # 特殊考虑：gou
            if inst['text'] == 'gou':
                predict_type, val = 'gou', '1.0'
            elif inst['text'].isdigit() and len(inst['text']) <= 6:
                predict_type, val = 'number', '1.0'
            else:
                c, val = text_model.predict(' '.join(list(inst['text'].decode('utf-8'))))
                predict_type = mapping_dict[str(c)]

                # 特殊处理场景
                # 1. clientCode, 月结编码，易混入姓名、电话等信息，如发现不是 number，直接变成姓名 or 电话
                # 2. detailAddress, 详细地址部分需要后续组合

            FLAG_need_check = 'receive' in name or 'delivery' in name
            print FLAG_need_check, name, inst['text'].isdigit(), ' '.join(list(inst['text'].decode('utf-8'))), predict_type, val

            if FLAG_need_check and inst['text'] != 'gou':

                # 月结编码中，姓名、电话等错位情况
                if name == 'deliveryClientCode':
                    if predict_type == 'name':
                        DICT_res['deliveryCustomerName'].append((to_add_text, rect, prob_list, detect_info))
                    elif predict_type == 'phone':
                        DICT_res['deliveryCustomerPhone'].append((to_add_text, rect, prob_list, detect_info))

                # predict val 应该 >= 0.8，概率太低
                # 寄件人区域处理
                elif 'delivery' in name and predict_type == 'address' and val >= 0.8:
                    DICT_res['deliveryCustomerAddress'].append((to_add_text, rect, prob_list, detect_info))

                # 寄件人区域处理
                elif 'delivery' in name and predict_type == 'phone' and val >= 0.8:
                    DICT_res['deliveryCustomerPhone'].append((to_add_text, rect, prob_list, detect_info))

                # 收件人区域处理
                elif 'receive' in name and predict_type == 'address' and val >= 0.8:
                    DICT_res['receiveDetailAddress'].append((to_add_text, rect, prob_list, detect_info))

                # 收件人姓名与电话判断
                elif 'receive' in name and predict_type == 'phone' and val >= 0.8:
                    DICT_res['receiveCustomerPhone'].append((to_add_text, rect, prob_list, detect_info))
                
                # 如果概率值 <= 0.8，则按照位置区域进行处理
                else:
                    # print '***', name, to_add_text 
                    DICT_res[name].append((to_add_text, rect, prob_list, detect_info))
            
            else:
                DICT_res[name].append((to_add_text, rect, prob_list, detect_info))

        else:
            render_text = inst['text']

        # # vis images
        # if FLAG_vis:
        #     image = ft.draw_text(image, (x0, y0 - 20), render_text, 18, (0, 0, 0))
        #     name = inst['filename']
        #     if 'hand' in os.path.basename(name): color = (255, 0, 0)
        #     elif 'print' in os.path.basename(name): color = (0, 255, 255)
        #     elif 'wrong' in os.path.basename(name): color = (0, 0, 255)
        #     else: color = (0, 0, 255)
        #     cv2.rectangle(image, (x0, y0), (x1, y1), color, 2)


    # ----------------------------------------
    # merge all result into one string
    # ----------------------------------------
    # 根据表格每个字段名，如包含多条（行）信息，对 text, area, prob_val 进行组合
    print '-' * 50
    DICT_merge_res = dict()
    DICT_merge_res_area = dict()
    for name in sorted(DICT_res.keys()):

        text = ''
        text_area = list()
        text_prob = list()
        text_detect = list()
        for s in sorted(DICT_res[name]):
            text += s[0].split('#@#')[1]
            text_area.append(s[1])
            text_prob.extend(s[2])
            text_detect.append(s[3])

        # 结合模型，判断 text string 类型，电话、姓名、地址等
        c, val = text_model.predict(' '.join(list(text.decode('utf-8'))))
        predict_type = mapping_dict[str(c)]

        DICT_merge_res[name]        = text
        DICT_merge_res_area[name]   = {'text': text, 'text_area': text_area, 'text_prob': text_prob, 'text_detect': text_detect, 'model_type': predict_type, 'model_prob': val}
        if DICT_merge_res[name]     == '': del DICT_merge_res[name]
        if DICT_merge_res_area[name]['text'] == '': del DICT_merge_res_area[name]
        print name, text

    if FLAG_vis:
        for idx, inst in enumerate(LIST_template_area):
            x0_, y0_, x1_, y1_ = inst['pos'][0], inst['pos'][1], inst['pos'][2], inst['pos'][3]
            cv2.rectangle(image_merge, (x0_, y0_), (x1_, y1_), (0, 0, 255), 1)
            
            if DICT_merge_res.has_key(inst['key']):
                # print inst['key'], DICT_merge_res.has_key(inst['key']), DICT_merge_res[inst['key']]
                render_text = '%s: %s' % (inst['name'], DICT_merge_res[inst['key']].decode('utf-8'))
                image_merge = ft.draw_text(image_merge, (x0_, y0_ - 20), render_text, 18, (0, 0, 0))

    return DICT_merge_res, DICT_merge_res_area, image, image_merge


# ft = util_render.put_chinese_text('msyh.ttc')

# FOLDER_image = 'data/gx_10000'
# FILE_layout = 'layout_config.json'
# LIST_res_json = glob.glob('block_vis/json/*.json')

# FILE_template = 'layout_config.json'
# LIST_template_area = init_layout(FILE_template)

# for fname in LIST_res_json[0 : 100]:
#     # if 'img20180202_14261617.jpg' not in fname: continue
#     data = json.loads(open(fname, 'r').read())
#     im_name = os.path.join(FOLDER_image, os.path.basename(fname.replace('_vis.json', '')))
#     image = cv2.imread(im_name)

#     if image is None: continue
#     print fname


#     # vis image in HTML
#     LIST_vis_data = list()
#     for idx, inst in enumerate(data['detect']):
#         vis_inst = {'text': inst['text'], 'prob': inst['prob'], 'pos': [inst['rect'][0], 0, 0, inst['rect'][1] + 50], 'q_id': str(idx)}
#         LIST_vis_data.append(vis_inst)

#     HTML = open('word-prob-vis-v1.html', 'r').read()
#     HTML = HTML.replace('var json = ###', 'var json = %s' % json.dumps(LIST_vis_data))
#     HTML = HTML.replace('<img src="###">', '<img src="%s">' % im_name)
#     HTML = HTML.replace('var width = ###', 'var width = %s' % image.shape[1])
#     HTML = HTML.replace('var height = ###', 'var height = %s' % image.shape[0])
#     with open('%s.html' % os.path.basename(im_name), 'w') as o: print >> o, HTML

#     # data_detect = data['detect']
#     # res, image = process(image, data_detect, LIST_template_area, True)

#     # FILE_result = os.path.join(os.getcwd(), os.path.basename(im_name) + '.json')
#     # with open(FILE_result, 'w') as o: print >> o, json.dumps(res)
#     # cv2.imwrite(os.path.basename(im_name), image)
