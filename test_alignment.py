# -*-coding:utf-8-*-
from Bio import pairwise2
import sys

reload(sys)
sys.setdefaultencoding("utf-8")
gap_char = u'▲'

a = u'广西壮族自治区崇左市凭祥市'
# a = u'浙江省杭州市余杭区崇贤街'
b = u'广西崇左凭祥广西凭祥'
obj = pairwise2.align
# c = pairwise2.align.globalxx(a, b)
d = pairwise2.align.globalms(list(a), list(b), 1, -1, -2, -1,  gap_char=[gap_char])
e = pairwise2.align.localms(list(a), list(b), 3, -2, -1.5, -1, gap_char=[gap_char])
e = pairwise2.align.globalms(list(a), list(b), 3, -2, -1.5, -1, gap_char=[gap_char])
print(d)