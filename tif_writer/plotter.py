#!/usr/bin/env python
# -*- coding: utf-8 -*-

import numpy as np
from copy import deepcopy


# 以图像的方式对数据矩阵进行可视化
#   如果设置rescale为True，则将自动归一化到0~255，否则将以原始数据展示
def see(datamat, color_mapping=False, title=None, new_figure=True, show=True):
    import numpy as np
    import matplotlib.pyplot as plt
    if not isinstance(datamat, np.ndarray):
        datamat = np.array(datamat)
    try:
        if color_mapping:
            datamat = _mask_to_color(datamat)
        if new_figure:
            plt.figure()
        if len(datamat.shape) == 2:
            plt.imshow(np.squeeze(datamat), plt.cm.gray)
        else:
            plt.imshow(np.squeeze(datamat))
        if title is not None:
            plt.title(title)
        if show:
            plt.show()
    except:
        print('* Error happens during visualization')


#   把mask转化为彩色的图像~
#   当需要观察特定数值的区域时，将target_value设置为对应值，符合的区域将以白色显示
def _mask_to_color(datamat, target_value=None):
    import numpy as np
    from .imgprocessing.basic import imsqueeze, get_rgb_table
    if len(datamat.shape) == 3:
        mask = imsqueeze(datamat)
    else:
        mask = datamat
    rgb_table = get_rgb_table()
    mask_color = rgb_table[mask.astype(np.int)]
    if target_value is not None:
        for i in range(3):
            original_channel = datamat[:, :, i]
            colored_channel = mask_color[:, :, i]
            colored_channel[original_channel == target_value] = 255
            mask_color[:, :, i] = colored_channel
    return mask_color.astype(np.uint8)


#   将多个slide_patch与mask_patch绘制在同一窗口
def see_pairs(slide_patches, mask_patches, target_value=None):
    #   处理送进来的不是list的情况
    if not isinstance(slide_patches, list):
        slide_patches = [slide_patches]
    if not isinstance(mask_patches, list):
        mask_patches = [mask_patches]
    pair_amount = len(slide_patches)
    import matplotlib.pyplot as plt
    plt.figure()
    for pair_id in range(pair_amount):
        plt.subplot(pair_amount, 2, 2 * pair_id + 1)
        slide_patch = slide_patches[pair_id]
        see(slide_patch, new_figure=False, show=False)
        plt.subplot(pair_amount, 2, 2 * pair_id + 2)
        mask_patch = mask_patches[pair_id]
        mask_patch_color = _mask_to_color(mask_patch, target_value=target_value)
        include_class = np.unique(mask_patch)
        see(mask_patch_color, new_figure=False, show=False, title=str(include_class))
    plt.show()