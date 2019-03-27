# -*-coding:utf-8-*-
import os, json, cv2, re, time, signal, codecs
import base64, glob, itertools, traceback
import Levenshtein as lvst
import math

# import ancillary
from Bio.pairwise2 import format_alignment
from Bio import pairwise2
import sys

reload(sys)
sys.setdefaultencoding("utf-8")


# 判断是否是电话
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


def main(truths, pred, line_data):
    # truth = "湖南省娄底市新化县南正街金属藏衣"
    # pred = "湖南底新化南正街金面放"
    print('\n'.join(truths))
    print(pred)
    # print line_data['pic_path']
    try:
        print('RUNNING!')
        alignments = []
        for truth in truths:
            if truth == '': continue
            alignments.append(pairwise2.align.globalms(list(truth), list(pred), 1, -1, -1, -1, gap_char=['_'])[0])
        # print('----------')
        # 对所有truth，选择得分最高的
        alignment = max(alignments, key=lambda x: x[2])
        print alignment
        align1, align2, score, begin, end = alignment
        # print align1, align2
        line_data['score'] = score
        correct_str = format_alignment_index(align1, align2, score, begin, end, line_data)
        # 找到详细地址
        c_num = 0
        for i in range(len(align2)-1, 0, -1):
            if align2[i] == '_':
                break
            else:
                continue
        for j in range(i, 0, -1):
            if align2[j] == '_':
                c_num += 1
                continue
            else:
                break
        if c_num>3:
            detail_address = align1[j+1:]
            detail_address = ''.join(detail_address)
        # print('详细地址：')
        # print(detail_address)
        # print('+++++++++')
        return correct_str
    except:
        print('ERROR!')
        print(traceback.format_exc())
        time.sleep(30)
        return ''


nations = codecs.open('database/nation.txt', 'r', 'utf-8')
nation = ''
for n in nations:
    nation = nation + n.strip() + '|'
    if len(n.strip()) > 2:
        nation = nation + n.strip()[:-1] + '|'
nation = str(nation[:-1])
# nation = '汉族'
def remove_suffix(name, area_level):
    if len(name) > 1:
        if area_level==0:
            sub_name = re.sub(r'(省$|市$|(维吾尔|壮族|回族|)自治区$|区$|地区$|特别行政区$)', '', name)
        elif area_level ==1:
            sub_name = re.sub(r'(市辖区$|市$|(%s)|自治州$|地区$|盟$)' % (nation), '', name)
        elif area_level==2:
            sub_name = re.sub(r'(市辖区$|市$|区$|(%s)|县$|自治县$|林区$|旗$|自治旗$)' % (nation), '', name)
        elif area_level==3:
            sub_name = re.sub(r'(街道办事处$|街道$|办事处$|(%s)|乡$|苏木$|镇$|农场$|监狱$|区公所$|街道办事$|地区办事处$|综合保税区$)' % (nation), '', name)
        else:
            print('地址级别参数错误：', area_level)
            return unicode(name)
        sub_name = unicode(sub_name)
        suffix = unicode(name)[len(sub_name):]
        return sub_name, suffix
        #return re.sub(r'(省|市|(维吾尔|壮族|回族|)自治区|区|地区)|(\B(%s)*(自治州|盟|县|自治县|自治旗|矿区|特区|特别行政区))()$'%(nation), '', name)

# name = '市中区'
# a, b = remove_suffix(name, 2)
# print(a, b)

def find_detail_address(addr1, align1, align2, last_jiexi_name, last_jiexi_name_begin_index, last_jiexi_name_end_index):
    """从两个匹配过的字符串中找合适的详细地址的字段
    """
    gap_char_num = 0
    for i in range(last_jiexi_name_begin_index, last_jiexi_name_end_index):
        if align2[i] == gap_char:
            gap_char_num+=1
    if gap_char_num<3:
        if align1[last_jiexi_name_end_index] ==align2[last_jiexi_name_end_index]:
            detail_address = align1[last_jiexi_name_end_index+1:]
        else:
            detail_address = align1[last_jiexi_name_end_index:]
    else:
        detail_address = align1[last_jiexi_name_begin_index:]
    # last_name_align2_index = ''.join(align2).find(last_jiexi_name[0:-1])
    # for i in range(last_name_align2_index, last_name_align2_index+len(last_jiexi_name)):
    #     pass
    # if align1[i] == align2[i]:
    #     if i < len(align1)-1:
    #         detail_address = align1[i+1:]
    #     else:
    #         detail_address = ''
    # else:
    #     detail_address = align1[i:]
    detail_address = ''.join(detail_address)
    detail_address = detail_address.replace(gap_char, '')
    detail_address += addr1.replace(''.join(align1).replace(gap_char, ''), '')
    return detail_address


