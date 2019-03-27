# -*- coding: utf-8 -*-
# -------------------------------------
# short text predict code
# -------------------------------------

import time
import json
import zerorpc
from tgrocery import Grocery


FOLDER_model = 'sample'
mapping_dict = {'1': 'phone', '2': 'name', '3': 'address', '4': 'package', '5': 'number'}

new_grocery = Grocery('sample')
new_grocery.load()
c = new_grocery.predict(text)
print '%s, %s, %s' % (c, mapping_dict[str(c)], line)




class MainRpc(object):

    def __init__(self):

        # rpc instance
        # direct connect KUAIDI detect & ocr RPC, nginx 虚拟入口
        self.c_det = zerorpc.Client()
        self.c_det.connect("tcp://%s" % RPC_menu['kuaidi_detect_PRC'])
        self.c_pre = zerorpc.Client()
        self.c_pre.connect("tcp://%s" % RPC_menu['kuaidi_ocr_RPC'])
        self.ft = util_render.put_chinese_text('msyh.ttc')

        # test and use in base64 code
        logger.info('start local kuaidi detect & predict test')
        for fname in glob.glob('../kuaidi/data/50_test/data/*.jpg'):
            if 'vis.jpg' in fname: continue
            TIME_start = time.time()
            # fname = '5602082344_20180116135634.jpg'
            data = {'fname': fname, 'img_str': fname}
            self.extract_predict(data, True)
            logger.info('finish test, cost %s' % (time.time() - TIME_start))

        # logger.info('start local kuaidi detect & predict test')
        # TIME_start = time.time()
        # fname = '5602082344_20180116135634.jpg'
        # data = {'fname': fname, 'img_str': _img_to_str_base64(cv2.imread(fname))}
        # self.extract_predict(data, True)
        # logger.info('finish test, cost %s' % (time.time() - TIME_start))

    def extract_predict(self, data, FLAG_vis=False):
        """ extract image and predict the content text
        """
        res = {
            'data': 0,
            'code': 102,
            'msg': ''
        }

        try:
            TIME_start = time.time()

            
            res['msg'] = 'ok'
            res['code'] = 0
            res['data'] = json.dumps(DICT_res)
            logger.info(DICT_res)
            logger.info('finish cost %s' % (time.time() - TIME_start))

        except Exception, e:
            res['msg'] = 'error'
            res['code'] = 103
            logger.error(str(e))
            logger.error(str(traceback.print_exc()))

        return res


# ----------------------------------------
# read RPC conf 
# ----------------------------------------
# forcely copy RPC_list file to local folder
from RPC_list import RPC_menu

SERVER_name = 'kuaidi_text_predict_RPC'
RPC_menu[SERVER_name] = '0.0.0.0:19999'
server = zerorpc.Server(MainRpc())
server.bind('tcp://%s' % RPC_menu[SERVER_name])
logger.info('-------------- %s --------------' % SERVER_name)
logger.info('start %s --- address %s ok!' % (SERVER_name, RPC_menu[SERVER_name]))
server.run()