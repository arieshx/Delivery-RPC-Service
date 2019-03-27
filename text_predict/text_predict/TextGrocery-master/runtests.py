# coding: utf-8

import unittest
import os
import shutil

from tgrocery import Grocery


train_src = [
    ('education', '我和你'),
    ('education', '你和我')
]
grocery_name = 'test'

grocery = Grocery(grocery_name)
grocery.train(train_src)
grocery.save()
new_grocery = Grocery('test')
new_grocery.load()
print '-' * 50
print grocery.predict('考生必读：新托福写作考试评分标准')
#assert grocery.get_load_status()
#assert grocery.predict('考生必读：新托福写作考试评分标准') == 'education'
# cleanup
#if grocery_name and os.path.exists(grocery_name):
#    shutil.rmtree(grocery_name)
