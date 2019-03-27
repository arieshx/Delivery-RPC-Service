#coding=utf-8
import codecs
import random

all = codecs.open('all.txt', 'w', 'utf-8')

#province = codecs.open('province.txt', 'r', 'utf-8')#1
#city = codecs.open('city.txt', 'r', 'utf-8')#2
address = codecs.open('address.txt', 'r', 'utf-8').readlines()#3
town = codecs.open('town.txt', 'r', 'utf-8').readlines()#4
name = codecs.open('name.txt', 'r', 'utf-8').readlines()#5
shouji = codecs.open('shouji.txt', 'r', 'utf-8').readlines()#6
dianhua = codecs.open('dianhua1.txt', 'r', 'utf-8').readlines()#7
#number = codecs.open('number.txt', 'r', 'utf-8')#8
leibie = codecs.open('leibie2.txt', 'r', 'utf-8').readlines()#9
'''
for line in province:
    all.write('1' + '\t' + line.strip() + '\n')
for line in city:
    all.write('2' + '\t' + line.strip() + '\n')
for line in area:
    all.write('3' + '\t' + line.strip() + '\n')
'''
'''
for line in address:
    all.write('3' + '\t' + line.strip() + '\n')
for line in town:
    all.write('4' + '\t' + line.strip() + '\n')
for line in name:
    all.write('5' + '\t' + line.strip() + '\n')
for line in shouji:
    all.write('6' + '\t' + line.strip() + '\n')
for line in dianhua:
    all.write('7' + '\t' + line.strip() + '\n')
#for line in number:
#    all.write('8' + '\t' + line.strip() + '\n')
for line in leibie:
    all.write('9' + '\t' + line.strip() + '\n')
'''
random.shuffle(address)
random.shuffle(town)
random.shuffle(name)
random.shuffle(shouji)
random.shuffle(dianhua)
random.shuffle(leibie)
for line in address[:1500]:
    all.write('3' + '\t' + line.strip() + '\n')
for line in town[:1500]:
    all.write('4' + '\t' + line.strip() + '\n')
for line in name[:1500]:
    all.write('5' + '\t' + line.strip() + '\n')
for line in shouji[:1500]:
    all.write('6' + '\t' + line.strip() + '\n')
for line in dianhua[:1500]:
    all.write('7' + '\t' + line.strip() + '\n')
#for line in quhao:
#    all.write('8' + '\t' + line.strip() + '\n')
for line in leibie[:1500]:
    all.write('9' + '\t' + line.strip() + '\n')



