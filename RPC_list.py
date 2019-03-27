# -*-coding:utf-8-*-
# --------------------------------------------------------
# RPC conf
# Copyright (c) 2018 SigmaAI
# Licensed under The MIT License [see LICENSE for details]
# Written by Zhilun YANG
# --------------------------------------------------------

import socket
from easydict import EasyDict as edict
__C = edict()
RPC_menu = __C
host_name = socket.gethostname()

env = 'dev'
if host_name in ['gpu-master', 'iZuf626a59hclcqeunc42eZ']: 
    env = 'prod-aliyun'

DICT_addr = {'dev':                     '192.168.1.115', 
             'prod-hexin':              '192.168.1.115',    # suggest use different machine node
             'prod-aliyun':             '0.0.0.0'}

#
# preprocess & layout
#
__C.page_layout_PRC                     = '%s:99999' % DICT_addr[env] 
__C.anchor_RPC                          = ''
__C.qrcode_RPC                          = ''
__C.student_id_RPC                      = ''                        # 学号识别（但姓名更靠谱）


#
# 姓名识别 & 处理
#
__C.name_detect_PRC                     = '%s:10000' % DICT_addr[env]
__C.name_ocr_RPC                        = '%s:10001' % DICT_addr[env]
__C.name_ngram_RPC                      = '%s:10002' % DICT_addr[env]


#
# English OCR
#
# 依赖项
__C.ocr_en_blank_detect_PRC             = '%s:19100' % DICT_addr[env]     # GPU 0
__C.ocr_en_correct_detect_PRC           = '%s:19200' % DICT_addr[env]     # GPU 0


# 英文 nginx 入口
__C.en_ocr_RPC                          = '%s:12000' % DICT_addr[env]
__C.en_ocr_RPC_01                       = '%s:12001' % DICT_addr[env]
__C.en_ocr_RPC_02                       = '%s:12002' % DICT_addr[env]
__C.en_ocr_RPC_03                       = '%s:12003' % DICT_addr[env]
__C.en_ocr_RPC_04                       = '%s:12004' % DICT_addr[env]
__C.en_ocr_RPC_05                       = '%s:12005' % DICT_addr[env]


# 中文 nginx 入口
__C.cn_ocr_RPC                          = '%s:11000' % DICT_addr[env]
__C.cn_ocr_RPC_01                       = '%s:11001' % DICT_addr[env]
__C.cn_ocr_RPC_02                       = '%s:11002' % DICT_addr[env]


# 数理 nginx 入口
__C.math_ocr_RPC                        = '%s:13000' % DICT_addr[env]
__C.math_ocr_RPC_01                     = '%s:13001' % DICT_addr[env]


# __C.cn_ocr_test_RPC                   = '%s:11002'
__C.en_ngram_RPC                        = '%s:12101' % DICT_addr[env]


# 试题 RPC 入口 - 线上
__C.quest_RPC_00                        = '%s:17000' % DICT_addr[env]
__C.quest_RPC_01                        = '%s:17001' % DICT_addr[env]
__C.quest_RPC_02                        = '%s:17002' % DICT_addr[env]
__C.quest_RPC_03                        = '%s:17003' % DICT_addr[env]

# 试题 RPC 入口 - 测试
__C.quest_RPC_08                        = '%s:17008' % DICT_addr[env]
__C.quest_RPC_09                        = '%s:17009' % DICT_addr[env]

#
# kuaidi RPC options
#
__C.kuaidi_RPC                          = '%s:18888' % DICT_addr[env]
__C.kuaidi_detect_PRC                   = '%s:18000' % DICT_addr[env]  # 18000
__C.kuaidi_detect_frcnn_PRC             = '%s:18003' % DICT_addr[env]
__C.kuaidi_ocr_RPC                      = '%s:18001' % DICT_addr[env]