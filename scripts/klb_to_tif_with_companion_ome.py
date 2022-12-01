#!/usr/bin/env python
# Generate companion files

import re
import os
import sys
import h5py
#import pyklb
    #requires pyklb (https://github.com/bhoeckendorf/pyklb); remember to install Cython and run setup.py as root, then pip install as root; get libklb.so and libklb_static.a from /tgmm-paper/build/keller-lab-block-filetype/src and copy to /usr/lib
import numpy as np
from ome_model import experimental as ome
from skimage.io._plugins import tifffile_plugin as tp
    #requires tifffile < 2022.4.22 i.e. sudo pip3 install tifffile==2022.4.8

FORMAT = "t(\d+)_s(\d+)\."
c_names = ["GFP-Smarcd3-F6","RFP-Mesp1_lineage"]
#UNIT = "microns"
UNIT = ["microns","µm"]
XY_RES = 0.380490284561
Z_RES = 4 * XY_RES
BASE_DIRECTORY = "/Users/dom/idr/Dominguez/sample" #os.getcwd()

SIZE_T = 1
SIZE_C = 1
MAX_C = 0
c_array = []

OUTPUT_DIR = BASE_DIRECTORY

if ( len(sys.argv) == 3 and len(sys.argv[2]) ) > 1: #with two arguments, first in input directory, second is output
    OUTPUT_DIR = sys.argv[2]
    BASE_DIRECTORY = sys.argv[1]
elif ( len(sys.argv) == 2 and len(sys.argv[1]) ) > 1: #with one argument, it is the output directory, assuming pwd is input
    OUTPUT_DIR = sys.argv[1]



#convert klb's to tif's in the base directory
# for root, dirs, files in os.walk(BASE_DIRECTORY):
#     for filename in files:
#         if re.search(FORMAT+"klb",filename): #( filename.endswith("00.h5") or filename.endswith("01.h5") ):
#             filename_root, file_extension = os.path.splitext(filename)
#
#             file_to_modify = filename
#             print( "Exporting TIF from file", file_to_modify)
#
#             image = pyklb.readfull(BASE_DIRECTORY + "/" + filename)
#             shape = image.shape
#             print(  shape)
#             tp.imsave(BASE_DIRECTORY + "/" + filename_root + ".tif", image.reshape(shape[0],1,shape[1],shape[2]), compress=6, resolution=(1./XY_RES,1./XY_RES), imagej=True, metadata={'spacing': Z_RES,'unit': UNIT[0]} )


#print("Generate companions from klb. Arguments: ", str(sys.argv))



os.makedirs(OUTPUT_DIR, exist_ok=True)
IMAGE_NAME = os.path.split(BASE_DIRECTORY)[-1]

image_files = os.listdir(BASE_DIRECTORY)
first_file = ""

for file in image_files:
    if match := re.search(FORMAT+"tif", file, re.IGNORECASE):
        if len(first_file) == 0:
            first_file = file
        t_index = int(match.group(1))
        c_index = int(match.group(2))
        c_array.append( c_index )
        SIZE_T = max(t_index + 1, SIZE_T)
c_array = np.unique ( c_array ).tolist()

SIZE_C = len(c_array)

#PhysicalSizeX="1.031" PhysicalSizeY="1.031" PhysicalSizeZ="5"
# <Pixels DimensionOrder="XYCZT" ID="Pixels:0:0" PhysicalSizeX="1.031" PhysicalSizeY="1.031" PhysicalSizeZ="5" SizeC="1" SizeT="1" SizeX="512" SizeY="512" SizeZ="91" Type="uint16">

#first image establishes XZY dim
img = tp.imread(BASE_DIRECTORY+"/"+first_file)
dim_ZXY = img.shape

companion = ome.Image(IMAGE_NAME, dim_ZXY[2], dim_ZXY[1], dim_ZXY[0], SIZE_C,
    sizeT=SIZE_T, order='XYZCT', type='uint8', physSizeX = XY_RES, physSizeY = XY_RES,
    physSizeZ = Z_RES, physSizeZUnit = UNIT[1], physSizeYUnit = UNIT[1], physSizeXUnit = UNIT[1] )
for chan_num in c_array:
    companion.add_channel(name=c_names[chan_num], samplesPerPixel=1)

for file in image_files:
    file = file.strip()
    if match := re.search(FORMAT+"tif", file, re.IGNORECASE):
        t_index = int(match.group(1))
        c_index = int(match.group(2))
        companion.add_tiff(file, c=c_array.index(c_index), t=t_index, planeCount=dim_ZXY[0])

companion_file = OUTPUT_DIR+"/"+IMAGE_NAME+".companion.ome"
if os.path.exists(companion_file):
    os.remove(companion_file)

with open(companion_file, 'wb') as o:
    ome.create_companion(images=[companion], out=o)
