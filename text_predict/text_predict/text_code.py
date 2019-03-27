# -*- coding: utf-8 -*-
import os, random, jieba, sys
from tgrocery import Grocery

arg = sys.argv
isTrain = 0
if len(arg) > 1:
    isTrain = int(arg[1])
    print type(isTrain), isTrain
cha = 0.5
if len(arg) > 2:
    cha = float(arg[2])
    print type(cha), cha
if not isTrain:
    # random trainset
    DICT_label = dict()
    for line in open('all.txt', 'r').readlines():
        try:
            label = line.strip().split('\t')[0]
            text  = line.strip().split('\t')[1]#.decode('utf-8')
            text  = ' '.join(list(text.decode('utf-8')))
            if DICT_label.has_key(label) == False: DICT_label[label] = []
            DICT_label[label].append(text)
        except:
            continue

    sample_ratio = 0.9

    LIST_train = list()
    LIST_valid = list()
    for label in DICT_label:
        LIST_text = DICT_label[label]
        random.shuffle(LIST_text)
        LIST_train.extend([(label, l) for l in LIST_text[0 : int(len(LIST_text) * sample_ratio)]])
        LIST_valid.extend([(label, l) for l in LIST_text[max(int(len(LIST_text) * sample_ratio),len(LIST_text)-200) : ]])
        print label, len(DICT_label[label]), DICT_label[label][0]

    print '-' * 30
    print 'train', len(LIST_train)
    print 'valid', len(LIST_valid)

    with open('train-sent.txt', 'w') as o:
        random.shuffle(LIST_train)
        for line in LIST_train:
            print >> o, ('%s,%s' % (line[0], line[1])).encode('utf-8')

    with open('valid-sent.txt', 'w') as o:
        random.shuffle(LIST_valid)
        for line in LIST_valid:
            print >> o, ('%s,%s' % (line[0], line[1])).encode('utf-8')

    # grocery = Grocery('sample', custom_tokenize=jieba.cut)
    grocery = Grocery('all')
    grocery.train('train-sent.txt', delimiter=',')
    # # 保存模型
    grocery.save()




new_grocery = Grocery('all')
new_grocery.load()
acc = new_grocery.test('valid-sent.txt', delimiter=',').accuracy_labels
for i in acc:
    print i, acc[i]
file = open('valid-sent.txt')
result = open('result.txt', 'w+')

DICT_res_stat = dict()
mapping_dict = {'1': 'province', '2': 'city', '3': 'address', '4': 'town', '5': 'name', '6': 'shouji', '7': 'dianhua', '8': 'number', '9': 'leibie'}

total_corr = 0
total_count = 0
with open('result.txt', 'w') as o:
    for line in file:
        line = line.strip()
        line_label = line.split(',')[0]
        text = line.split(',')[1]
        c = new_grocery.predict(text)
        #d是对text的每个类别预测的权重，对d进行排序
        d = c.dec_values
        s = sorted(d.items(),key = lambda x:x[1],reverse = True)
        #若排序后第二的label是leibie，且值与第一相差不超过cha的话，就讲label改为leibie
        if s[1][0] == '9' and s[0][1] - s[1][1] < cha:
            c = '9'
        #print mapping_dict[str(c)], text
  
        print >> o, '%s, %s, %s' % (c, mapping_dict[str(c)], line)
        if DICT_res_stat.has_key(line_label) == False: DICT_res_stat[line_label] = {'error' : [], 'correct': []}
        if str(c) == line_label:
            DICT_res_stat[line_label]['correct'].append(line)
            total_corr += 1
        else:
            DICT_res_stat[line_label]['error'].append(line)
        total_count += 1

# stat out
print '-' * 50
for label in DICT_res_stat:
    print mapping_dict[str(label)], 1.0 * len(DICT_res_stat[label]['correct'])/(len(DICT_res_stat[label]['error']) + len(DICT_res_stat[label]['correct'])), len(DICT_res_stat[label]['correct']), (len(DICT_res_stat[label]['error']) + len(DICT_res_stat[label]['correct']))
print '-' * 50
print 1.0 * total_corr / total_count