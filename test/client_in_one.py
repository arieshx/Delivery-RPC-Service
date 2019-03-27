# -*- coding: utf-8
# ------------------------------------------
# Kuaidi pipeline code
# ------------------------------------------

import cv2, glob
import zerorpc
import os, sys
import numpy as np
import json, time
import time, shutil, base64
import util_draw_cn as util_render

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


def _data_convert_image(data):
    """ standard image read and load online version
    """
    TIME_start = time.time()
    if isinstance(data, (str, unicode)):
        if data.startswith(('http:', 'https:')):
            image = _url_to_image(data)
        elif data.endswith(('.jpg', '.png')):
            data = data.replace('\\', '/')
            image = cv2.imread(data)
        else:
            image = cv2.imdecode(np.asarray(bytearray(data), dtype=np.uint8), 1)
    else:
        image = data

    assert len(image.shape) == 3
    return image


c_kuaidi = zerorpc.Client()
c_kuaidi.connect("tcp://192.168.1.115:18888") # kuaidi

for _ in range(10):
    fname = '5602082344_20180116135634.jpg'
    image = _data_convert_image(fname)
    data = {'fname': fname, 'img_str': _img_to_str_base64(image)}
    
    TIME_start = time.time()
    res = c_kuaidi.extract_predict(data, False)
    print 'cost time', time.time() - TIME_start


with open('res.json', 'w') as o:
    print >> o, json.dumps(res)



# c_pre = zerorpc.Client()
# c_pre.connect("tcp://192.168.1.115:18001") # kuaidi
# ft = util_render.put_chinese_text('msyh.ttc')
# print '-' * 50, 'predict OK'


# FOLDER_predict = 'block_vis_gx/predict'
# if os.path.exists(FOLDER_predict): shutil.rmtree(FOLDER_predict)
# os.makedirs(FOLDER_predict)
# FOLDER_detect = 'block_vis_gx/detect'
# if os.path.exists(FOLDER_detect): shutil.rmtree(FOLDER_detect)
# os.makedirs(FOLDER_detect)
# FOLDER_detect = 'block_vis_gx/json'
# if os.path.exists(FOLDER_detect): shutil.rmtree(FOLDER_detect)
# os.makedirs(FOLDER_detect)


# # LIST_image = glob.glob('/media/hd01/zhilun/kaggle-canbin/dataset/batch_7590/*.jpg')
# # LIST_image += glob.glob('/media/hd01/zhilun/kaggle-canbin/dataset/batch_7500/*.jpg')
# LIST_image = glob.glob('data/20180201_gx/*.jpg')

# for idx, fname in enumerate(LIST_image):
#     # if '5216967784_20170419211116' not in fname: continue

#     TIME_start = time.time()
#     count = 0
#     image = None
#     image = cv2.imread(fname)
#     image = image[55 :, :, :]

#     data = {'fname': fname, 'img_str': _img_to_str_base64(image)}
#     res_detect = c_det.detect(data)
#     count += len(res_detect['data'])

#     # --------------------------------------
#     # extract detection and predict text from image
#     LIST_res = extract_predict(image, fname, res_detect['data'])
#     print '%s/%s' % (idx, len(LIST_image)), round(time.time() - TIME_start, 3), count, fname

#     for text_inst in LIST_res:
#         name = text_inst['filename']
#         rect = [int(v) for v in os.path.basename(name).split('#')[-1].split('.jpg')[0].split('_')]
#         x, y, w, h = rect[0], rect[1], rect[2], rect[3]

#         # vis hand or print
#         if 'hand' in os.path.basename(name): color = (255, 0, 0)
#         elif 'print' in os.path.basename(name): color = (0, 255, 255)
#         elif 'wrong' in os.path.basename(name): color = (0, 0, 255)
#         cv2.rectangle(image, (x, y), (w, h), color, 2)
#     # cv2.imwrite('block_vis/detect/%s_vis.jpg' % os.path.basename(fname), image)

#     # --------------------------------------
#     # vis predict result on image
#     for idx, text_inst in enumerate(LIST_res):
#         name = text_inst['filename']
#         rect = [int(v) for v in os.path.basename(name).split('#')[-1].split('.jpg')[0].split('_')]
#         x, y, w, h = rect[0], rect[1], rect[2], rect[3]
#         render_text = text_inst['text']
#         image = ft.draw_text(image, (x, y - 20), render_text, 18, (0, 0, 0))
#         LIST_res[idx]['rect'] = rect
#         LIST_res[idx]['text'] = LIST_res[idx]['text']
#         LIST_res[idx]['filename'] = os.path.basename(LIST_res[idx]['filename'])

#     # if idx <= 100:
#     cv2.imwrite('block_vis_gx/predict/%s_vis.jpg' % os.path.basename(fname), image)
    
#     with open('block_vis_gx/json/%s_vis.json' % os.path.basename(fname), 'w') as o: 
#         print >> o, json.dumps({'bbox': res_detect['data'], 'detect': LIST_res})
