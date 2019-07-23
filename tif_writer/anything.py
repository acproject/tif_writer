# !/usr/bin/env python
# -*- coding: utf-8 -*-

import numpy as np

#   输入图像路径/数据矩阵，返回数据矩阵
def anything_as_ndarray(input):
    if isinstance(input, str):
        #   如果是图像路径，则读取数据返回
        from .files import imread
        data = imread(input)
        return data
    elif isinstance(input, list):
        #   如果是一个list，则用numpy转化为numpy数组返回
        print('warning: list transfer to ndarray')
        return np.array(input)
    elif isinstance(input, np.ndarray):
        #   如果本来就是一个ndarray，直接返回
        return input
    else:
        print('Unrocognized object')
        raise ValueError