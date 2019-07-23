#!/usr/bin/env python
# -*- coding: utf-8 -*-
#   Monitor主要实现对任务的监控和管理
import os

#   在终端显示进度条
def terminal_viewer(current, total, head="Percent: ", tail="", interval=0):
    import sys
    bar_length = 60
    percent = current / total
    hashes = '#' * int(percent * bar_length)
    spaces = ' ' * (bar_length - len(hashes))
    if interval == 0 or int(current * 100 / total) % interval == 0:
        sys.stdout.write("\r%s[%s] %d%% %d/%d %s"
                         % (head, hashes + spaces, percent * 100, current, total, tail))
        sys.stdout.flush()