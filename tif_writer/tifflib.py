# !/usr/bin/env python
# -*- coding: utf-8 -*-

import h5py
import numpy as np
import os
import sys

'''Used for writing tif file'''


#   初始化参数：
#       target_tiff: 目标tiff路径
#       tiff_width: 目标tiff的宽度
#       tiff_height: 目标tiff的高度
#       default_val: tiff的初始值，默认0
#       write_tile_size: 最终写tiff时使用的块大小，默认为512
#       chunk_size: 暂存数据的大小，默认1024
#   方法：
#       write(x, y, tile)：以位置(x, y)为左上角，写入一个任意大小的tile
#       write_center(x, y, tile)：以位置(x, y)为中心，写入一个任意大小的tile
#       finish()：完成所有数据的写入后，调用该命令生成最终的tiff文件

#   Initialization:
#       target_tiff: the path for saving tif file
#       tiff_width: the width of the tif file
#       tiff_height: the height of the tif file
#       default_val: initial value of all pixels in tif file, default = 0
#       write_tile_size: TileSize used in mir.writer, you can leave this as default
#       chunk_size: chunk size for building hdf5 file, you can leave this as default
#   Method:
#       write(x, y, tile): write a tile at location (x,y) (top left coordinates), tile: 2-d uint8 ndarray of arbitary size
#       write(x, y, tile): write a tile at location (x,y) (center coordinates), tile: 2-d uint8 ndarray of arbitrary size
#       finish(): when all data has been writen, call this to obtain final tif file.
class Tiff_writer():
    def __init__(self, target_tiff, tiff_width, tiff_height,
                 default_val=0,
                 spacing=None,
                 write_tile_size=512, chunk_size=1024):
        self.target_tiff = target_tiff
        self.tiff_width = tiff_width
        self.tiff_height = tiff_height
        self.default_val = default_val
        self.spacing = spacing

        def get_2_base(num):
            power = 1
            while num / power >= 1:
                power = power * 2
            return int(power / 2)

        if write_tile_size is not None:
            #   要求tile_size必须为2的次方，如果不是，就向下找到最接近的
            write_tile_size = get_2_base(write_tile_size)

        #   检查write_tile_size是否过小
        if write_tile_size < 16:
            print('tile size must larger than 16 restricted by mir')
            raise ValueError

        self.write_tile_size = write_tile_size

        self.chunk_size = get_2_base(chunk_size)

        if self.chunk_size < self.write_tile_size:
            #   这样子可以保证写数据时，只需要从某一个chunk上读
            print('write_tile_size must not larger than chunk_size')
            raise ValueError

        self.horizontal_chunk_amount = int(np.ceil(tiff_width / chunk_size))
        self.vertical_chunk_amount = int(np.ceil(tiff_height / chunk_size))

        from .files import purename

        hdf5name = purename(target_tiff) + '_temp.hdf5'
        self.hdf5name = hdf5name
        if os.path.isfile(hdf5name):
            os.remove(hdf5name)

        print('initializing hdf5 data structure ...')
        sys.stdout.flush()
        self.__hdf5file_init(hdf5name)

    #   初始化中间的hdf5文件
    #   在根目录下创建了适当数目的group
    #   在根目录下创建了'accessed'数据集，对应每个group是否被访问过，初始化全为False
    def __hdf5file_init(self, hdf5name):
        f = h5py.File(hdf5name)
        #   为每一个子区域创建一个group，同时在母数据集上设置一个标记矩阵，表示每个区域是否被改动
        f.create_dataset(name='accessed', dtype=bool,
                         data=np.zeros((self.vertical_chunk_amount, self.horizontal_chunk_amount), dtype=bool))
        for x in range(self.horizontal_chunk_amount):
            for y in range(self.vertical_chunk_amount):
                sub_group = f.create_group(str(x) + '_' + str(y))
        f.close()  # 先保存下来
        f = h5py.File(hdf5name, 'r+')  # 然后再打开
        self.f = f

    #   只有当必要的时候，才对一个group进行初始化
    def __subgroup_init(self, sub_group):
        chunk_default_data = (np.ones((self.chunk_size, self.chunk_size)) * self.default_val).astype(np.uint8)
        sub_group.create_dataset('value', dtype='uint8', data=chunk_default_data)

    #   给定一个chunk的坐标范围，以及一个区域(x_lb,y_lb)~(x_ub,y_ub)，返回交叉区域在各自上的相对位置
    def __find_relative_location(self, chunk_x_lb, chunk_y_lb, chunk_x_ub, chunk_y_ub,
                                 x_lb, y_lb, x_ub, y_ub):
        #   首先返回交叉区域的绝对坐标
        cross_x_lb_absolute = max(chunk_x_lb, x_lb)
        cross_y_lb_absolute = max(chunk_y_lb, y_lb)
        cross_x_ub_absolute = min(chunk_x_ub, x_ub)
        cross_y_ub_absolute = min(chunk_y_ub, y_ub)
        #   再返回交叉区域对于chunk的相对坐标
        cross_x_lb_relative_chunk = int(cross_x_lb_absolute - chunk_x_lb)
        cross_y_lb_relative_chunk = int(cross_y_lb_absolute - chunk_y_lb)
        cross_x_ub_relative_chunk = int(cross_x_ub_absolute - chunk_x_lb)
        cross_y_ub_relative_chunk = int(cross_y_ub_absolute - chunk_y_lb)
        #   再计算交叉区域对于x的相对坐标
        cross_x_lb_relative_tile = int(cross_x_lb_absolute - x_lb)
        cross_y_lb_relative_tile = int(cross_y_lb_absolute - y_lb)
        cross_x_ub_relative_tile = int(cross_x_ub_absolute - x_lb)
        cross_y_ub_relative_tile = int(cross_y_ub_absolute - y_lb)
        return (cross_x_lb_relative_chunk, cross_x_ub_relative_chunk, cross_y_lb_relative_chunk,
                cross_y_ub_relative_chunk), \
               (cross_x_lb_relative_tile, cross_x_ub_relative_tile, cross_y_lb_relative_tile,
                cross_y_ub_relative_tile)

    #   以x,y位置为左上角，写入一批数据tile
    def write(self, x, y, tile, save=False):
        f = self.f

        chunk_size = self.chunk_size

        tile_shape = tile.shape

        x_lb = x
        x_ub = x + tile_shape[1]  # 坐标上界，不包含
        y_lb = y
        y_ub = y + tile_shape[0]

        x_chunk_lb = int(max(np.floor(x_lb / chunk_size), 0))
        y_chunk_lb = int(max(np.floor(y_lb / chunk_size), 0))
        x_chunk_ub = int(min(np.floor((x_ub - 1) / chunk_size), self.horizontal_chunk_amount - 1))
        y_chunk_ub = int(min(np.floor((y_ub - 1) / chunk_size), self.vertical_chunk_amount - 1))

        for x_chunk_id in range(x_chunk_lb, x_chunk_ub + 1):
            for y_chunk_id in range(y_chunk_lb, y_chunk_ub + 1):
                #   这是这个chunk的四个边界(绝对坐标)
                this_chunk_x_lb = x_chunk_id * chunk_size
                this_chunk_x_ub = this_chunk_x_lb + chunk_size  # 不包含
                this_chunk_y_lb = y_chunk_id * chunk_size
                this_chunk_y_ub = this_chunk_y_lb + chunk_size
                #   获得所需的范围
                (cross_x_lb_relative_chunk, cross_x_ub_relative_chunk, cross_y_lb_relative_chunk,
                 cross_y_ub_relative_chunk), \
                (cross_x_lb_relative_tile, cross_x_ub_relative_tile, cross_y_lb_relative_tile,
                 cross_y_ub_relative_tile) \
                    = self.__find_relative_location(this_chunk_x_lb, this_chunk_y_lb, this_chunk_x_ub, this_chunk_y_ub,
                                                    x_lb, y_lb, x_ub, y_ub)

                #   检查数据的情况，如果用户试图在写默认块，而且该位置尚未初始化，则什么都不做
                sub_tile = tile[cross_y_lb_relative_tile:cross_y_ub_relative_tile,
                           cross_x_lb_relative_tile:cross_x_ub_relative_tile]

                #   检查该组是否已被创建，如果尚未创建，则进行创建
                group_name = str(x_chunk_id) + '_' + str(y_chunk_id)
                if not f['accessed'][y_chunk_id, x_chunk_id]:
                    if (sub_tile == self.default_val).all():
                        continue
                    self.__subgroup_init(f[group_name])
                    f['accessed'][y_chunk_id, x_chunk_id] = True

                #   读取现有数据
                value = f[str(x_chunk_id) + '_' + str(y_chunk_id)]['value']

                #   改写数据
                value[cross_y_lb_relative_chunk:cross_y_ub_relative_chunk,
                cross_x_lb_relative_chunk:cross_x_ub_relative_chunk] = sub_tile
        if save:
            self.f.close()  # 先保存下来
            f = h5py.File(self.hdf5name)  # 再打开
            self.f = f

    #   以x,y位置为中心，写入一批数据
    def write_center(self, x, y, tile, save=False):
        h, w = tile.shape

        def get_shift(s):
            return int(np.floor((s - 1) / 2))

        x_lt = x - get_shift(w)
        y_lt = y - get_shift(h)
        self.write(x_lt, y_lt, tile, save)

    #   完成数据构建，生成最终的tiff文件，默认情况下删除临时的hdf5文件
    def finish(self, free=True):

        #   首先把文件关闭保存数据，再重新打开
        self.f.close()  # 先保存下来
        f = h5py.File(self.hdf5name, 'r')  # 然后以只读方式打开

        import multiresolutionimageinterface as mir
        writer = mir.MultiResolutionImageWriter()
        writer.openFile(self.target_tiff)
        self.write_tile_size = self.chunk_size  # 用新的程序，直接写每个chunk就行了
        writer.setTileSize(self.write_tile_size)
        writer.setCompression(mir.LZW)
        writer.setDataType(mir.UChar)
        writer.setInterpolation(mir.NearestNeighbor)
        writer.setColorType(mir.Monochrome)
        writer.writeImageInformation(self.tiff_width, self.tiff_height)
        if self.spacing is not None:
            spacing_vec = mir.vector_double()
            spacing_vec.push_back(float(self.spacing))
            spacing_vec.push_back(float(self.spacing))
            writer.setSpacing(spacing_vec)

        print('start writing tiff file {} ...'.format(self.target_tiff))
        print('   width: {}, height: {}, default value: {}'.format(self.tiff_width, self.tiff_height, self.default_val))
        print('   write tile size: {}, chunk size: {}'.format(self.write_tile_size, self.chunk_size))
        sys.stdout.flush()

        #   新的程序
        for chunk_x in range(self.horizontal_chunk_amount):
            for chunk_y in range(self.vertical_chunk_amount):
                if not f['accessed'][chunk_y, chunk_x]:  # 注：在上面的设定中，accessed是矩阵形式的，它的x和y和坐标是反的
                    continue
                group_name = str(chunk_x) + '_' + str(chunk_y)
                value = f[group_name]['value']
                writer.writeBaseImagePartToLocation(np.array(value).flatten(), chunk_x * self.chunk_size,
                                                    chunk_y * self.chunk_size)

        # #   以前的程序，适用于尺寸很正常的tiff
        # x_steps = int(self.tiff_width / self.write_tile_size)
        # y_steps = int(self.tiff_height / self.write_tile_size)
        #
        # default_block_flatten = (self.default_val * np.ones(shape=(self.write_tile_size, self.write_tile_size))).astype(
        #     np.uint8).flatten()
        # current = 0
        # total = y_steps * x_steps
        # from .monitor import terminal_viewer
        # for y_step in range(y_steps):
        #     for x_step in range(x_steps):
        #         current += 1
        #         terminal_viewer(current, total)
        #         #   计算是哪一个chunk
        #         chunk_x = int(x_step * self.write_tile_size / self.chunk_size)
        #         chunk_y = int(y_step * self.write_tile_size / self.chunk_size)
        #         #   若该chunk未被访问过，直接写默认块
        #         if not f['accessed'][chunk_y, chunk_x]:
        #             writer.writeBaseImagePart(default_block_flatten)
        #             continue
        #         group_name = str(chunk_x) + '_' + str(chunk_y)
        #         value = f[group_name]['value']
        #         #   计算在该chunk中的起始坐标
        #         this_tile_x_lb = x_step * self.write_tile_size - chunk_x * self.chunk_size
        #         this_tile_y_lb = y_step * self.write_tile_size - chunk_y * self.chunk_size
        #         this_tile_value = value[this_tile_y_lb:this_tile_y_lb + self.write_tile_size,
        #                           this_tile_x_lb:this_tile_x_lb + self.write_tile_size]
        #         #   准备数据
        #         writer.writeBaseImagePart(this_tile_value.flatten())
        f.close()
        writer.finishImage()
        if free:
            self.free()

    #   删除存储的中间hdf5文件
    def free(self):
        try:
            os.remove(self.hdf5name)
        except:
            print('error happen while cleaning intermedia hdf5 file')