gap_char = '▲'  # ''
def get_detail_add(addr1, addr2, addr2_list):
    """
    addr1 = '上海浦东新区南汇宣桥镇宣桥枫庭1955弄5号40'
    addr2 = '上海市上海市浦东新区中国（上海）自由贸易试验区（保税片区）'
    :param addr1:
    :param addr2:
    :param addr2_list:
    :return:
    """

    human_check = 0
    print('---------------------------------------开始进行alignment来判断地址解析是否正确以及获取各个地址')
    assert len(addr2_list) in [2, 3, 4], '神经网络输出字段范围从2到4'
    assert sum([len(_) for _ in addr2_list]) == len(addr2), '长度不符合'
    print('初始输入文本：')
    print(addr1)
    print('初始神经网络解析输出:')
    print(addr2)

    # 对解析地址出北京市北京市的，去掉一个
    if_remove_sheng = 0
    tmp_addr2_list = addr2_list[:]
    if addr2_list[0] == addr2_list[1]:
        tmp_addr2_list = addr2_list[1:]
        if_remove_sheng = 1
    # 对原地址有北京北京的，去掉一个
    # zhixiashi_list = [u'北京', u'上海', u'重庆', u'天津']
    # care_str = addr1[0:6]
    # remain_str = care_str
    # for zhixiashi in zhixiashi_list:
    #     all_index = [m.start() for m in re.finditer(zhixiashi, addr1)]
    #     if len(all_index) >1:
    #         remain_str = care_str[all_index[-1]: ]
    #         break
    #     elif len(all_index) == 1:
    #         # remain_str = care_str
    #         break
    #     else:
    #         continue
    # addr1 = remain_str+addr1[6:]
    # addr1可能多几个字，比如有限公司，比如一个人名，这样会使alignment危险，所以从地址开始匹配，去掉开头。
    # if len(tmp_addr2_list)!=0:
    #     for idx, a_char in enumerate(tmp_addr2_list[0][0:2]):
    #         addr1_index_begin = addr1.find(a_char)
    #         if addr1_index_begin == -1:
    #             if idx == 1:
    #                 human_check = 1
    #             else:
    #                 continue
    #         else:
    #             addr1 = addr1[addr1_index_begin: ]
    #             break

    # 首先进行一遍alignment，然后找到匹配最好的解析地址，然后从那一级再次alignment
    addr2 = ''.join(tmp_addr2_list)
    addr1_align = addr1[0:]
    print('首先一次匹配初始信息-----------------------')
    print('addr1做匹配字段：')
    print(addr1_align)
    print('解析做匹配字段:')
    print(addr2)
    alignments = []
    alignments.extend(
        pairwise2.align.globalms(list(addr1_align), list(addr2), 1, -1, -1, -1, gap_char=[gap_char]))
    alignment = max(alignments, key=lambda x: x[2])
    align1, align2, score, begin, end = alignment
    show_align_result(align1, align2, begin, end)

    str_align2 = ''.join(align2)
    right_percent_dict = {0: 0, 1: 0, 2: 0, 3: 0}
    begin_index_dict = {0: 0, 1: 0, 2: 0, 3: 0}
    for idx, jiexi_name in enumerate(tmp_addr2_list):
        if if_remove_sheng:
            area_level = idx+1
        else:
            area_level = idx
        only_name = remove_suffix(str(jiexi_name), area_level)
        index = str_align2.rfind(only_name)
        if index != -1:
            start_index = index
            end_index = index + len(only_name)
            begin_index_dict[area_level] = start_index
            char_num = len(only_name)
            if char_num == 0:
                right_percent_dict[area_level] = 0
            else:
                right_num = 0
                for i in range(start_index, end_index):
                    if align1[i] == align2[i]:
                        right_num += 1
                right_percent_dict[area_level] = right_num*1./char_num
        else:
            right_percent_dict[area_level] = 0
    great_level = 0
    for area_level in right_percent_dict.keys():
        if right_percent_dict[area_level] >= right_percent_dict[great_level]:
            great_level = area_level
    if right_percent_dict[great_level]> 0.3:
        begin_index = begin_index_dict[great_level]
        addr1_remove_head = ''.join(align1[begin_index:]).replace(gap_char, '')
        tmp_addr2_list = addr2_list[great_level:]
    else:
        human_check = 1
        detail_address = addr1
        print('寻找最佳开头匹配位置失败，返回humancheck')
        return detail_address, tmp_addr2_list, human_check

    while len(tmp_addr2_list) > 0:
        addr2 = ''.join(tmp_addr2_list)
        addr1_align = addr1_remove_head[0: len(addr2)]
        print('一次匹配初始信息-----------------------')
        print('addr1做匹配字段：')
        print(addr1_align)
        print('解析做匹配字段:')
        print(addr2)
        alignments = []
        alignments.extend(
            pairwise2.align.globalms(list(addr1_align), list(addr2), 1, -1, -1, -1, gap_char=[gap_char]))
        alignment = max(alignments, key=lambda x: x[2])
        align1, align2, score, begin, end = alignment
        show_align_result(align1, align2, begin, end)
        # 一次匹配完毕，判断最后一个解析字段是否合理
        last_jiexi_name = tmp_addr2_list[-1]
        str_align2 = ''.join(align2)

        # 找到最后一个解析字段在align2的位置，可以包含gap，
        # i = len(last_jiexi_name)-1
        # for j in range(len(str_align2)-1, -1, -1):
        #     if str_align2[j] == gap_char:
        #         continue
        #     elif str_align2[j] == last_jiexi_name[i]:
        #         if i > 0:
        #             i -= 1
        #         else:
        #             break
        # if str_align2[j] == last_jiexi_name[0]:
        #     last_jiexi_name_begin_index = j
        #     last_jiexi_name_end_index = j + str_align2[j:].rfind(last_jiexi_name[-1])
        # else:
        #     print('something error~')
        #     return 'error'

        # 找到最后一个解析字段在align2的位置，不可以包含gap
        last_jiexi_pure_name = remove_suffix(str(last_jiexi_name))
        index = str_align2.rfind(last_jiexi_name[:-1])
        if index != -1:
            last_jiexi_name_begin_index = index
            last_jiexi_name_end_index = index+len(last_jiexi_name)-1
        else:
            print('最后一级解析字段并不完美,去掉进行下次匹配')
            tmp_addr2_list = tmp_addr2_list[: -1]
            continue
        char_num = 0
        char_right_num = 0
        for i in range(last_jiexi_name_begin_index, last_jiexi_name_end_index):
            char_num += 1
            if align1[i] == align2[i]:
                char_right_num += 1
        if char_num == 0:
            print('town error, char_num ==0')
        else:
            last_name_pass_percent = char_right_num * 1. / char_num
        if last_name_pass_percent >= 0.34:  # 1.0/(last_jiexi_name_end_index-last_jiexi_name_begin_index):
            detail_address = find_detail_address(addr1_remove_head, align1, align2, last_jiexi_name, last_jiexi_name_begin_index, last_jiexi_name_end_index)
            print('解析和匹配比较合理，找到合理的详细地址:')
            print(detail_address)
            remain_addr2_list = addr2_list[0: addr2_list.index(tmp_addr2_list[-1])+1]
            if len(remain_addr2_list) >=2:
                human_check = 0
            else:
                human_check = 1
            return detail_address, remain_addr2_list, human_check

        # last_jiexi_name_align_index = ''.join(align2).find(last_jiexi_name[0:-1])
        # if last_jiexi_name_align_index == -1:
        #     tmp_addr2_list = tmp_addr2_list[: -1]
        #     continue
        # char_num = 0
        # char_right_num = 0
        # for i in range(last_jiexi_name_align_index, last_jiexi_name_align_index + len(last_jiexi_name)):
        #     char_num += 1
        #     if align1[i] == align2[i]:
        #         char_right_num += 1
        # if char_num == 0:
        #     print('town error, char_num ==0')
        # else:
        #     last_name_pass_percent = char_right_num * 1. / char_num
        # if last_name_pass_percent > 1.0/(len(last_jiexi_name)-1):
        #     print('解析和匹配比较合理，找到合理的详细地址')
        #     detail_address = find_detail_address(addr1, align1, align2, last_jiexi_name)
        #     return detail_address, tmp_addr2_list
        #     break
        else:
            print('最后一级解析字段并不完美,去掉进行下次匹配')
            tmp_addr2_list = tmp_addr2_list[: -1]
            continue
    #if detail_address == u'':
    detail_address = addr1
    print('完全体：')
    print(detail_address)
    human_check = 1
    remain_addr2_list = []
    return detail_address, remain_addr2_list, human_check

    # 验证区和详细地址是否alignment合理，也验证了地址解析神经网络的正确性。
    # 区
    # if index_dict['dist']['start'] != None:
    #     net_dist_name = addr2[index_dict['dist']['start']: index_dict['dist']['end']]
    #     str_align2 = ''.join(align2)
    #     dist_index = str_align2.find(net_dist_name)
    #     char_num = 0
    #     char_right_num = 0
    #     for i in range(dist_index, dist_index+len(net_dist_name)):
    #         char_num +=1
    #         if align1[i] == align2[i]:
    #             char_right_num += 1
    #     if char_num == 0:
    #         print('error, char_num == 0')
    #     else:
    #         dist_pass_percent = char_right_num*1./char_num
    #     if dist_pass_percent > 0.3:
    #         human_check = 0
    #     else:
    #         human_check = 1
    # if len(addr2_list)==4:
    #     net_town_name = addr2_list[3]
    #     str_align2 = ''.join(align2)
    #     town_index = str_align2.find(net_town_name)
    #     char_num = 0
    #     char_right_num = 0
    #     for i in range(town_index, town_index+len(net_town_name)):
    #         char_num += 1
    #         if align1[i] == align2[i]:
    #             char_right_num += 1
    #     if char_num == 0:
    #         print('town error, char_num ==0')
    #     else:
    #         town_pass_percent = char_right_num*1./char_num
    #     if town_pass_percent>0.4:
    #         human_check = 0
    #     else:
    #         human_check = 1
    # if human_check:
    #     addr2_notown = ''.join(addr2_list[: -1])
    #     print('街道对比失败，要去去掉街道再次alignment')
    #     print('输入文本：')
    #     print(addr1)
    #     print('神经网络输出去掉街道以后:')
    #     print(addr2_notown)
    #     alignments = []
    #     alignments.extend(pairwise2.align.globalms(list(addr1), list(addr2_notown), 1, -1, -1, -1, gap_char=[gap_char]))
    #     alignment = max(alignments, key=lambda x: x[2])
    #     align1, align2, score, begin, end = alignment
    #     show_align_result(align1, align2, begin, end)
    #     addr2 = addr2_notown
    #     addr2_list = addr2_list[: -1]
    # dist_or_town_name = addr2_list[-1][0:2]
    # reverse_align2 = align2[::-1]
    # wan_index = reverse_align2.index(dist_or_town_name[1])
    # real_index = len(align2)-1-wan_index
    # assert real_index >0
    # for i in range(real_index, len(align2)):
    #     if align2[i] == gap_char:
    #         break
    # detail_address = align1[i:]
    # detail_address = ''.join(detail_address)
    # detail_address = detail_address.replace(gap_char, '')
    # if len(detail_address) > 3:
    #     pass
    # else:
    #     detail_address = addr1
    #
    # # 找到详细地址
    # # c_num = 0
    # # for i in range(len(align2) - 1, , -1):
    # #     if align2[i] == '▲':
    # #         break
    # #     else:
    # #         continue
    # # for j in range(i, 0, -1):
    # #     if align2[j] == '▲':
    # #         c_num += 1
    # #         continue
    # #     else:
    # #         break
    # # if c_num > 3:
    # #     detail_address = align1[j + 1:]
    # #     detail_address = ''.join(detail_address)
    # #
    # # else:
    # #     detail_address = addr1
    #
    # print('-'*50)
    # if human_check:
    #     if_remove_town = 1
    # else:
    #     if_remove_town = 0
    # return detail_address, if_remove_town


