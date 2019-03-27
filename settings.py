# -*-encoding: utf-8 -*-
# ----------------------------------------------
# @author zengbaoqing
# Nov 2017
# ----------------------------------------------

import os
import socket
import logging.config
from datetime import datetime

hostname = socket.gethostname()
if hostname.startswith('ali-prod'):
    env = 'prod'
    debug = False
    cache = True

elif hostname.startswith('vpc-prod'):
    env = 'prod'
    debug = False
    cache = True

elif hostname.startswith('ali-stable'):
    env = 'stable'
    debug = False
    cache = True

elif hostname.startswith('ali-test'):
    env = 'test'
    debug = False
    cache = False
else:
    env = 'dev'
    debug = True
    cache = True

# ----------------------------------------------
# Modify Currect RPC config
# ----------------------------------------------
# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
curr_dir = os.getcwd().split('/')[-1]
LOG_FILE_PATH = '/mnt/logs/%s/%s-index.log' % (curr_dir, datetime.now().strftime('%Y-%m-%d'))
if env == 'dev':
    LOG_FILE_PATH = os.path.join('../..', 'logs/%s/%s-index.log' % (curr_dir, datetime.now().strftime('%Y-%m-%d')))
    LOG_FILE_PATH = os.path.join('../', 'test_logs/%s/%s-index.log' % (curr_dir, datetime.now().strftime('%Y-%m-%d')))
    head, tail = os.path.split(LOG_FILE_PATH)
    if os.path.exists(head) == False: os.makedirs(head)
# ----------------------------------------------

# Logging conifg
LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'formatters': {
        'standard': {
            'format': '%(asctime)s [%(levelname)s] %(message)s'
        },
        'precise': {
            'format': '%(levelname)s \x1b[6;30;42m%(asctime)s\x1b[0m %(name)s \x1b[1;32;40m%(message)s\x1b[0m'
        },
    },
    'handlers': {
        'default': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': LOG_FILE_PATH,  # 日志输出文件
            'maxBytes': 1024 * 1024 * 5,  # 文件大小
            'backupCount': 5,  # 备份份数
            'formatter': 'standard',  # 使用哪种formatters日志格式
        },
        'error': {
            'level': 'ERROR',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': LOG_FILE_PATH,
            'maxBytes': 1024 * 1024 * 5,
            'backupCount': 5,
            'formatter': 'standard',
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'precise'
        },
        'request_handler': {
            'level': 'DEBUG',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': LOG_FILE_PATH,
            'maxBytes': 1024 * 1024 * 5,
            'backupCount': 5,
            'formatter': 'standard',
        },
        'scprits_handler': {
            'level': 'DEBUG',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': LOG_FILE_PATH,
            'maxBytes': 1024 * 1024 * 5,
            'backupCount': 5,
            'formatter': 'standard',
        }
    },
    'loggers': {
        'rpc': {
            'handlers': ['default', 'console'],
            'level': 'DEBUG',
            'propagate': False
        }
    }
}

logging.config.dictConfig(LOGGING)
logger = logging.getLogger('rpc')
