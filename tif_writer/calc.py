#!/usr/bin/env python
# -*- coding: utf-8 -*-

import numpy as np

#   送入的数据构成一个list，返回的是那些处于同位置各数据源均非nan的数据
def filter_nan(data_list):
    if not isinstance(data_list, list):
        data_list = [data_list]
    datalength = len(data_list[0])
    invalid_flag = np.zeros(datalength, dtype=np.bool)
    for data in data_list:
        invalid_flag = np.logical_or(invalid_flag, np.isnan(data))
    valid_flag = np.logical_not(invalid_flag)
    result_list = []
    for data in data_list:
        new_data = data[valid_flag]
        result_list.append(new_data)
    return result_list