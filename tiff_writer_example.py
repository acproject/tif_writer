#!/usr/bin/env python
# -*- coding: utf-8 -*-

import numpy as np

'''
    Example 1: Build a tiff image
'''
from tif_writer.tifflib import Tiff_writer

tiff_width = 1234
tiff_height = 3456
writer = Tiff_writer(target_tiff='temp.tif',
                     tiff_width=tiff_width,
                     tiff_height=tiff_height,
                     default_val=0)
writer.write(x=0, y=0, tile=np.ones((312, 312), dtype='uint8'))
writer.write(x=512, y=0, tile=2 * np.ones((765, 234), dtype='uint8'))
writer.write(x=234, y=3000, tile=np.floor(np.random.random_sample((500, 600)) * 10).astype('uint8'))
writer.finish()

'''
    Example 2: See the result
'''
from tif_writer.slidelib import mir_based_slide
from tif_writer.plotter import see

slide = mir_based_slide().OpenSlide('temp.tif')
tile = slide.read_region(location=(0, 0), level=0)
see(tile, color_mapping=True)