def address_match(addr1, addr2_list):
    """
        addr1 = '上海浦东新区南汇宣桥镇宣桥枫庭1955弄5号40'
        addr2_list = ['上海市','上海市', '浦东新区', '中国（上海）自由贸易试验区（保税片区）']
        :param addr1:
        :param addr2_list:
        :return:
        """
    human_check = 0
    print('---------------------------------------开始进行alignment来判断地址解析是否正确以及获取各个地址')
    assert len(addr2_list) in [2, 3, 4], '神经网络输出字段范围从2到4'
    print('初始输入文本：')
    print(addr1)
    print('初始神经网络解析输出:')
    print(''.join(addr2_list))

    # 首先将解析出的地址，直辖市的部分删去一个字段，所以这两个变量记录了去除开头的信息
    if addr2_list[0] == addr2_list[1]:
        remove_zero_addr2_list = [u'___']+addr2_list[1:]
        if_remove_sheng = 1
    else:
        remove_zero_addr2_list = addr2_list[:]
        if_remove_sheng = 0
    # 将去掉zero级别解析地址字段去掉后缀（或不去掉后缀）后与长字段做直接alignment，找到长字段的最佳开始匹配位置
    remove_suffix_addr2_info_list = []  # 记录了去掉后缀的纯字段信息和去掉的后缀
    for level, name in enumerate(addr2_list):
        pure_name, suffix = remove_suffix(str(name), level)
        remove_suffix_addr2_info_list.append({'pure_name': pure_name, 'suffix': suffix})

    remove_suffix_pure_name_list = [_['pure_name'] for _ in remove_suffix_addr2_info_list]
    if if_remove_sheng:
        sort_align_addr2 = u'__' + ''.join(remove_suffix_pure_name_list[1:])
    else:
        sort_align_addr2 = ''.join(remove_suffix_pure_name_list[:])
    sort_align_addr1 = addr1[:]
    print('首先一次匹配,寻找最优长地址匹配点-----------------------')
    print('addr1做匹配字段：')
    print(sort_align_addr1)
    print('解析做匹配字段:')
    print(sort_align_addr2)
    alignments = []
    alignments.extend(
        pairwise2.align.localms(list(sort_align_addr1), list(sort_align_addr2), 3, -2, -1, -1, gap_char=[gap_char]))
    max_score = max(alignments, key=lambda x: x[2])[2]
    # 找同样分数中最合适的
    best_index = 0
    tmp_gap_num = 1000
    for idx, one_align in enumerate(alignments):
        if one_align[2] == max_score:
            last_word_index = ''.join(one_align[1]).rfind(sort_align_addr2[-1])
            gap_num = ''.join(one_align[1][0: last_word_index+1]).count(gap_char)
            if gap_num<=tmp_gap_num:
                best_index = idx
                tmp_gap_num = gap_num
    alignment = alignments[best_index]
    align1, align2, score, begin, end = alignment
    show_align_result(align1, align2, begin, end)
    # 做完sort alognment，寻找最优开始匹配点
    str_align2 = ''.join(align2)
    right_percent_dict = {0: 0, 1: 0, 2: 0, 3: 0}  # 相对于初始的 addr2_list,而言
    begin_index_dict = {0: 0, 1: 0, 2: 0, 3: 0}
    remove_part = u''
    for idx, pure_name in enumerate(remove_suffix_pure_name_list):
        if if_remove_sheng and idx == 0:
            continue
        area_level = idx
        remain_part = str_align2.replace(remove_part, '')
        index = remain_part.find(pure_name)
        if index != -1:

            start_index = index + len(remove_part)
            end_index = start_index + len(pure_name)
            remove_part = str_align2[0: end_index]
            begin_index_dict[area_level] = start_index
            char_num = len(pure_name)
            if char_num == 0:
                right_percent_dict[area_level] = 0
            else:
                right_num = 0
                for i in range(start_index, end_index):
                    if align1[i] == align2[i]:
                        right_num += 1
                right_percent_dict[area_level] = right_num * 1. / char_num
        else:
            right_percent_dict[area_level] = 0

    great_level = 0
    for area_level in right_percent_dict.keys():
        if right_percent_dict[area_level] >= right_percent_dict[great_level]:
            great_level = area_level
    if right_percent_dict[3] > 0.8:
        start_level = 3
        begin_index = begin_index_dict[3]
        addr1_good_start = ''.join(align1[begin_index:]).replace(gap_char, '')
    elif right_percent_dict[2] > 0.8:
        start_level = 2
        begin_index = begin_index_dict[2]
        addr1_good_start = ''.join(align1[begin_index:]).replace(gap_char, '')
    elif right_percent_dict[1] > 0.8:
        start_level = 1
        begin_index = begin_index_dict[1]
        addr1_good_start = ''.join(align1[begin_index:]).replace(gap_char, '')
    else:
        human_check = 1
        remain_addr2_list = addr2_list[0:2]
        detail_address = addr1
        print('寻找最佳开头匹配位置失败')
    if human_check:
        return detail_address, remain_addr2_list, human_check
    # 寻找到了最佳的长字符串开始位置

    align_addr2 = ''.join(addr2_list[great_level:])
    align_addr1 = addr1_good_start[0: len(align_addr2)]
    last_part_addr1 = addr1_good_start.replace(align_addr1, '')
    last_part_addr1 = addr1_good_start[len(align_addr2):]
    print('从长字符串的最优点开始匹配-----------------------')
    print('addr1做匹配字段：')
    print(align_addr1)
    print('解析做匹配字段:')
    print(align_addr2)
    alignments = []
    alignments.extend(
        pairwise2.align.globalms(list(align_addr1), list(align_addr2), 1, -1, -1, -1, gap_char=[gap_char]))
    alignment = max(alignments, key=lambda x: x[2])
    align1, align2, score, begin, end = alignment
    show_align_result(align1, align2, begin, end)

    pure_name = remove_suffix_addr2_info_list[start_level]['pure_name']
    suffix = remove_suffix_addr2_info_list[start_level]['suffix']
    index = ''.join(align2).index(pure_name)
    right_num = 0
    for i in range(index, index+len(pure_name)):
        if align1[i] == align2[i]:
            right_num+=1
    if len(pure_name) == 0:
        print('error'*30,pure_name)
    pure_name_right_percent = right_num*1./len(pure_name)
    if pure_name_right_percent>0.8:

        # 找到合适的详细地址开始位置
        suffix_index = index+len(pure_name)
        if ''.join(align1[suffix_index: suffix_index+len(suffix)]) == suffix:
            detail_index = suffix_index+len(suffix)
        else:
            if start_level==3:
                detail_index = index
            else:
                detail_index = suffix_index
        detail_address = ''.join(align1[detail_index:]).replace(gap_char, '')+ last_part_addr1
        remain_addr2_list = addr2_list[0: start_level+1]
        print('找到合适详细地址：')
        print(detail_address)
        print('保留解析结果')
        print(remain_addr2_list[-1])
    else:
        #
        print('不会出现这种情形，出现的log，需要写其他的规则')
        detail_address = addr1
        remain_addr2_list = addr2_list
    return detail_address, remain_addr2_list, human_check


