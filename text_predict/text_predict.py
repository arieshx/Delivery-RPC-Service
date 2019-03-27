#coding=utf-8
from tgrocery import Grocery

text_model = Grocery('all_no_town')
text_model.load()
#输入文本，预测出class_name和class_prob
def predict(text):
    c = text_model.predict(' '.join(list(text)))
    class_name = str(c)
    class_prob = c.dec_values[class_name]
    return class_name, class_prob
print predict(u'100')