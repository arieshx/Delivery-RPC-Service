# -*-coding:utf-8-*-
# ----------------------------------------------
# Shanghai Depon Express Predict
# Zhilun YANG
# 12/05/2017
# ----------------------------------------------

import os
import re
import cv2
import sys
import glob
import time
import json
import base64
import shutil
import urllib
import socket
import zerorpc
import traceback
from matplotlib import pyplot as plt

sys.path.append('./addressTranslate')
# import translate
# from addressTranslate import translate
from back_code.network import translate
import numpy as np
from PIL import Image
from StringIO import StringIO
from tgrocery import Grocery
from itertools import combinations
from sklearn.externals import joblib

import utils
from check import rule_check
from settings import logger
from database.model import parse_feature as feature_unit


class MainRpc(object):

    def __init__(self):

        # ----------------------------------
        # load position predict model
        # ----------------------------------
        # categery,x,y,w,h,length,is_digital,has_PCD,is_161,is_162,is_163,is_164
        # self.GBC_best = joblib.load('database/model/GBC_origin.model', mmap_mode=None)
        self.GBC_best_161 = joblib.load('database/model/GBC_origin_161_1.model', mmap_mode=None)
        self.GBC_best_163 = joblib.load('database/model/GBC_origin_163_5.model', mmap_mode=None)
        self.GBC_best_164 = joblib.load('database/model/GBC_origin_164_1.model', mmap_mode=None)
        self.position_map = {
                            '0': 'deliveryCompany',
                            '1': 'deliveryCustomerName',
                            '2': 'deliveryCustomerPhone',
                            '3': 'deliveryCustomerAddress',
                            '4': 'clientCode',
                            '5': 'notificationMode',
                            '6': 'receiveCompany',
                            '7': 'receiveCustomerName',
                            '8': 'receiveCustomerPhone',
                            '9': 'receiveCustomerAddress',
                            '10': 'goodsName',
                            '11': 'insuranceAmount',
                            '12': 'sameDayRefund',
                            '13': 'threeDaysRefund',
                            '14': 'codAmount',
                            '15': 'accountName',
                            '16': 'collectionAccount',
                            '17': 'packageFeeCanvas',
                            '18': 'deliveryInboundFee',
                            '19': 'original',
                            '20': 'fax',
                            '21': 'other'
        }
        self.cls_dict_161 = {
            0: 0,
            1: 1,
            2: 2,
            3: 3,
            4: 5,
            5: 4,
            6: 21,
        }
        self.position_map_161 = {
            0: 'deliveryCompany',
            1: 'deliveryCustomerName',
            2: 'deliveryCustomerPhone',
            3: 'deliveryCustomerAddress',
            4: 'notificationMode',
            5: 'clientCode',
            6: 'other',
        }
        self.cls_dict_163 = {
            0: 6,
            1: 7,
            2: 8,
            3: 9,
            4: 10,
            5: 21,
        }
        self.position_map_163 = {
            0: 'receiveCompany',
            1: 'receiveCustomerName',
            2: 'receiveCustomerPhone',
            3: 'receiveCustomerAddress',
            4: 'goodsName',
            5: 'other',
        }
        self.cls_dict_164 = {
            0: 11,
            1: 12,
            2: 13,
            3: 14,
            4: 15,
            5: 16,
            6: 17,
            7: 18,
            8: 19,
            9: 20,
            10: 21,
        }
        self.position_map_164 = {
            0: 'insuranceAmount',
            1: 'sameDayRefund',
            2: 'threeDaysRefund',
            3: 'codAmount',
            4: 'accountName',
            5: 'collectionAccount',
            6: 'packageFeeCanvas',
            7: 'deliveryInboundFee',
            8: 'original',
            9: 'fax',
            10: 'other',
        }
        # ----------------------------------
        # load text predict model
        # ----------------------------------
        logger.info('------------------- start text predict model ----------------------')
        self.mapping_dict = {
            '3': 'address',
            '4': 'town',
            '5': 'name',
            '6': 'shouji',
            '7': 'dianhua',
            '9': 'leibie'
        }

        classMap = {
            '1': 'province',
            '2': 'city',
            '3': 'address',
            '4': 'town',
            '5': 'name',
            '6': 'shouji',
            '7': 'dianhua',
            '8': 'number',
            '9': 'leibie',
            '10': 'gou',
            '11': 'ERROR',
            '12': 'area',
            '13': 'street'
        }
        self.text_model = Grocery('text_predict/all_no_town')
        self.text_model.load()

        # text_predict = '湖 南 省 长 沙 市'
        # print type(self.text_model.predict(text_predict))
        # c, val = self.text_model.predict(text_predict)
        # logger.info('text input:  %s ' % text_predict)
        # logger.info('text output: %s, %s' % (self.mapping_dict[str(c)], val))
        # logger.info('------------------- finish text predict model ----------------------')

        # ----------------------------------
        # test express image predict
        # ----------------------------------
        if os.path.exists('vis_%s' % socket.gethostname()) == False: os.makedirs('vis_%s' % socket.gethostname())
        logger.info('start local kuaidi detect & predict test')

        LIST_test_ims = glob.glob('*.jpg')[:1]
        
        print '*' * 50
        print 'total ims', len(LIST_test_ims)
        for idx, fname in enumerate(LIST_test_ims[0: ]):
            TIME_start = time.time()
            data = {'fname': fname, 'img_str': fname}
            area_code = os.path.basename(fname).split('_')[-1].split('.')[0]
            res = self.extract_predict(data, True, True, False, area_code, False) # the last OCR is true, just return
            logger.info('finish %s test, cost %s' % (idx, time.time() - TIME_start))


    def extract_predict(self, data, FLAG_area=False, FLAG_vis=False, FLAG_no_parse=False, area_code='161', FLAG_ocr=False):
        """ extract image text and predict the content text
            1. detect text on image
            2. predict text
            3. recheck with deppon's standards
        """

        res = {
            'data': 0,
            'code': 102,
            'msg': ''
        }

        try:
            TIME_start = time.time()
            fname = data['fname']

            # check if img_str is base64 or url
            image = utils._data_convert_image(data['img_str'])
            image_vis = image.copy()
            logger.info('start task %s ### in area_code %s' % (fname, area_code))

            # ------------------------------------
            # 1. detect text
            # ------------------------------------
            # makesure detection data is base64 encode
            if isinstance(data['img_str'], (str, unicode)) and data['img_str'].startswith(('http:', 'https:')) == False and data['img_str'].endswith(('.jpg', '.png')) == False: pass
            else: data['img_str'] = utils._img_to_str_base64(image)

            print 'start detect!'
            c_det = zerorpc.Client()
            c_det.connect("tcp://%s" % RPC_menu['kuaidi_detect_PRC'])
            res_detect = c_det.detect(data, 0.8, False,)
            assert res_detect['msg'] == 'ok'
            c_det.close()
            print 'end detect'

            # ------------------------------------
            # 2. predict text
            # ------------------------------------
            DICT_bbox = dict()
            LIST_data_kuaidi = list()

            # ctpn 可视化出检测框结果
            # bboxdict = res_detect['data']['bbox_list']
            # for idx, inst in enumerate(bboxdict):
            #     x0, y0, x1, y1 = max(0, int(inst['bbox'][0]) - 5), max(0, int(inst['bbox'][1])), min(int(inst['bbox'][2]) + 5, image.shape[1]), min(int(inst['bbox'][3]) + 3, image.shape[0])
            #     im_crop = image[y0 : y1, x0 : x1, :]
            #     save_name = os.path.join('%s#%s#%d_%d_%d_%d.jpg' % (os.path.basename(fname), inst['score'], x0, y0, x1, y1))
            #     if 0 in im_crop.shape: continue
            #     LIST_data_kuaidi.append({'fname': save_name, 'img_str': utils._img_to_str_base64(im_crop)})
            #     DICT_bbox['%s_%s_%s_%s' % (x0, y0, x1, y1)] = inst
            #     cv2.rectangle(image_vis, (x0, y0), (x1, y1), (255, 0, 0), 1)

            # east 可视化检测框结果
            bbox_list = res_detect['data']
            for idx, inst in enumerate(bbox_list):
                x0, y0, x1, y1 = max(0, int(inst['x0']) - 5), max(0, int(inst['y0'])), min(int(inst['x2']) + 5, image.shape[1]), min(int(inst['y2']) + 3, image.shape[0])
                im_crop = image[y0: y1, x0: x1, :]
                save_name = os.path.join(
                    '%s#%s#%d_%d_%d_%d.jpg' % (os.path.basename(fname), inst['score'], x0, y0, x1, y1))
                if 0 in im_crop.shape: continue
                LIST_data_kuaidi.append({'fname': save_name, 'img_str': utils._img_to_str_base64(im_crop)})
                DICT_bbox['%s_%s_%s_%s' % (x0, y0, x1, y1)] = inst
                cv2.rectangle(image_vis, (x0, y0), (x1, y1), (255, 0, 0), 1)


            if len(LIST_data_kuaidi) == 0: return []
            print 'start ocr'
            c_pre = zerorpc.Client()
            c_pre.connect("tcp://%s" % RPC_menu['kuaidi_ocr_RPC'])
            pre_result = c_pre.predict_kuaidi(LIST_data_kuaidi, 'kuaidi')
            # 将gou转化为✓
            # for _ in pre_result['data'].keys():
            #     if pre_result['data'][_]['text'] == 'gou':
            #         pre_result['data'][_]['text'] = '✓'
            assert pre_result['msg'] == 'ok'
            c_pre.close()
            print 'end ocr'

            # ------------------------------------
            # 3. export to deppon final data
            # ------------------------------------
            # TODO use GBC_best to predict possible final output
            # ------------------------------------

            print '$' * 100
            if FLAG_ocr: return ''

            # 通过 predict string position 修正左右 padding，以检测 detect 是否正常
            for idx, name in enumerate(pre_result['data']):
                inst = pre_result['data'][name]
                im_name_rect = os.path.basename(inst['filename']).split('#')[-1].split('@')[0].split('.jpg')[0].split('_')
                x0, y0, x1, y1 = int(im_name_rect[0]), int(im_name_rect[1]), int(im_name_rect[2]), int(im_name_rect[3])
                pre_result['data'][name]['rect'] = [x0, y0, x1, y1]
                pre_result['data'][name]['filename'] = os.path.basename(inst['filename'])
                pre_result['data'][name]['detect'] = DICT_bbox['%s_%s_%s_%s' % (x0, y0, x1, y1)]

                # 更细粒度字符集切分与处理，根据字符左侧、右侧，更新 crop_list
                if inst['text'] != 'gou' and len(inst['pos']) >= 2:
                    if (inst['text'].isdigit() and len(inst['text']) > 1) or (inst['text'].isdigit() == False and len(inst['text']) > 3):
                        line_h = y1 - y0
                        clean_x0 = max(x0, x0 + inst['pos'][0] - int(0.75 * line_h)) if inst['pos'][0] >= 0.5 * line_h else x0
                        clean_x1 = min(x1, x0 + inst['pos'][-1] + int(0.75 * line_h) if ((x1 - inst['pos'][-1]) >= line_h) else x1)
                        cv2.rectangle(image_vis, (clean_x0, y0), (clean_x1, y1), (0, 255, 0), 2)

            # DICT_res, DICT_res_area, image, image_merge = utils.process(image, pre_result['data'], self.text_model, self.mapping_dict, True)
            LIST_out_text = utils.process_text_classify(image, pre_result['data'], self.text_model, self.mapping_dict, area_code, True)
            # print LIST_out_text

            # ------------------------------------
            # 4. check output format
            # ------------------------------------
            # 根据语言模型、识别概率、输出要求等，检测最后输出结果
            
            DICT_return = dict()
            position_feature = feature_unit.parse(LIST_out_text, image.shape[1], image.shape[0], area_code)
            if area_code == '161' or area_code == '162' or area_code == '161_1':
                y_pred_prob = self.GBC_best_161.predict_proba(position_feature)
            elif area_code == '163':
                y_pred_prob = self.GBC_best_163.predict_proba(position_feature)
            elif area_code == '164':
                y_pred_prob = self.GBC_best_164.predict_proba(position_feature)
            else:
                raise Exception("area-code must be one of '161','162','163','164', '161_1")

            for val_prob, text_inst, feature in zip(y_pred_prob, LIST_out_text, position_feature):
                pos_idx = np.argmax(val_prob)
                if area_code == '161' or area_code == '162' or area_code == '161_1':
                    cate = self.position_map[str(self.cls_dict_161[int(pos_idx)])]
                elif area_code == '163':
                    cate = self.position_map[str(self.cls_dict_163[int(pos_idx)])]
                else:
                    cate = self.position_map[str(self.cls_dict_164[int(pos_idx)])]

                if len(text_inst['text']) == 0: continue
                # print cate, text_inst['text'], feature

                # ------------------------------------
                # 直接判断省市县字段
                # if   text_inst['text'] in utils.LIST_area:     cate = 'rcDistName'
                # elif text_inst['text'] in utils.LIST_city:     cate = 'rcCityName'
                # elif text_inst['text'] in utils.LIST_province: cate = 'rcProvName'
                # elif text_inst['text'] in utils.LIST_street:   cate = 'street'

                # ------------------------------------
                # 直接判断是否为月结编码
                if area_code == '162':
                    if text_inst['text'].isdigit() and rule_check.is_cusNum(text_inst['text']):   cate = 'clientCode'

                # 按照 position = x + y 进行排序（不太准），后续针对163中的地址框又进行了排序
                xy_prefix = 0.1 * text_inst['area'][0] + text_inst['area'][1]
                
                # ------------------------------------
                # 将省市区街道都化为详细地址
                if DICT_return.has_key(cate) == False: DICT_return[cate] = dict()
                DICT_return[cate][xy_prefix] = {'text': text_inst['text'], 'text_inst': text_inst, 'cate': cate,
                                                'text_cate_prob': np.max(val_prob)}

                
            # 判断电话文本行中是否合理
            def is_like_dianhua(text):
                if len(text) < 6:
                    return False
                for ch in text:
                    if u'\u4e00' <= ch <= u'\u9fff':
                        return False
                return True
                
            # 强规则去掉163分类错误的电话（发件人电话在最上面、右下角的number）和地址（发件人的地址在最上面）
            if area_code == '163':
                # 判断电话是否分类正确
                if 'receiveCustomerPhone' in DICT_return:
                    # 若电话的框有两个及以上的时候
                    while len(DICT_return['receiveCustomerPhone']) > 1:
                        TUPLE_return = sorted(DICT_return['receiveCustomerPhone'].items())
                        # 若右下角有框框，则去掉
                        if TUPLE_return[-1][1]['text_inst']['area'][2] / image.shape[1] > 0.92 and TUPLE_return[-1][1]['text_inst']['area'][3] / image.shape[0] > 0.93:
                            if DICT_return.has_key('other') == False: DICT_return['other'] = dict()
                            DICT_return['other'][TUPLE_return[-1][0]] = DICT_return['receiveCustomerPhone'][TUPLE_return[-1][0]]
                            del DICT_return['receiveCustomerPhone'][TUPLE_return[-1][0]]
                            continue
                        # （先看字，再看位置）
                        # 若最下面的框中包含文字或长度小于6且(最上面的框或倒数第二个框like_dianhua)，则去掉
                        if not is_like_dianhua(TUPLE_return[-1][1]['text']) and (is_like_dianhua(TUPLE_return[0][1]['text']) or is_like_dianhua(TUPLE_return[-2][1]['text'])):
                            if DICT_return.has_key('other') == False: DICT_return['other'] = dict()
                            DICT_return['other'][TUPLE_return[-1][0]] = DICT_return['receiveCustomerPhone'][TUPLE_return[-1][0]]
                            del DICT_return['receiveCustomerPhone'][TUPLE_return[-1][0]]
                            continue
                        # 若最上面有框框，则去掉
                        if TUPLE_return[0][1]['text_inst']['area'][1]*1. / image.shape[0] < 0.05:
                            if DICT_return.has_key('other') == False: DICT_return['other'] = dict()
                            DICT_return['other'][TUPLE_return[0][0]] = DICT_return['receiveCustomerPhone'][TUPLE_return[0][0]]
                            del DICT_return['receiveCustomerPhone'][TUPLE_return[0][0]]
                            continue
                        # 若最上面的框中包含文字或长度小于6，则去掉
                        if not is_like_dianhua(TUPLE_return[0][1]['text']):
                            if DICT_return.has_key('other') == False: DICT_return['other'] = dict()
                            DICT_return['other'][TUPLE_return[0][0]] = DICT_return['receiveCustomerPhone'][TUPLE_return[0][0]]
                            del DICT_return['receiveCustomerPhone'][TUPLE_return[0][0]]
                        break
                # 判断地址是否分类正确
                if 'receiveCustomerAddress' in DICT_return:
                    TUPLE_return = sorted(DICT_return['receiveCustomerAddress'].items())
                    while len(DICT_return['receiveCustomerAddress']) > 1:
                        # 若右下角有框框，则去掉
                        if TUPLE_return[-1][1]['text_inst']['area'][2] / image.shape[1] > 0.92 and TUPLE_return[-1][1]['text_inst']['area'][3] / image.shape[0] > 0.93:
                            # print '右下角有框框'
                            if DICT_return.has_key('other') == False: DICT_return['other'] = dict()
                            DICT_return['other'][TUPLE_return[-1][0]] = DICT_return['receiveCustomerAddress'][TUPLE_return[-1][0]]
                            del DICT_return['receiveCustomerAddress'][TUPLE_return[-1][0]]
                            TUPLE_return = sorted(DICT_return['receiveCustomerAddress'].items())
                            continue
                        # 若最上面有框框且最下面的框框和最上面的框框差距大于1.8倍的框高，则去掉
                        if float(TUPLE_return[0][1]['text_inst']['area'][1]) / image.shape[0] < 0.2 and \
                        (TUPLE_return[-1][1]['text_inst']['area'][1] - TUPLE_return[0][1]['text_inst']['area'][1]) > \
                        1.8 * (TUPLE_return[0][1]['text_inst']['area'][3] - TUPLE_return[0][1]['text_inst']['area'][1]):
                            # print '最上面有框框'
                            if DICT_return.has_key('other') == False: DICT_return['other'] = dict()
                            DICT_return['other'][TUPLE_return[0][0]] = DICT_return['receiveCustomerAddress'][TUPLE_return[0][0]]
                            del DICT_return['receiveCustomerAddress'][TUPLE_return[0][0]]
                            TUPLE_return = sorted(DICT_return['receiveCustomerAddress'].items())
                            continue
                        # 若最下面的框框和倒数第二个框框的高度差1.8倍的框高，则去掉
                        if (TUPLE_return[-1][1]['text_inst']['area'][1] - TUPLE_return[-2][1]['text_inst']['area'][1]) > \
                        1.8 * (TUPLE_return[-1][1]['text_inst']['area'][3] - TUPLE_return[-1][1]['text_inst']['area'][1]):
                            if DICT_return.has_key('other') == False: DICT_return['other'] = dict()
                            DICT_return['other'][TUPLE_return[-1][0]] = DICT_return['receiveCustomerAddress'][TUPLE_return[-1][0]]
                            del DICT_return['receiveCustomerAddress'][TUPLE_return[-1][0]]
                            TUPLE_return = sorted(DICT_return['receiveCustomerAddress'].items())
                            continue

                        break
            # 强规则去掉161不是人名的字段
            if 'deliveryCustomerName' in DICT_return:
                TUPLE_return = sorted(DICT_return['deliveryCustomerName'].items())
                # print TUPLE_return
                # 若框框个数大于2的话
                while len(TUPLE_return) > 1:
                    for tup in TUPLE_return:
                        #干掉纯数字
                        # print tup[1]['text']
                        if tup[1]['text'].isdigit():
                            if DICT_return.has_key('other') == False: DICT_return['other'] = dict()
                            DICT_return['other'][tup[0]] = DICT_return['deliveryCustomerName'][tup[0]]
                            del DICT_return['deliveryCustomerName'][tup[0]]
                            continue
                        if (1.0 * tup[1]['text_inst']['area'][0] / image.shape[1] < 0.4 and tup[1]['text_cate_prob'] < 0.95) \
                        or (tup[1]['text_cate_prob'] < 0.9):
                            if DICT_return.has_key('other') == False: DICT_return['other'] = dict()
                            DICT_return['other'][tup[0]] = DICT_return['deliveryCustomerName'][tup[0]]
                            del DICT_return['deliveryCustomerName'][tup[0]]
                            continue
                    break

            # 选择寄件人电话中分类得分最高的
            if 'deliveryCustomerPhone' in DICT_return:
                TUPLE_return = sorted(DICT_return['deliveryCustomerPhone'].items())
                # print TUPLE_return
                # 若框框个数大于2的话
                while len(TUPLE_return) > 1:
                    if TUPLE_return[0][1]['text_cate_prob'] < TUPLE_return[1][1]['text_cate_prob']:
                        if DICT_return.has_key('other') == False: DICT_return['other'] = dict()
                        DICT_return['other'][TUPLE_return[0][0]] = DICT_return['deliveryCustomerPhone'][TUPLE_return[0][0]]
                        del DICT_return['deliveryCustomerPhone'][TUPLE_return[0][0]]
                    else:
                        if DICT_return.has_key('other') == False: DICT_return['other'] = dict()
                        DICT_return['other'][TUPLE_return[1][0]] = DICT_return['deliveryCustomerPhone'][TUPLE_return[1][0]]
                        del DICT_return['deliveryCustomerPhone'][TUPLE_return[1][0]]
                    TUPLE_return = sorted(DICT_return['deliveryCustomerPhone'].items())

            # 161的强规则
            if area_code == '161':
                # 如果没有电话，将月结编码分给电话
                if 'deliveryCustomerPhone' in DICT_return:
                    pass
                else:
                    if 'clientCode' in DICT_return:
                        DICT_return['deliveryCustomerPhone'] = DICT_return['clientCode']
                    else:
                        pass

            # 比较两个框的前后关系,冒泡排序算法
            def compare_address(param1, param2):
                rec1 = param1[1]['text_inst']['area']
                rec2 = param2[1]['text_inst']['area']
                end_y = max(rec1[3], rec2[3])
                start_y = min(rec1[1], rec2[1])
                overlap_height = (rec1[3] - rec1[1]) + (rec2[3] - rec2[1]) - (end_y - start_y)
                sum_height = (rec1[3] - rec1[1]) + (rec2[3] - rec2[1])
                if overlap_height <= 0:
                    overlap_y = 0
                else:
                    overlap_y = overlap_height * 1. / (end_y - start_y)

                #
                ifAscend = 1
                if overlap_y > 0.5:
                    center_x1 = (rec1[2] + rec1[0]) / 2
                    center_x2 = (rec2[2] + rec2[0]) / 2
                    if center_x2 > center_x1:
                        ifAscend = 1
                    else:
                        ifAscend = 0
                else:
                    center_y1 = (rec1[1] + rec1[3]) / 2
                    center_y2 = (rec2[1] + rec2[3]) / 2
                    if center_y2 > center_y1:
                        ifAscend = 1
                    else:
                        ifAscend = 0

                return ifAscend

            # 重新调整xy_prefix的值，以提高地址拼接的准确率（未测试）
            # 163排序地址框
            if area_code == '163':
                if 'receiveCustomerAddress' in DICT_return:
                    list_text = list(DICT_return['receiveCustomerAddress'].items())
                    for i in range(0, len(list_text)-1):
                        for j in range(i+1, len(list_text)):
                            if compare_address(list_text[i], list_text[j]):
                                continue
                            else:
                                tmp = list_text[i]
                                list_text[i] = list_text[j]
                                list_text[j] = tmp
                    DICT_return['receiveCustomerAddress'] = dict()
                    for idx, content in enumerate(list_text):
                        DICT_return['receiveCustomerAddress'][idx] = content[1]

            
            # ------------------------------------
            # 5. mesh up final output
            # ------------------------------------
            # 如果为电话号码 or 客户编码，纯数字，需要 recheck 模型
            # 按照，161 - 164，限制相关输出 ~

            def area_check(inst, DICT_return, return_data):
                """ parse return_data to fullfill the output value 
                    return_data: program final output. return_data has 161 - 164 category
                """

                for name in return_data:
                    if DICT_return.has_key(name):
                        
                        # 为 return_data 每一字段 name 计算赋值
                        text = ''
                        LIST_text_inst = list()
                        LIST_text_min_prob = list()
                        LIST_text_min_prob_char = list()
                        LIST_text_cate_prob = list()

                        # 考虑同一字段可能会有多条记录，例如分类出2个电话，将多条记录拼接起来
                        for key_name in sorted(DICT_return[name].keys()):
                            text_line           = DICT_return[name][key_name]['text']
                            text_area           = DICT_return[name][key_name]['text_inst']['area']
                            text_ocr_prob       = DICT_return[name][key_name]['text_inst']['ocr_prob']
                            text_cate_prob      = DICT_return[name][key_name]['text_cate_prob']          # position classifiy prob value
                            
                            # consider has more than 1 phone, 15201119999 15201119999
                            if 'Phone' in name: text += text_line + ' '
                            else: text += text_line

                            LIST_text_inst.append({'text': text_line, 
                                                   'text_area': text_area, 
                                                   'text_ocr_prob': text_ocr_prob,
                                                   'text_cate_prob': text_cate_prob})
                            
                            LIST_text_min_prob.append(np.min(text_ocr_prob))
                            LIST_text_min_prob_char.append(list(text_line)[np.argmin(text_ocr_prob)])
                            LIST_text_cate_prob.append(text_cate_prob)

                        # ------------------------------------
                        # machine check rules
                        # 从 OCR 识别、字段规则、字段位置分类，三个维度判断
                        text = text.strip()
                        FLAG_machine    = True if np.min(LIST_text_cate_prob) >= 0.95 else {'cate_prob': np.min(LIST_text_cate_prob), 'value': False}
                        FLAG_ocr_pass   = True if np.min(LIST_text_min_prob) >= 0.85 else {'text_min_prob': np.min(LIST_text_min_prob), 'text': LIST_text_min_prob_char[np.argmin(LIST_text_min_prob)], 'value': False}
                        print name, text, '****'

                        # 如果是电话，则考虑有两种电话类型，空格类型与 / 类型
                        FLAG_rule_pass = True
                        if name in ['deliveryCustomerPhone', 'receiveCustomerPhone']:
                            if text.strip() == '':
                                FLAG_rule_pass = {'msg': 'phone is empty check failed', 'value': False}

                            # 确保子电话 (sub phone) 也为正常，也可能有月结编码
                            sep_str = ' '
                            if '/' in text:
                                sep_str = '/'

                            for sub_text in text.split(sep_str):
                                if rule_check.is_phoneNum(sub_text) == False:
                                    FLAG_rule_pass = {'msg': 'phone %s check failed' % sub_text, 'value': False}
                                    break

                        # # 如有省份，不在列表即为出错,事实上不可能有省份
                        # elif name == 'rcProvName':
                        #     FLAG_rule_pass = True if text in utils.LIST_province else {'msg': 'not prov %s' % text, 'value': False}

                        elif name == 'clientCode':
                            FLAG_rule_pass = True if rule_check.is_cusNum(text) else {'msg': 'not clientCode %s' % text,
                                                                                       'value': False}

                        return_data[name] = {'FLAG_machine_pass': FLAG_machine, 'FLAG_rule_pass': FLAG_rule_pass, 'FLAG_ocr_pass': FLAG_ocr_pass,
                                              'text': text, 'text_list': LIST_text_inst}

                # ------------------------------------
                # 根据地址，提取解析出省、市、县位置
                # Add by Guxiang'suggestion，将省、市、县再合并到地址中处理
                # if return_data.has_key('receiveCustomerAddress'):
                #     # TODO 以后变成直接程序调用，不用本地文件
                #     # if return_data['receiveCustomerAddress'] == -1:
                #         # merge_text = '%s%s%s' % (return_data['rcProvName']['text'], return_data['rcCityName']['text'], return_data['rcDistName']['text'])
                #     # else:
                #         # merge_text = '%s%s%s%s' % (return_data['rcProvName']['text'], return_data['rcCityName']['text'], return_data['rcDistName']['text'], return_data['receiveCustomerAddress']['text'])
                #
                #     merge_text = return_data['receiveCustomerAddress']['text']
                #     print merge_text
                #     # print return_data['receiveCustomerAddress']['text']
                #     with open('t.txt', 'w') as o: print >> o, ' '.join(list(merge_text)).encode('utf-8')
                #     if len(merge_text.strip()) != 0:
                #         score, network_result = translate.network_parse('t.txt', 'o.txt')
                #         print score, network_result
                #
                #         if abs(score) >= 1:  # 修改过
                #             FLAG_machine = {'msg': 'mnt parse %s' % network_result, 'score': float(score), 'value': False}
                #             if return_data['receiveCustomerAddress'] != -1:
                #                 return_data['receiveCustomerAddress']['AddrRes'] = FLAG_machine
                #         else:
                #             return_data['receiveCustomerAddress']['AddrRes'] = {'msg': 'mnt parse %s' % network_result, 'score': float(score), 'value': True}
                #             # 如果概率靠谱，需将省市县解析出来
                #             detailAddress = ''
                #             split_string = network_result.split()
                #             print split_string
                #             loc_mapping = {0: 'rcProvName', 1: 'rcCityName', 2: 'rcDistName', 3: 'rcTownName'}
                #             for i, split_text in enumerate(split_string):
                #                 # 去掉省市区街道前缀
                #                 if len(split_text) > 1:
                #                     return_data[loc_mapping[i]]['text'] = split_text
                #                 elif len(split_text) == 1:
                #                     detailAddress += split_text
                #             return_data['receiveCustomerAddress']['text'] = detailAddress

                return return_data


            assert area_code in ['161', '161_1', '162', '163', '164']
            # 161: deliveryCustomerPhone, deliveryCustomerName, notificationMode
            # 162: clientCode
            # 163: receiveCustomerPhone, receiveCustomerName, rcProvName, rcCityName, rcDistName, receiveCustomerAddress, goodsName
            # 164: insuranceAmount

            if area_code == '161':  # 非常可能有月结编码
                return_data = {'deliveryCustomerPhone': -1, 'deliveryCustomerName': -1, 'notificationMode': -1}
                return_data = area_check(inst, DICT_return, return_data)

            elif area_code == '161_1':
                return_data = {'deliveryCustomerPhone': -1, 'deliveryCustomerName': -1, 'notificationMode': -1, 'dcProvName': -1, 'dcCityName': -1, 'dcDistName': -1, 'deliveryCustomerAddress': -1}
                return_data = area_check(inst, DICT_return, return_data)

                # final check for 省、市、区
                if return_data['dcProvName'] != -1:
                    if return_data['dcProvName']['text'] not in utils.LIST_province or len(return_data['dcProvName']['text']) < 2:
                        return_data['dcProvName']['FLAG_rule_pass'] = {'value': False, 'msg': '%s not in Dict' % return_data['dcProvName']['text']}
                if return_data['dcCityName'] != -1:
                    if return_data['dcCityName']['text'] not in utils.LIST_city or len(return_data['dcCityName']['text']) < 2:
                        return_data['dcCityName']['FLAG_rule_pass'] = {'value': False, 'msg': '%s not in Dict' % return_data['dcCityName']['text']}
                if return_data['dcDistName'] != -1:
                    if return_data['dcDistName']['text'] not in utils.LIST_area or len(return_data['dcDistName']['text']) < 2:
                        return_data['dcDistName']['FLAG_rule_pass'] = {'value': False, 'msg': '%s not in Dict' % return_data['dcDistName']['text']}
                # 是否满足省市区规则
                # if return_data['deliveryCustomerAddress'] != -1:
                #     return_data['deliveryCustomerAddress']['is_valid_pca'] = True if rule_check.is_valid_pca(return_data['dcProvName']['text'], return_data['dcCityName']['text'], return_data['dcDistName']['text']) else False

            elif area_code == '162':
                return_data = {'clientCode': -1}
                print DICT_return.keys(), DICT_return.keys() == return_data.keys()
                return_data = area_check(inst, DICT_return, return_data)

            elif area_code == '163':
                return_data = {'receiveCustomerPhone': -1, 'receiveCustomerName': -1, 'rcProvName': -1, 'rcCityName': -1, 'rcDistName': -1, 'rcTownName': -1, 'receiveCustomerAddress': -1, 'goodsName': -1}
                return_data = area_check(inst, DICT_return, return_data)

                # final check for 省、市、区
                if return_data['rcProvName'] != -1:
                    if return_data['rcProvName']['text'] not in utils.LIST_province or len(return_data['rcProvName']['text']) < 2:
                        return_data['rcProvName']['FLAG_rule_pass'] = {'value': False, 'msg': '%s not in Dict' % return_data['rcProvName']['text']}
                if return_data['rcCityName'] != -1:
                    if return_data['rcCityName']['text'] not in utils.LIST_city or len(return_data['rcCityName']['text']) < 2:
                        return_data['rcCityName']['FLAG_rule_pass'] = {'value': False, 'msg': '%s not in Dict' % return_data['rcCityName']['text']}
                if return_data['rcDistName'] != -1:
                    if return_data['rcDistName']['text'] not in utils.LIST_area or len(return_data['rcDistName']['text']) < 2:
                        return_data['rcDistName']['FLAG_rule_pass'] = {'value': False, 'msg': '%s not in Dict' % return_data['rcDistName']['text']}
                # 是否满足省市区规则
                # if return_data['receiveCustomerAddress'] != -1:
                #     return_data['receiveCustomerAddress']['is_valid_pca'] = True if rule_check.is_valid_pca(return_data['rcProvName']['text'], return_data['rcCityName']['text'], return_data['rcDistName']['text']) else False

            elif area_code == '164':
                return_data = {'insuranceAmount': -1, 'sameDayRefund': -1, 'threeDaysRefund': -1, 'codAmount': -1, 'accountName': -1,
                'collectionAccount': -1, 'packageFeeCanvas': -1, 'deliveryInboundFee': -1, 'original': -1, 'fax': -1, 'human_check': False}
                return_data = area_check(inst, DICT_return, return_data)

                # 加一个补丁，对于164，目前可能将关心的字段错误分成了other，所以设置一个补救措施，对于位置在左半边文本框，我们将之分类为maybeCare类，给前端提供参考。
                # DICT_return['maybeCare'] = dict()
                dict_others = DICT_return['other']
                for one_key in dict_others.keys():
                    height, width = image.shape[0:2]
                    box_area = dict_others[one_key]['text_inst']['area']
                    box_area = [int(_) for _ in box_area]
                    box_y = (box_area[1] + box_area[3])/2
                    box_x = (box_area[0] + box_area[2])/2
                    box_height = abs(box_area[3] - box_area[1])
                    if box_x < width*0.4 and box_y>0.1*height and box_height< 0.25*height:
                        return_data['human_check'] = True
                        break



            logger.info('start finish %s. cost time %s' % (fname, time.time() - TIME_start))
            logger.info('start finish %s. %s' % (fname, json.dumps(return_data)))
            # with open('vis_%s/%s.json' % (socket.gethostname(), os.path.basename(fname)), 'w') as o:
            #     print >> o, json.dumps(return_data)

            res['msg'] = 'ok'
            res['code'] = 0
            res['data'] = json.dumps(return_data)
            res['detect'] = json.dumps(LIST_out_text)
            res['detect_cate'] = json.dumps(DICT_return)

            # ------------------------------------
            # 3. update predict result
            # ------------------------------------

            if FLAG_vis:
                if os.path.exists('vis_%s' % socket.gethostname()) == False: os.makedirs('vis_%s' % socket.gethostname())
                cv2.imwrite('vis_%s/det.%s' % (socket.gethostname(), os.path.basename(fname)), image_vis, [int(cv2.IMWRITE_JPEG_QUALITY), 20])

            if FLAG_vis:
                # vis image in HTML
                LIST_vis_data = list()
                for idx, name in enumerate(pre_result['data']):
                    inst = pre_result['data'][name]
                    vis_inst = {'text': inst['text'], 'prob': inst['prob'], 'pos': [inst['rect'][0], 0, 0, inst['rect'][1]], 'q_id': str(idx)}
                    LIST_vis_data.append(vis_inst)

                HTML = open('word-prob-vis-v1.html', 'r').read()
                HTML = HTML.replace('var json = ###', 'var json = %s' % json.dumps(LIST_vis_data))
                HTML = HTML.replace('<img src="###">', '<img src="det.%s">' % os.path.basename(fname))
                HTML = HTML.replace('var width = ###', 'var width = %s' % image.shape[1])
                HTML = HTML.replace('var height = ###', 'var height = %s' % image.shape[0])
                # with open('vis_%s/%s.html' % (socket.gethostname(), os.path.basename(fname)), 'w') as o: print >> o, HTML

            # ------------------------------------
            # 如不需解析成德邦格式，直接返回
            if FLAG_no_parse == True:
                res['data'] = json.dumps(pre_result)
                return res

            # if FLAG_vis:
                # with open('vis_%s/%s.json' % (socket.gethostname(), os.path.basename(fname)), 'w') as o: print >> o, json.dumps(LIST_out_text)
                # cv2.imwrite('vis_%s/vis.merge.' % socket.gethostname() + os.path.basename(fname), image_merge)

        except Exception, e:
            res['msg'] = 'error'
            res['code'] = 103
            logger.info('error task %s ### in area_code %s' % (fname, area_code))
            logger.error(str(e))
            logger.error(str(traceback.print_exc()))

        return res

    def parse_address(self, address_text):
        """
        解析一个拼接起来的地址，得到其省事县街道详细地址，若解析模型自信程度太低，则没有解析结果。
        :param address_text: 传递过来的拼接起来的地址，待解析
        :return:
        """
        import addr_alignment
        with open('t.txt', 'w') as o:
            print >> o, ' '.join(list(address_text)).encode('utf-8')
        return_dict = {'human_check': False, 'provName': u'', 'cityName': u'', 'distName': u'', 'townName': u'', 'detailAddress': u''}
        if len(address_text.strip()) != 0:
            score, network_result = translate.network_parse('t.txt', 'o.txt')
            list_address = network_result.split(' ')
            print score, network_result

            # 调低阈值
            if abs(score) >= 1:
                return_dict['human_check'] = True
                print('score low, failed')
                print(score)
            else:
                # 如果概率靠谱，需将省市县解析出来
                split_string = network_result.split()
                loc_mapping = {0: 'provName', 1: 'cityName', 2: 'distName', 3: 'townName'}

                # 通过地址alignment获得详细地址
                addr2 = ''.join(list_address)
                addr1 = address_text.strip()
                addr2_list = list_address
                if not len(addr2_list) in [2, 3, 4]:
                    print('神经网络地址解析结果应该有2/3/4级, 该字段解析结果异常：', addr1)
                if_pca, if_correct_jiedao = rule_check.check_net_parse_result(addr2_list)
                if if_pca:
                    if not if_correct_jiedao:
                        addr2_list = addr2_list[0: 3]
                else:
                    print('地址解析结果不符合pca，不需要在进行alignment')
                    return_dict['human_check'] = True
                    return return_dict

                detail_address, remain_addr2_list, human_check = addr_alignment.address_match(addr1, addr2_list)
                for i, jiexi_name in enumerate(remain_addr2_list):
                    return_dict[loc_mapping[i]] = jiexi_name
                return_dict['detailAddress'] = detail_address
                if detail_address != '':
                    print('地址alignment得到的详细地址:')
                    print(detail_address)
                if human_check == 1:
                    return_dict['human_check'] = human_check
        return return_dict

    def parse_address_bak(self, address_text):
        """ parse address code
        """
        with open('t.txt', 'w') as o: print >> o, ' '.join(list(address_text)).encode('utf-8')
        print address_text
        score, network_result = translate.network_parse('t.txt', 'o.txt')
        print score, network_result
        return_data = {'rcProvName': {'text': ''}, 'rcCityName': {'text': ''}, 'rcDistName': {'text': ''}}

        if abs(score) >= 0.015: 
            return network_result, score
        else:
            # 如果概率靠谱，需将省市县解析出来
            split_string = network_result.split()
            loc_mapping = {0: 'rcProvName', 1: 'rcCityName', 2: 'rcDistName', 3: 'rcTownName'}
            for i, split_text in enumerate(split_string):
                return_data[loc_mapping[i]]['text'] = split_text
        return return_data, score


    def check_params(self, data):
        import addr_alignment
        """ check params value by rules, 检查最后输出，保障输出结果满足相关规则
            {
            "result": {
                "receiveCustomerPhone": 18811,
                "receiveCustomerName": "王云建",
                "rcProvName": null,
                "rcCityName": null,
                "rcDistName": null,
                "receiveCustomerAddress": "北京平谷区滨河街道平谷区府前西街15号",
                "goodsName": "衣服"
            },
            "cpId": "163"
            }
        """

        logger.info('start check %s' % (data))
        area_code = data['cpId']

        if area_code == '161':
            data['msg'] = {'deliveryCustomerPhone': -1, 'deliveryCustomerName': -1, 'notificationMode': -1}

            data['msg']['deliveryCustomerPhone'] = {'value': False}
            if data['result']['deliveryCustomerPhone']['text'].strip() == '':
                data['msg']['deliveryCustomerPhone'] = {'value': False, 'msg': 'error number empty'} 
                
            # 姓名为空不给过
            if data['result']['deliveryCustomerName']['text'].strip() == '':
                data['msg']['deliveryCustomerName'] = {'value': False, 'msg': 'error name empty'} 

            for sub_text in data['result']['deliveryCustomerPhone']['text'].split():
                if rule_check.is_phoneNum(sub_text) == False:
                    data['msg']['deliveryCustomerPhone'] = {'value': False, 'msg': 'error number %s' % sub_text} 
                    break
                data['msg']['deliveryCustomerPhone'] = {'value': True}




        elif area_code == '161_1':
            data['msg'] = {'deliveryCustomerPhone': -1, 'deliveryCustomerName': -1, 'dcProvName': -1, 'dcCityName': -1, 'dcDistName': -1, 'deliveryCustomerAddress': -1, 'notificationMode': -1}

            data['msg']['deliveryCustomerPhone'] = {'value': False}
            if data['result']['deliveryCustomerPhone']['text'].strip() == '':
                data['msg']['deliveryCustomerPhone'] = {'value': False, 'msg': 'error number empty'} 
                
            # 姓名为空不给过
            if data['result']['deliveryCustomerName']['text'].strip() == '':
                data['msg']['deliveryCustomerName'] = {'value': False, 'msg': 'error name empty'} 

            for sub_text in data['result']['deliveryCustomerPhone']['text'].split():
                if rule_check.is_phoneNum(sub_text) == False:
                    data['msg']['deliveryCustomerPhone'] = {'value': False, 'msg': 'error number %s' % sub_text} 
                    break
                data['msg']['deliveryCustomerPhone'] = {'value': True}


            merge_text = '%s%s%s%s' % (data['result']['dcProvName']['text'], data['result']['dcCityName']['text'], data['result']['dcDistName']['text'], data['result']['deliveryCustomerAddress']['text'])
            addr_parse_result = self.parse_address(merge_text)
            if addr_parse_result['human_check']:
                data['msg']['human_check'] = True
                return data
            else:
                data['result']['dcProvName']['text'] = addr_parse_result['provName']
                data['result']['dcCityName']['text'] = addr_parse_result['cityName']
                data['result']['dcDistName']['text'] = addr_parse_result['distName']
                data['result']['dcTownName']['text'] = addr_parse_result['townName']
                data['result']['deliveryCustomerAddress']['text'] = addr_parse_result['detailAddress']
                if data['result']['deliveryCustomerAddress']['text'].strip() == '':
                    data['msg']['deliveryCustomerAddress'] = {'value': False, 'msg': 'empty deliveryCustomerAddress'}
            # with open('t.txt', 'w') as o: print >> o, ' '.join(list(merge_text)).encode('utf-8')
            # if len(merge_text.strip()) != 0:
            #     score, network_result = translate.network_parse('t.txt', 'o.txt')
            #     list_address = network_result.split(' ')
            #     # detail_address = ''.join(list_address[3:])
            #     # if len(detail_address)>len(merge_text):
            #     #     data['msg']['human_check'] = True
            #     #     return data
            #
            #     print score, network_result
            #
            #     # 调低阈值
            #     if abs(score) >= 1:
            #         data['msg']['human_check'] = True
            #         print('score low, failed')
            #         print(score)
            #         return data
            #     else:
            #         # 如果概率靠谱，需将省市县解析出来
            #         split_string = network_result.split()
            #         loc_mapping = {0: 'dcProvName', 1: 'dcCityName', 2: 'dcDistName', 3: 'dcTownName'}
            #         detailAddress = ''
            #         for i, split_text in enumerate(split_string):
            #             # 去掉省市区街道前缀
            #             if len(split_text) > 1:
            #                 data['result'][loc_mapping[i]]['text'] = split_text
            #             elif len(split_text) == 1:
            #                 detailAddress += split_text
            #         print('detailAddress:')
            #         print(detailAddress)
            #         data['result']['receiveCustomerAddress']['text'] = detailAddress
            #         # 通过地址alignment获得详细地址
            #         addr2 = ''.join(list_address)
            #         addr1 = merge_text.strip()
            #         detail_address = addr_alignment.get_detail_add(addr1, addr2)
            #         data['result']['receiveCustomerAddress']['text'] = detail_address
            #         print('detail_address:')
            #         print(detail_address)

            # final check for 省、市、区
            data['msg']['dcProvName'] = {'value': True} if data['result']['dcProvName']['text'] in utils.LIST_province and len(data['result']['dcProvName']['text']) >= 2 else {'value': False, 'msg': 'error dcProvName %s' % data['result']['dcProvName']['text']} 
            data['msg']['dcCityName'] = {'value': True} if data['result']['dcCityName']['text'] in utils.LIST_city and len(data['result']['dcCityName']['text']) >= 2 else {'value': False, 'msg': 'error dcCityName %s' % data['result']['dcCityName']['text']} 
            data['msg']['dcDistName'] = {'value': True} if data['result']['dcDistName']['text'] in utils.LIST_area and len(data['result']['dcDistName']['text']) >= 2 else {'value': False, 'msg': 'error dcDistName %s' % data['result']['dcDistName']['text']} 

            # 验证省、市、区满足物理规则
            # data['msg']['is_valid_pca'] = True if rule_check.is_valid_pca(data['result']['dcProvName']['text'], data['result']['dcCityName']['text'], data['result']['dcDistName']['text']) else False
            # if data['msg']['is_valid_pca'] == False:
            #     data['msg']['human_check'] = True


        elif area_code == '162':
            data['msg'] = {'clientCode': -1}
            data['msg']['clientCode'] = {'value': True} if rule_check.is_cusNum(data['result']['clientCode']['text']) else {'value': False, 'msg': 'error clientCode %s' % data['result']['clientCode']['text']} 


        elif area_code == '163':
            data['msg'] = {'receiveCustomerPhone': -1, 'receiveCustomerName': -1, 'rcProvName': -1, 'rcCityName': -1, 'rcDistName': -1, 'receiveCustomerAddress': -1, 'goodsName': -1}
            data['msg']['receiveCustomerPhone'] = {'value': False}
            if data['result']['receiveCustomerPhone']['text'].strip() == '':
                data['msg']['receiveCustomerPhone'] = {'value': False, 'msg': 'error number empty'} 

            # 姓名为空不给过
            if data['result']['receiveCustomerName']['text'].strip() == '':
                data['msg']['receiveCustomerName'] = {'value': False, 'msg': 'error name empty'} 

            for sub_text in data['result']['receiveCustomerPhone']['text'].split():
                data['msg']['receiveCustomerPhone'] = {'value': True} if rule_check.is_phoneNum(sub_text) else {'value': False, 'msg': 'error number %s' % sub_text} 

            merge_text = '%s%s%s%s' % (data['result']['rcProvName']['text'], data['result']['rcCityName']['text'], data['result']['rcDistName']['text'], data['result']['receiveCustomerAddress']['text'])
            addr_parse_result = self.parse_address(merge_text)
            if addr_parse_result['human_check']:
                data['msg']['human_check'] = True
                return data
            else:
                data['result']['rcProvName']['text'] = addr_parse_result['provName']
                data['result']['rcCityName']['text'] = addr_parse_result['cityName']
                data['result']['rcDistName']['text'] = addr_parse_result['distName']
                data['result']['rcTownName']['text'] = addr_parse_result['townName']
                data['result']['receiveCustomerAddress']['text'] = addr_parse_result['detailAddress']
                if data['result']['receiveCustomerAddress']['text'].strip() == '':
                    data['msg']['receiveCustomerAddress'] = {'value': False, 'msg': 'empty receiveCustomerAddress'}
            # with open('t.txt', 'w') as o: print >> o, ' '.join(list(merge_text)).encode('utf-8')
            # if len(merge_text.strip()) != 0:
            #     score, network_result = translate.network_parse('t.txt', 'o.txt')
            #     list_address = network_result.split(' ')
            #     print score, network_result
            #
            #     if abs(score) >= 1:#修改过
            #         data['msg']['human_check'] = True
            #         print('score low, failed')
            #         print(score)
            #         return data
            #     else:
            #         # 如果概率靠谱，需将省市县解析出来
            #         # print 'jiexichenggong!!!!'
            #         detailAddress = ''
            #         split_string = network_result.split()
            #         loc_mapping = {0: 'rcProvName', 1: 'rcCityName', 2: 'rcDistName', 3: 'rcTownName'}
            #         for i, split_text in enumerate(split_string):
            #             #去掉省市区街道前缀
            #             if len(split_text) > 1:
            #                 data['result'][loc_mapping[i]]['text'] = split_text
            #             elif len(split_text) == 1:
            #                 detailAddress += split_text
            #         print('detailAddress:')
            #         print(detailAddress)
            #         data['result']['receiveCustomerAddress']['text'] = detailAddress
            #         # 通过地址alignment获得详细地址
            #         addr2 = ''.join(list_address)
            #         addr1 = merge_text.strip()
            #         detail_address = addr_alignment.get_detail_add(addr1, addr2)
            #         print('detail_address:')
            #         print(detail_address)
            #         data['result']['receiveCustomerAddress']['text'] = detail_address

            # final check for 省、市、区
            data['msg']['rcProvName'] = {'value': True} if data['result']['rcProvName']['text'] in utils.LIST_province and len(data['result']['rcProvName']['text']) >= 2 else {'value': False, 'msg': 'error rcProvName %s' % data['result']['rcProvName']['text']} 
            data['msg']['rcCityName'] = {'value': True} if data['result']['rcCityName']['text'] in utils.LIST_city and len(data['result']['rcCityName']['text']) >= 2 else {'value': False, 'msg': 'error rcCityName %s' % data['result']['rcCityName']['text']} 
            data['msg']['rcDistName'] = {'value': True} if data['result']['rcDistName']['text'] in utils.LIST_area and len(data['result']['rcDistName']['text']) >= 2 or data['result']['rcDistName']['text']==u'' else {'value': False, 'msg': 'error rcDistName %s' % data['result']['rcDistName']['text']}

            # 验证省、市、区满足物理规则
            # data['msg']['is_valid_pca'] = True if rule_check.is_valid_pca(data['result']['rcProvName']['text'], data['result']['rcCityName']['text'], data['result']['rcDistName']['text']) else False
            # if data['msg']['is_valid_pca'] == False:
            #     data['msg']['human_check'] = True
            # print '163jieshu!!!'

        elif area_code == '164':
            data['msg'] = {'insuranceAmount': -1}
            data['msg']['insuranceAmount'] = {'value': True} if data['result']['insuranceAmount']['text'].isdigit() else {'value': False, 'msg': 'error insuranceAmount %s' % data['result']['insuranceAmount']['text']} 


        logger.info('check result %s' % (data))
        return data


    def test_extract_predict(self, data):
        if 1:
            fname = data['fname']
            area_code = '161'
            # check if img_str is base64 or url
            image = utils._data_convert_image(data['img_str'])
            image_vis = image.copy()
            logger.info('start task %s ### in area_code %s' % (fname, area_code))

            # ------------------------------------
            # 1. detect text
            # ------------------------------------
            # makesure detection data is base64 encode
            if isinstance(data['img_str'], (str, unicode)) and data['img_str'].startswith(('http:', 'https:')) == False and data['img_str'].endswith(('.jpg', '.png')) == False: pass
            else: data['img_str'] = utils._img_to_str_base64(image)

            c_det = zerorpc.Client()
            c_det.connect("tcp://%s" % RPC_menu['kuaidi_detect_PRC'])
            res_detect = c_det.detect(data, 0.9, False)
            assert res_detect['msg'] == 'ok'
            c_det.close()

            # ------------------------------------
            # 2. predict text
            # ------------------------------------
            DICT_bbox = dict()
            LIST_data_kuaidi = list()

            # 目前测试，EAST 检测出效果最好
            bboxdict = res_detect['data']
            for idx, inst in enumerate(bboxdict):
                # 确保 coor 满足切图图像需求
                x0, y0, x1, y1 = max(0, int(inst['x0']) - 5), max(int(inst['y0']) - 2, 0), min(int(inst['x2']) + 5, image.shape[1]), min(int(inst['y2']) + 2, image.shape[0])
                im_crop = image[y0 : y1, x0 : x1, :]

                # 保留原始 coor 信息与切图
                x0, y0, x1, y1 = int(inst['x0']), int(inst['y0']), int(inst['x2']), int(inst['y2'])
                save_name = os.path.join('%s#%s#%d_%d_%d_%d.jpg' % (os.path.basename(fname), inst['score'], x0, y0, x1, y1))
                if 0 in im_crop.shape: continue
                LIST_data_kuaidi.append({'fname': save_name, 'img_str': utils._img_to_str_base64(im_crop)})
                DICT_bbox['%s_%s_%s_%s' % (x0, y0, x1, y1)] = inst
                cv2.rectangle(image_vis, (x0, y0), (x1, y1), (255, 0, 0), 2)

            if len(LIST_data_kuaidi) == 0: return []
            c_pre = zerorpc.Client()
            c_pre.connect("tcp://%s" % RPC_menu['kuaidi_ocr_RPC'])
            pre_result = c_pre.predict_kuaidi(LIST_data_kuaidi, 'kuaidi')
            assert pre_result['msg'] == 'ok'
            c_pre.close()

            # ------------------------------------
            # 3. export to deppon final data
            # ------------------------------------
            # TODO use GBC_best to predict possible final output
            # ------------------------------------

            # ------------------------------------
            # local low probility text linefilename
            # ------------------------------------
            print '$' * 100

            # 通过 predict string position 修正左右 padding，以检测 detect 是否正常
            for idx, name in enumerate(pre_result['data']):
                inst = pre_result['data'][name]
                im_name_rect = os.path.basename(inst['filename']).split('#')[-1].split('@')[0].split('.jpg')[0].split('_')
                x0, y0, x1, y1 = int(im_name_rect[0]), int(im_name_rect[1]), int(im_name_rect[2]), int(im_name_rect[3])
                pre_result['data'][name]['rect'] = [x0, y0, x1, y1]
                pre_result['data'][name]['filename'] = os.path.basename(inst['filename'])
                pre_result['data'][name]['detect'] = DICT_bbox['%s_%s_%s_%s' % (x0, y0, x1, y1)]
                print inst['text']

                x0 -= 20
                x1 -= 20

                # 更细粒度字符集切分与处理，根据字符左侧、右侧，更新 crop_list
                if inst['text'] != 'gou' and len(inst['pos']) >= 1:
                    if (inst['text'].isdigit() and len(inst['text']) > 1) or (inst['text'].isdigit() == False and len(inst['text']) >= 1):
                        print inst['text'], '***'
                        line_h = y1 - y0
                        # 'Yes' if fruit == 'Apple' else 'No'
                        clean_x0 = max(x0, x0 + inst['pos'][0] - int(0.75 * line_h)) if inst['pos'][0] >= 0.5 * line_h else x0
                        # clean_x1 = min(x1, x0 + inst['pos'][-1] + int(4.0 * line_h) if ((x1 - inst['pos'][-1]) >= line_h) else x1)
                        clean_x1 = min(x1 + 20, x1 + int(0.5 * line_h))
                        cv2.rectangle(image_vis, (clean_x0, y0), (clean_x1, y1), (0, 255, 0), 2)
            cv2.imwrite('%s/%s' % ('vis_detect', os.path.basename(fname)), image_vis)


    def faster_rcnn_code(self, data, FLAG_area=False, FLAG_vis=False, FLAG_no_parse=False, area_code='161'):
        """ code for use faster rcnn detection, add more bbox """
 
        # ------------------------------------
        # 1. 返回所有概率 >= 0.15 结果
        # 2. 选取 >= 0.8 部分提取，获得最终精准部分
        # 3. 删除 2 中选择重叠区域，剩下部分，再按照 2 方法合并
        # 降低概率阈值，获取更多

        fname = data['fname']

        # check if img_str is base64 or url
        image = utils._data_convert_image(data['img_str'])
        image_vis = image.copy()
        logger.info('start task %s ### in area_code %s' % (fname, area_code))

        # ------------------------------------
        # 1. detect text
        # ------------------------------------
        # makesure detection data is base64 encode
        if isinstance(data['img_str'], (str, unicode)) and data['img_str'].startswith(('http:', 'https:')) == False and data['img_str'].endswith(('.jpg', '.png')) == False: pass
        else: data['img_str'] = utils._img_to_str_base64(image)

        c_det = zerorpc.Client()
        c_det.connect("tcp://%s" % RPC_menu['kuaidi_detect_frcnn_PRC'])
        res_detect = c_det.detect(data, 0.2, 0.3)
        assert res_detect['msg'] == 'ok'
        c_det.close()
        
        # c_det.detect(data, 0.4, 0.3), 0.75 means more rectangle detection results
        THRE_small = 0.10
        THRE_large = 0.60

        LIST_used = list()
        LIST_clean = list()
        DICT_bbox = dict()
        LIST_data_kuaidi = list()

        # 目前测试，EAST 检测出效果最好
        bboxdict = res_detect['data']
        # 传统 Faster RCNN 检测流程，根据概率 Filter 结果
        for idx, inst in enumerate(bboxdict):
            if idx in LIST_used: continue

            rect = inst['bbox']
            x0, y0, x1, y1 = rect[0], rect[1], rect[2], rect[3]

            LIST_IoU_high = list()
            LIST_IoU_lower = list()
            
            # 高概率 THRE_large Filter
            LIST_IoU_high  = [(i, bbox) for i, bbox in enumerate(bboxdict) if idx not in LIST_used and bbox['score'] >= THRE_large and utils.IoU(bbox['bbox'], inst['bbox']) >= 0.2]
            LIST_used.extend([r[0] for r in LIST_IoU_high])

            # 低概率 THRE_small Filter
            LIST_IoU_lower = [(i, bbox) for i, bbox in enumerate(bboxdict) if idx not in LIST_used and bbox['score'] >= THRE_small and utils.IoU(bbox['bbox'], inst['bbox']) >= 0.2]
            LIST_used.extend([r[0] for r in LIST_IoU_lower])

            # 如高、低概率都无
            if len(LIST_IoU_high) == 0 and len(LIST_IoU_lower) == 0: continue

            # merge LIST_match_IoU
            FLAG_low_prob = True if len(LIST_IoU_high) == 0 else False

            if len(LIST_IoU_high) > 0:
                p = 3
                new_x0 = max(0, min([r[1]['bbox'][0] for r in LIST_IoU_high]) - 3 * p)
                new_y0 = max(0, min([r[1]['bbox'][1] for r in LIST_IoU_high]) - p)
                new_x1 = max([r[1]['bbox'][2] for r in LIST_IoU_high]) + 3 * p
                new_y1 = max([r[1]['bbox'][3] for r in LIST_IoU_high]) + p

            elif len(LIST_IoU_lower) > 0:
                # new_x0_big = min([r[1]['bbox'][0] for r in LIST_IoU_lower]) - 3 * p
                # new_y0_big = min([r[1]['bbox'][1] for r in LIST_IoU_lower]) - p
                # new_x1_big = max([r[1]['bbox'][2] for r in LIST_IoU_lower]) + 3 * p
                # new_y1_big = max([r[1]['bbox'][3] for r in LIST_IoU_lower]) + p

                p = 1
                new_x0 = max(0, min([r[1]['bbox'][0] for r in LIST_IoU_lower]) - 3 * p)
                new_y0 = max(0, min([r[1]['bbox'][1] for r in LIST_IoU_lower]) - p)
                new_x1 = max([r[1]['bbox'][2] for r in LIST_IoU_lower]) + 3 * p
                new_y1 = max([r[1]['bbox'][3] for r in LIST_IoU_lower]) + p

            # 过大笔迹直接滤除
            if new_y1 - new_y0 >= 150: continue

            # 判断新组合 rect 和已有数据是否有重合
            LIST_clean_IoU = [i for i, bbox in enumerate(LIST_clean) if utils.IoU(bbox, [new_x0, new_y0, new_x1, new_y1]) >= 0.2]
            if len(LIST_clean_IoU) > 0: continue

            # add to predict images list
            LIST_clean.append((new_x0, new_y0, new_x1, new_y1))
            DICT_bbox['%s_%s_%s_%s' % (new_x0, new_y0, new_x1, new_y1)] = inst

            im_crop = image[new_y0 : new_y1, new_x0 : new_x1, :]
            save_name = os.path.join('%s#%s#%d_%d_%d_%d.jpg' % (os.path.basename(fname), inst['class'], new_x0, new_y0, new_x1, new_y1))
            
            LIST_data_kuaidi.append({'fname': save_name, 'img_str': utils._img_to_str_base64(im_crop)})
            
            color = (255, 0, 0) if FLAG_low_prob == False else (0, 0, 255)
            cv2.rectangle(image_vis, (new_x0, new_y0), (new_x1, new_y1), color, 2)
            cv2.putText(image_vis, inst['class'] + str(round(inst['score'], 4)), (x0, y0), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 0, 0), 2)

# ----------------------------------------
# read RPC conf 
# ----------------------------------------
# forcely copy RPC_list file to local folder
from RPC_list import RPC_menu

# rpc = MainRpc()
# data = {
            # "result": {
                # "receiveCustomerPhone": {'text':'18333333333'},
                # "receiveCustomerName": {'text':u"钟伟宏"},
                # "rcProvName": {'text':u'四川'},
                # "rcCityName": {'text':''},
                # "rcDistName": {'text':u''},
                # "rcTownName": {'text':u''},
                # "receiveCustomerAddress": {'text':u"成都锦江"},
                # "goodsName": {'text':u""}
            # },
            # "cpId": "163"
            # }
# print repr(rpc.check_params(data)).decode('unicode-escape')

SERVER_name = 'kuaidi_RPC'
server = zerorpc.Server(MainRpc())
server.bind('tcp://0.0.0.0:18888')
server.run()

# server.bind('tcp://%s' % RPC_menu[SERVER_name])
logger.info('-------------- %s --------------' % SERVER_name)
logger.info('start %s --- address %s ok!' % (SERVER_name, RPC_menu[SERVER_name]))
