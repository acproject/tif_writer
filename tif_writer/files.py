# !/usr/bin/env python
# -*- coding: utf-8 -*-
import os
from .imgprocessing.basic import imread


#   获取纯文件名
def purename(path):
    return os.path.splitext(os.path.basename(path))[0]