def show_align_result(align1, align2, begin, end):
    # 文本长度以预测文本即align2的长度为准
    # end = len(align2.strip('-'))
    # end += 1 if (len(align1)>end and align1[end] in PUNCT) else 0
    align1 = ''.join(align1)
    align2 = ''.join(align2)

    # 生成如下格式的字符串显示
    #   st-udy. Most of students study English by class. We don't have
    #   |  |||||||||||||||||||||||||||||||||||||||||||||||||||||||||||
    #   s-iudy. Most of students study English by class. We don't have
    s = []
    s.append("%s\n" % align1)
    for a, b, str_idx in zip(align1, align2, range(begin, end)):
        if a == b:
            s.append("|")  # match
        elif a == gap_char or b == gap_char:
            s.append(".")  # gap
        else:
            s.append(".")  # mismatch

    s.append("\n")
    s.append("%s\n" % align2)
    print(''.join(s))


# 将align1和align2对齐
def format_alignment_index(align1, align2, score, begin, end, line_data):
    """ use Bio.pairwise2.format_alignment as reference
        http://biopython.org/DIST/docs/api/Bio.pairwise2-pysrc.html#format_alignment
    """

    # 文本长度以预测文本即align2的长度为准
    # end = len(align2.strip('-'))
    # end += 1 if (len(align1)>end and align1[end] in PUNCT) else 0
    align1 = ''.join(align1)
    align2 = ''.join(align2)
    print(begin, end)

    # 生成如下格式的字符串显示
    #   st-udy. Most of students study English by class. We don't have
    #   |  |||||||||||||||||||||||||||||||||||||||||||||||||||||||||||
    #   s-iudy. Most of students study English by class. We don't have
    s = []
    s.append("%s\n" % align1)
    for a, b, str_idx in zip(align1, align2, range(begin, end)):
        if a == b:
            s.append("|")  # match
        elif a == "_" or b == "_":
            s.append(" ")  # gap
        else:
            s.append(".")  # mismatch

    s.append("\n")
    s.append("%s\n" % align2)
    print(''.join(s))

    # 开始配对
    correct_str = correction(align1, align2, line_data)
    return correct_str


