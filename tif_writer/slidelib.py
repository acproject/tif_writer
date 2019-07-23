#!/usr/bin/env python
# -*- coding: utf-8 -*-

import gc, os, time, multiprocessing
import numpy as np
import multiresolutionimageinterface as mir

'''
    This is an object that mimic openslide
    Get a new slide: slide = mir_based_slide().OpenSlide(slide_path)
    The object have properties like: level_count, level_downsamples, level_dimensions, dimensions, spacing
    The main function is to get a patch from a slide, using read_region
'''


class mir_based_slide():

    def __init__(self):
        pass

    def OpenSlide(self, slide_path):
        self.slide_path = slide_path
        self.slide = mir.MultiResolutionImageReader().open(slide_path)
        if self.slide is None:
            print('* Error while opening ' + slide_path + ' [mir_based_slide @ slidelib]')
            raise (ValueError)
        else:
            self.slide.setCacheSize(0)  # 试试加上这句能否缓解内存的问题
            self.level_count = self.slide.getNumberOfLevels()
            self.level_downsamples = [self.slide.getLevelDownsample(level) for level in range(self.level_count)]
            self.level_dimensions = [self.slide.getLevelDimensions(level) for level in range(self.level_count)]
            self.dimensions = self.level_dimensions[0]
            self.spacing = self.slide.getSpacing()
        return self

    #   读区域
    #       location：待读取位置的左上角坐标，tuple
    #       level：待进行读取的层级，int
    #       size：待读取的尺寸，tuple；若为int，则长宽一致；若留为None，则读取该level下的全尺寸
    def read_region(self, location, level, size=None, mode='lefttop', reverse_zero=False):
        #   处理location
        effective_location = (int(location[0]), int(location[1]))
        #   如果size是int，那么默认为两方向尺寸相同
        if isinstance(size, int):
            effective_size = (size, size)
        elif size is None:
            effective_size = self.level_dimensions[level]
        else:
            effective_size = (int(size[0]), int(size[1]))

        #   如果是center模式，那么起始坐标需要往左上方向偏移
        if mode == 'center':
            final_location = (int(effective_location[0] - effective_size[0] * self.level_downsamples[level] / 2),
                              int(effective_location[1] - effective_size[1] * self.level_downsamples[level] / 2))
        else:
            final_location = effective_location
        #   正常截取patch的流程
        patch = self.slide.getUCharPatch(final_location[0], final_location[1],
                                         effective_size[0], effective_size[1],
                                         level)
        if patch.shape[2] == 1:
            patch = np.repeat(patch, 3, axis=-1)  # openslide里，单通道也会读成3通道的，这里模仿一下
        #   如果需要将0转置为255，则进行该流程
        if reverse_zero:
            patch[patch == 0] = 255
            patch = patch.astype(np.uint8)
        return patch

    def close(self):
        self.slide.close()
        del self.slide_path
        del self.slide
        del self.level_count
        del self.level_downsamples
        del self.level_dimensions
        del self.dimensions
        gc.collect()



#   获取一个slide的预览图，默认会使用最低分辨率
def get_preview(slide, level=None):
    if isinstance(slide, str):
        slide = mir_based_slide().OpenSlide(slide)
        need_close = True
    else:
        need_close = False
    level = level if level is not None else (slide.level_count - 1)
    level = level if level >= 0 else (slide.level_count + level)
    downsample_rate = slide.level_downsamples[level]
    tile = np.array(slide.read_region((0, 0), level, slide.level_dimensions[level]))
    tile = tile[:, :, 0:3]
    if need_close:
        slide.close()
    return tile