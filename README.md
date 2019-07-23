# tif_writer
A tool for saving multi-resolution-image

tif格式常用于数字病理图像的储存(有时也称whole-slide-image, WSI)，其本质是一个经过压缩的多分辨率的图像。目前在数字病理领域已开展了许多竞赛，例如Camelyon16[1], Camelyon17[2], ACDC Lung Cancer[3]等，得到了现代机器学习领域研究者的广泛关注。作为一个刚刚接触该领域的人，我感到在数据的读取和保存方面有着诸多的不便。虽然已经有openslide[4]以及ASAP[5]等优秀的库，但在结果的保存方面(对我)仍然是一个困扰。因此我将部分代码分享出来，希望能够帮助新接触tif多分辨率图像文件的人。

本代码主要基于ASAP的多分辨率图像接口（multiresolutionimageinterface），在使用之前需要先安装ASAP，并将ASAP安装目录下的bin文件夹添加到用户变量“PYTHONPATH”中。[6]是关于multiresolutionimageinterface的一份非常棒的教程，事实上在编写本代码的过程中，大部分内容也参考了[6]。但在使用multiresolutionimageinterface的过程中，我发现有一些细节并未完全地阐述，导致了保存的tif文件出现错位甚至保存失败的情况。因此阐述更详细的细节，并提供更便于使用的接口成为了这份代码的初衷。

尽管如此，我们仍然推荐尽量使用原始的multiresolutionimageinterface。为此分享一些实际使用中的细节：
1. writer.setTileSize(TileSize) 指定了每次写入数据的大小，该设置是一次性的，无法更改。也就是说，不能够在某个位置写入一个(512,512)的块，再在另一个位置写入(256,256)的块。
2. TileSize必须是2的指数，并且不能小于16，否则会报错。
3. writer.writeBaseImagePart()函数的逻辑是从左到右，从上到下依次按TileSize的大小写入。如果遇到宽度不能被TileSize整除的情况，在边界时，仍然需要送入TileSize大小的数据。在写完该块后，位置会自动置于下一个TileSize行，不会因为边界的不能整除而偏移。
4. 我们更推荐使用writer.writeBaseImagePartToLocation(tile,x,y)方法，它可以避免writeBaseImagePart不能灵活切换位置的不变，但TileSize的限制仍然适用。当x,y不是TileSize的整数倍时，坐标会被向下取为整数倍，因此本质上并没有解决自由写入的问题。

在本份代码中，Tiff_writer对象会创建一个临时的hdf5文件用于存储中间数据，以便反复写入。在创建后，即可通过write(x, y, tile)方法写入数据。位置x和y是自由的，当越界时会自动截断。tile是一个正常的nxm的uint8型ndarray，不需要flatten，所需的空间会通过tile的尺寸自动推断。可以在tiff_writer_example.py中找到一个简单的例子。

[1] https://camelyon16.grand-challenge.org

[2] https://camelyon17.grand-challenge.org

[3] https://acdc-lunghp.grand-challenge.org

[4] https://openslide.org/

[5] https://computationalpathologygroup.github.io/ASAP/

[6] Litjens, Geert, et al. "1399 H&E-stained sentinel lymph node sections of breast cancer patients: the CAMELYON dataset." GigaScience 7.6 (2018): giy065.

Format 'tif' is widly used in digital pathology image storage(sometimes also referred as whole-slide-image, WSI), whose essence is a compressed multi-resolution image. There were many challanges held in digital pathology field, such as Camelyon16[1], Camelyon17[2], ACDC Lung Cancer[3], drawing widely attention from modern machine learning researchers. As a beginner, I felt a little bit inconvenience for reading and writing tif files. Despite excellent library like openslide[4] and ASAP[5] have been released, it still a trouble for me to save the result properly. Due to these reason, I released part of my code, hopefully it may help beginner on multi-resolution images.

These codes mainly based on multiresolutionimageinterface(mir) of ASAP. You need to install ASAP, and include the 'bin' path to user environment variable "PYTHONPATH". [6] is a wonderful tutorial about mir, actually, most of my code referred to [6]. However, during working with mir, I found some details were not completely described, which may cause dislocation or even failure while saving the result. So better details and a more convenient interface become the intuition of this repository.

Despite this, I would still recommand using original mir, since it is an official software and definately more stable than mine. For such, some details provided as following:
1. writer.setTileSize(TileSize) set the size of data each time you write. This can be set only one time, and can not change afterwards. That is to say, you can not write a (512,512) patch, and then write a (256,256) patch.
2. TileSize must be an exponent of 2 and cannot be less than 16, otherwise an error will raised.
3. writer.writeBaseImagePart() will write data of size {TileSize} in a "left to right, then top to bottom" way. If the width can not be divisible by {TileSize}, it will be chopped automatically, but you still need to input a tile of size {TileSize}. After writing this tile, the location will move to next row of {TileSize}. It won't shifted due to indivisible issue.
4. I would prefer writer.writeBaseImagePartToLocation(tile,x,y) method rather than writeBaseImagePart(), since the location has more freedom. However, the restrict of {TileSize} still exist. If x or y is not an integer multiple of {TileSize}, they will be 'floored'. So in principle, it is not completely free.

In this repository, Tiff_writer object will create a temporary 'hdf5' file for save intermediate data, to enable free/repeatable writing. After creation, you can write data via method: write(x, y, tile). Location x and y is compeletly of freedom, data will be chopped automatically when exceeding boundary. 'tile' is a 'ndarray' of type 'uint8', you don't need to flatten it. The required space will be inferred from tile.shape. You can find a simple example in tiff_writer_example.py.
