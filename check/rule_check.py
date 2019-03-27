# -*-coding:utf-8-*-
import re
import codecs
import json
import os

folder = os.path.dirname(os.path.realpath(__file__))
root_dir = os.path.abspath(os.path.join(folder, '..'))
pcas = json.load(codecs.open('%s/pca.json' % folder, 'r', 'utf-8'))

def is_valid_pca(province, city, area):
    if pcas.has_key(province):
        if pcas[province].has_key(city):
            if area in pcas[province][city] or area==u'':
                return True
    return False


def if_correct_jiedao(area, jiedao):
    """
    判断街道是否是符合实际的街道
    :param area:
    :param jiedao:
    :return:
    """
    streets_info = json.loads(open('%s/database/streets_new.json' %(root_dir), 'r').read())
    areas_info = json.loads(open('%s/database/areas_new.json' %(root_dir), 'r').read())
    # streets_name_list = [_['name'] for _ in streets_info]
    correct_jiedao = False
    index_list = [i for i, v in enumerate(streets_info) if jiedao == v['name']]
    for index in index_list:
        areaCode = streets_info[index]['areaCode']
        area_index_list = [i for i, v in enumerate(areas_info) if areaCode == v['code']]
        if len(area_index_list)==0:
           print('找到该街道，该街道所属的区号未找到， 区号是：', areaCode)
        else:
            area_name = areas_info[area_index_list[0]]['name']
            if area == area_name:
                correct_jiedao = True
                break
            else:
                print(u'解析出来的区，街道：', area, jiedao)
                print(u'找到该街道，但是该街道所属区：', area_name, jiedao)
    return correct_jiedao

# 安国市 祁州药市街道
# area = u'安国市'
# jiedao = u'祁州药市街道'
# if_correct_jiedao(area, jiedao)

def check_net_parse_result(addr_list):
    """
    检查神经网络解析地址的结果是否合理，
    :return:
    """
    if len(addr_list) == 2:
        province, city = addr_list[0: 2]
        area = u''
    else:
        province, city, area = addr_list[0: 3]
    if_pca = is_valid_pca(province, city, area)
    if if_pca:
        if len(addr_list)==4:
            area, jiedao = addr_list[2:4]
            correct_jiedao = if_correct_jiedao(area, jiedao)
        else:
            correct_jiedao = True
    else:
        correct_jiedao = False
    return if_pca, correct_jiedao



def is_phoneNum(s):
    s = s.strip()
    p1 = re.compile(r'(13[0-9]|14[579]|15[0-3,5-9]|16[6]|17[0135678]|18[0-9]|19[89])\d{8}$')
    p2 = re.compile(r'(0\d{2,3}-?|)\d{7,8}(-\d{1,4}|)$')
    p3 = re.compile(r'^400(-?\d){7}$')
    deppon_month_code = '4008305555'

    if s.strip() == deppon_month_code:
        return False
    elif p1.match(s) or p2.match(s) or p3.match(s):
        return True
    else:
        return False
        
def is_cusNum(s):
    """ month code """
    s = s.strip()
    p = re.compile(r'[456]\d{8}$|\d{6}$|\d{4}($|-\d$)|\d{8}-(\d{6}$|\d{8}$|\d{3}-\d{4}$)|[FE]\d+$|S\d{8}-\d{8}$')
    deppon_month_code = '4008305555'
    if p.match(s) or s == deppon_month_code:
        return True
    else:
        return False

print is_phoneNum('0590-6088820')