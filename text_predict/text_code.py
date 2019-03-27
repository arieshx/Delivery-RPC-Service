# -*- coding: utf-8 -*-
import os, random, jieba
from tgrocery import Grocery

# random trainset
DICT_label = dict()
for line in open('all.txt', 'r').readlines():
    try:
        label = line.strip().split('\t')[0]
        text  = line.strip().split('\t')[1]
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
    LIST_valid.extend([(label, l) for l in LIST_text[int(len(LIST_text) * sample_ratio) : ]])
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
# acc = new_grocery.test('valid-sent.txt', delimiter=',').accuracy_labels
# for i in acc:
#     print i, acc[i]
file = open('valid-sent.txt')
result = open('result.txt', 'w+')

DICT_res_stat = dict()
mapping_dict = {'1': 'province', '2': 'city', '3': 'area', '4': 'town', '5': 'name', '6': 'shouji', '7': 'dianhua', '8': 'quhao', '9': 'leibie'}

total_corr = 0
total_count = 0
with open('result.txt', 'w') as o:
    for line in file:
        line = line.strip()
        line_label = line.split(',')[0]
        text = line.split(',')[1]
        c, val = new_grocery.predict(text)
        #print mapping_dict[str(c)], text

        # print c, val
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
    print mapping_dict[str(label)], 1.0 * len(DICT_res_stat[label]['correct'])/(len(DICT_res_stat[label]['error']) + len(DICT_res_stat[label]['correct'])), (len(DICT_res_stat[label]['error']) + len(DICT_res_stat[label]['correct']))
print '-' * 50
print 1.0 * total_corr / total_count