'''
    Used for build a tif file from an existed image
    e.g. You use otsu to get a foreground mask at lower resolution, now you want to enlarge it to the same size as original slide
'''
#   Inputs:
#       image: Path of an image or ndarray
#       target_tiff: Path of the target tif file
#       expand_rate: The amplification. For example, you generate mask at level 5, then it should be 32 to match slide at level 0
#       spacing: The spacing of generated tif, not important if you don't use spacing property of a slide
#       assigned_height: The target height can be calculated by image.height * expand_rate, but you can set this manually in case of indivisible issue
#       assigned_height: Similar as "assigned_height"
#       show_process: Do you want to show a process bar in the terminal?
#       tile_size: Just leave it as default.

def build_tif_from_image(image, target_tiff, expand_rate=1,
                         spacing=None, assigned_height=None, assigned_width=None,
                         show_process=False, tile_size=512):
    expand_rate = int(expand_rate)
    from .anything import anything_as_ndarray
    from .imgprocessing.basic import imsqueeze, imrescale
    data = imsqueeze(anything_as_ndarray(image))
    image_height, image_width = data.shape
    target_height = int(image_height * expand_rate) if assigned_height is None else assigned_height
    target_width = int(image_width * expand_rate) if assigned_width is None else assigned_width
    writer = Tiff_writer(target_tiff, target_width, target_height, spacing=spacing, write_tile_size=tile_size)
    writer_tile_size = writer.write_tile_size
    image_step_size = int(
        max(int(np.round(writer_tile_size / expand_rate)), 1))  # 在原图像上每次移动的距离，256对应Tiff_writer里的write_tile_size
    #   例如，每次移动32，放大8倍，就成了256的大小了
    #   这里的坐标是在最终的大tiff上的
    print('writing image data ...')
    sys.stdout.flush()
    current = 0
    total = target_height * target_width / (writer_tile_size ** 2)

    from .monitor import terminal_viewer
    for y in range(0, target_height, writer_tile_size):
        for x in range(0, target_width, writer_tile_size):
            current += 1
            if show_process:
                terminal_viewer(current, total)
            #   首先回溯到原来的小图上
            x_small = int(x / expand_rate)
            y_small = int(y / expand_rate)
            #   截出所需要的大小
            y_ub = min(y_small + image_step_size, image_height)
            x_ub = min(x_small + image_step_size, image_width)
            patch = data[y_small:y_ub, x_small:x_ub].astype(np.uint8)
            if not np.any(patch):
                continue
            patch_expand = imrescale(patch, scale=expand_rate, hard=True)
            writer.write(x, y, patch_expand)
    writer.finish()
    pass