# 判断是否是中文
def isChinese(str):
    if not isinstance(str, unicode):
        str = str.decode('utf-8')
    for ch in str:
        if u'\u4e00' <= ch <= u'\u9fff':
            return True
    return False


# 80%以上的字符是数字，则str是数字
def isNumber(str):
    i = 0
    for ch in str:
        if ch.isdigit():
            i += 1
    return False if float(i) / len(str) < 0.8 else True


# 进行纠正
def correction(align1, align2, line_data):
    # weights = line_data['prob']
    text_ocr_prob = line_data['text_ocr_prob']
    index = 0
    correct_str = []
    # if line_data['isNumber']:
    if (isNumber(align1) and line_data['score'] / len(align1) >= 0.6) \
            or (not isNumber(align1) and line_data['score'] >= 0):
        print '-------------------'
        # if (align1[-2:] == '先生' or align1[-2:] == '小姐') and line_data['score'] == 0:
        # print align1
        # print align2
        # print(line_data['score'])
        # time.sleep(2)
        # return ''
        for t, p in zip(list(align1), list(align2)):
            if t == p:
                index += 1
                correct_str.append(t)
            elif t == '_':
                if text_ocr_prob[index] > 0.85:
                    correct_str.append(p)
                index += 1
            elif p == '_':
                correct_str.append(t)
            else:
                if text_ocr_prob[index] > 0.9:
                    correct_str.append(p)
                else:
                    correct_str.append(t)
                index += 1
        return ''.join(correct_str)
    else:
        return ''
    # else:
    # if line_data['score'] >= 0:
    # return align1
    # return ''


