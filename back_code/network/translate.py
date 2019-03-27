# -*-coding:utf-8-*-
#!/usr/bin/env python
from __future__ import division, unicode_literals
import argparse
import os

from onmt.translate.Translator import make_translator

import onmt.io
import onmt.translate
import onmt
import onmt.ModelConstructor
import onmt.modules
import onmt.opts

folder = os.path.dirname(os.path.realpath(__file__))
root_dir = os.path.abspath(os.path.join(folder, '../..'))


def network_parse(src_file, out_file):
    # 注释掉了强行加3个字符的操作，也可以选择留下。
    # with open(src_file, 'r') as f:
    #     txt = f.readline()
    # with open(src_file, 'w') as f:
    #     f.write(some_char+txt)
    LIST_predict = translator.translate(opt.src_dir, src_file, out_file, opt.batch_size, opt.attn_debug)
    return LIST_predict[1][0]['score'], ' '.join(LIST_predict[1][0]['area'])

# -------------------------------------
# when load at first
# -------------------------------------
parser = argparse.ArgumentParser(description='translate.py', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
onmt.opts.add_md_help_argument(parser)
onmt.opts.translate_opts(parser)
opt = parser.parse_args()

# set some default value
opt.gpu = -1
opt.model = '%s/deppon_model_acc_99.87_ppl_1.00_e9.pt' % folder  # no detail
# opt.model = '%s/deppon_model_acc_98.56_ppl_1.07_e11_detail.pt' % folder  # no detail
opt.replace_unk = True
opt.verbose = True
opt.attn_debug = False
translator = make_translator(opt, report_score=True)

# network_parse('t.txt', 'o.txt')
with open('%s/back_code/network/t_muban.txt' %(root_dir), 'r') as f:
    a = f.readline()
some_char = a[0:3]