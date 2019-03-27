# -*-coding:utf-8-*-
with open('./t.txt', 'r') as f:
    a = f.readline()
with open('./t2.txt', 'r') as o:
    b = o.readline()
with open('./t3.txt', 'w') as f3:
    f3.write(u'上 海 浦 东 新 区 南 汇 宣 桥 镇 宣 桥 枫 庭 1 9 5 5 弄 5 号 4 0'.encode('utf-8'))
with open('./t3.txt', 'r') as o:
    c = o.readline()
for i in range(81):
    if a[i+3] == c[i]:
        continue
    else:
        print i
print(a[0:3])
print(a)
print(b)
print(c)