# 删除图片
def removeImg(url):
    splited_url = url.split('/')
    fpath = './dataset/kd_images/{}/{}'.format(splited_url[-2], splited_url[-1])
    os.remove(fpath)


# 判断item是否是个dict且key是item的一个键
def has_result(item, key):
    return isinstance(item, dict) and key in item


# 得到text的开头或者结尾相同的每个子串
def getTextList(text):
    List = []
    for i in range(len(text)):
        List.append(text[:i + 1])
        List.append(text[-i - 1:])
    List.reverse()
    return List


def quHouzui(str):
    return re.sub(r'(省|市|(维吾尔|壮族|回族|)自治区|区|地区|街道|镇|乡)|(\B(%s)*(自治州|盟|县|旗|自治县|自治旗|矿区|特区|特别行政区))$' % (nation), '', str)


def parse_address(address_text):
    """
    解析一个拼接起来的地址，得到其省事县街道详细地址，若解析模型自信程度太低，则没有解析结果。
    :param address_text: 传递过来的拼接起来的地址，待解析
    :return:
    """
    from check import rule_check
    import addr_alignment
    from back_code.network import translate
    with open('t.txt', 'w') as o:
        # print >> o, ' '.join(list(address_text)).encode('utf-8')
        o.write(' '.join(address_text).encode('utf-8'))
    return_dict = {'human_check': False, 'provName': u'', 'cityName': u'', 'distName': u'', 'townName': u'',
                   'detailAddress': u''}
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
                print('pca验证通过')
                if not if_correct_jiedao:
                    print('街道验证不通过')
                    addr2_list = addr2_list[0: 3]
                else:
                    print('街道验证通过')
            else:
                print('pca验证不通过，街道不需要验证')
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
    return remain_addr2_list, detail_address

