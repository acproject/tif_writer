#!/usr/bin/env python
# -*- coding: utf-8 -*-

import numpy as np
from PIL import Image

#   打开一个图像文件，并读入数据
def imread(img_path):
    return np.array(Image.open(img_path))

#   搞这么麻烦，是因为不想在对三维图缩放的时候，把第三维也缩放了……
def imrescale(img, scale, hard=False):
    target_width = int(np.round(img.shape[1] * scale))
    target_height = int(np.round(img.shape[0] * scale))
    return imrescale_to_shape(img, (target_width, target_height), hard=hard)

#   把图像缩放到指定尺寸(使用线性插值，会产生过度)
def imrescale_to_shape(img, target_shape, hard=False):
    # img_shape = img.shape
    # final_scale = np.ones_like(img_shape).astype(np.double)
    # final_scale[0] = target_shape[0] / img_shape[0]
    # final_scale[1] = target_shape[1] / img_shape[1]
    # return scipy_ndi_int_zoom(img, final_scale, order=1, mode='nearest')
    #   使用Image库进行缩放会比ndimage快四五百倍，应注意的是resize方法的参数是(缩放后的宽,缩放后的高)
    img = Image.fromarray(img)
    if isinstance(target_shape, int):
        target_shape = (target_shape, target_shape)
    if hard:
        return np.array(img.resize((target_shape[1], target_shape[0]), Image.NEAREST))
    else:
        return np.array(img.resize((target_shape[1], target_shape[0]), Image.BILINEAR))



#   把一个图像从3维变为2维（取首个维度），如果本来就是二维，直接返回
def imsqueeze(img):
    if len(img.shape) == 3:
        return img[:, :, 0]
    else:
        return img

#   定义一些具有显著差别的颜色
#   参考：https://sashat.me/2017/01/11/list-of-20-simple-distinct-colors/
def get_rgb_table():
    rgb_table = [
        [0, 0, 0],
        [0, 130, 200],
        [128, 0, 0],
        [0, 0, 128],
        [245, 130, 48],
        [250, 190, 190],
        [230, 190, 255],
        [255, 255, 25],
        [170, 110, 40],
        [230, 25, 75],
        [0, 128, 128],
        [60, 128, 75],
        [70, 240, 240],
        [240, 50, 230],
        [255, 250, 200],
        [170, 255, 195],
        [128, 128, 0],
        [210, 245, 60],
        [145, 30, 180],
        [255, 215, 180]
    ]
    #   后面再多，就用随机的颜色了
    rgb_table = np.concatenate([rgb_table, np.floor(256 * np.random.random_sample((255 - len(rgb_table), 3)))])
    return np.array(rgb_table)