if __name__ == '__main__':
    list_addr1 = list()
    answer_list = list()
    one_addr1 = u'广东广州中大长江布区交易城A区四街04'
    list_addr1.append(one_addr1)
    one_answer = (u'广州市', u'中大长江布区交易城A区四街04')
    answer_list.append(one_answer)

    one_addr1 = u'广西壮族自治区崇左市凭祥市南大路百汇超市对面汉佣大厦西面12号仓库'
    list_addr1.append(one_addr1)
    one_answer = (u'凭祥市', u'南大路百汇超市对面汉佣大厦西面12号仓库')
    answer_list.append(one_answer)

    one_addr1 = u'广东深圳东门宝华白马时装批发市场6楼'
    list_addr1.append(one_addr1)
    one_answer = (u'深圳市', u'东门宝华白马时装批发市场6楼')
    answer_list.append(one_answer)

    one_addr1 = u'贵州省贵阳市花溪区湖潮乡贵安新区电子信产业园5栋4楼'
    list_addr1.append(one_addr1)
    one_answer = (u'花溪区', u'湖潮乡贵安新区电子信产业园5栋4楼')
    answer_list.append(one_answer)

    one_addr1 = u'贵州省贵阳市花溪区'
    list_addr1.append(one_addr1)
    one_answer = (u'花溪区', u'')
    answer_list.append(one_answer)

    one_addr1 = u'广东省深圳市宝安区'
    list_addr1.append(one_addr1)
    one_answer = (u'宝安区', u'')
    answer_list.append(one_answer)

    one_addr1 = u'广西壮族自治区崇左市凭祥市'
    list_addr1.append(one_addr1)
    one_answer = (u'凭祥市', u'')
    answer_list.append(one_answer)

    one_addr1 = u'启明核心科技静静北京丰台南三环中路19号（城市印象)1-C-1102'
    list_addr1.append(one_addr1)
    one_answer = (u'丰台区', u'南三环中路19号（城市印象)1-C-1102')
    answer_list.append(one_answer)

    one_addr1 = u'北京市北京市丰台南三环中路19号（城市印象)1-C-1102'
    list_addr1.append(one_addr1)
    one_answer = (u'丰台区', u'南三环中路19号（城市印象)1-C-1102')
    answer_list.append(one_answer)

    one_addr1 = u'广东省深圳市宝安区'
    list_addr1.append(one_addr1)
    one_answer = (u'宝安区', u'')
    answer_list.append(one_answer)

    one_addr1 = u'上海浦东新区南汇宣桥镇宣桥枫庭1955弄5号40'
    list_addr1.append(one_addr1)
    one_answer = (u'浦东新区', u'南汇宣桥镇宣桥枫庭1955弄5号40')
    answer_list.append(one_answer)

    one_addr1 = u'广东珠海香州九州大道东197号'
    list_addr1.append(one_addr1)
    one_answer = (u'珠海市', u'香州九州大道东197号')
    answer_list.append(one_answer)

    one_addr1 = u'新疆乌鲁木齐天山区九州大道东197号'
    list_addr1.append(one_addr1)
    one_answer = (u'乌鲁木齐市', u'天山区九州大道东197号')
    answer_list.append(one_answer)

    one_addr1 = u'湖北恩施恩施清江东路5号'
    list_addr1.append(one_addr1)
    one_answer = (u'恩施市', u'清江东路5号')
    answer_list.append(one_answer)

    one_addr1 = u'北京北京市丰台区宛平城镇丰台看守所南墙胡同到头001号'
    list_addr1.append(one_addr1)
    one_answer = (u'丰台区', u'宛平城镇丰台看守所南墙胡同到头001号')
    answer_list.append(one_answer)

    one_addr1 = u'浙江省杭州市余杭区崇贤街道府新街105号崇贤街道办事处'
    list_addr1.append(one_addr1)
    one_answer = (u'崇贤街道', u'府新街105号崇贤街道办事处')
    answer_list.append(one_answer)

    one_addr1 = u'天津塘沽黄海路19号金元宝国际店二楼曼妮夯'
    list_addr1.append(one_addr1)
    one_answer = (u'天津市', u'塘沽黄海路19号金元宝国际店二楼曼妮夯')
    answer_list.append(one_answer)

    one_addr1 = u'河北省保定市安国市祁州路街道祁州镇丽景佳苑小区3号楼1单元301室'
    list_addr1.append(one_addr1)
    one_answer = (u'安国市', u'祁州路街道祁州镇丽景佳苑小区3号楼1单元301室')
    answer_list.append(one_answer)

    one_addr1 = u'河北廊坊大厂夏垫潮白河工业园太丰村北'
    list_addr1.append(one_addr1)
    one_answer = (u'大厂回族自治县', u'夏垫潮白河工业园太丰村北')
    answer_list.append(one_answer)

    one_addr1 = u'北京北京市丰台区宛平城镇丰台看守所南墙胡同到头001号'
    list_addr1.append(one_addr1)
    one_answer = (u'丰台区', u'宛平城镇丰台看守所南墙胡同到头001号')
    answer_list.append(one_answer)

    one_addr1 = u'山东省枣庄市市中区文化路街道振兴路儿童乐园西门对过北30米蛙鱼君的店'
    list_addr1.append(one_addr1)
    one_answer = (u'文化路街道办事', u'文化路街道振兴路儿童乐园西门对过北30米蛙鱼君的店')
    answer_list.append(one_answer)

    one_addr1 = u'云南曲靖麒麟南宁南宁西路621号聚一堂茶店'
    list_addr1.append(one_addr1)
    one_answer = (u'南宁街道', u'南宁南宁西路621号聚一堂茶店')
    answer_list.append(one_answer)

    one_addr1 = u'江苏苏州吴中吴中科技园307长景路99号'
    list_addr1.append(one_addr1)
    one_answer = (u'吴中区', u'吴中科技园307长景路99号')
    answer_list.append(one_answer)

    one_addr1 = u'吉林长春宽城柳影路美景天城2期41栋3门'
    list_addr1.append(one_addr1)
    one_answer = (u'柳影街道', u'柳影路美景天城2期41栋3门')
    answer_list.append(one_answer)

    one_addr1 = u'贵州省*市大十字街道学院路州林汽大修厂(原鑫湾湾)酒家旁'
    list_addr1.append(one_addr1)
    one_answer = (u'', u'贵州省*市大十字街道学院路州林汽大修厂(原鑫湾湾)酒家旁')
    answer_list.append(one_answer)

    one_addr1 = u'湖北省武汉市武昌区杨园街街道杨园街办事处友谊大道铁机路铁机东区3栋1单元302'
    list_addr1.append(one_addr1)
    one_answer = (u'武昌区', u'杨园街街道杨园街办事处友谊大道铁机路铁机东区3栋1单元302')
    answer_list.append(one_answer)

    one_addr1 = u'广东惠州博罗湖镇胡镇罗口顺244省道锦德电化有'
    list_addr1.append(one_addr1)
    one_answer = (u'湖镇镇', u'湖镇胡镇罗口顺244省道锦德电化有')
    answer_list.append(one_answer)

    one_addr1 = u'天津和平区和平区岳阳道73号和平新中心'
    list_addr1.append(one_addr1)
    one_answer = (u'和平区', u'和平区岳阳道73号和平新中心')
    answer_list.append(one_answer)

    # 北京北京市丰台区宛平城镇丰台看守所南墙胡同到头001号
    # 浙江省杭州市余杭区崇贤街道府新街105号崇贤街道办事处
    # 江苏苏州吴中吴中科技园307长景路99号
    # 吉林长春城柳路美景天城2期41栋3门401
    #
    run_answer_list = list()
    for idx, one_addr1 in enumerate(list_addr1[:]):
        print(idx)
        remain_addr2_list, detail_address = parse_address(one_addr1)
        run_answer_list.append((remain_addr2_list[-1], detail_address))

    # 比较结果是否正确，
    for i in range(len(answer_list)):
        if answer_list[i] == run_answer_list[i]:
            print(u'待解析字段：', '*'*60, 'OK', i)
            print(list_addr1[i])
            print('解析结果:')
            print('保留字段：%s\t详细地址：%s' %(run_answer_list[i][0],run_answer_list[i][1]) )
        else:
            print(u'待解析字段：', '*' * 60, 'ERROR', i)
            print(list_addr1[i])
            print('解析结果:')
            print('保留字段：%s\t详细地址：%s' % (run_answer_list[i][0], run_answer_list[i][1]))
