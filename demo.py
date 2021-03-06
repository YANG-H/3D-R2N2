'''
Demo code for the paper

Choy et al., 3D-R2N2: A Unified Approach for Single and Multi-view 3D Object
Reconstruction, ECCV 2016
'''
import os
import sys
if (sys.version_info < (3, 0)):
    raise Exception("Please follow the installation instruction on 'https://github.com/chrischoy/3D-R2N2'")

import shutil
import numpy as np
from subprocess import call

from PIL import Image
from models import load_model
from lib.config import cfg, cfg_from_list
from lib.solver import Solver
from lib.voxel import voxel2obj, voxel2text

DEFAULT_WEIGHTS = 'output/ResidualGRUNet/default_model/weights.npy'


def cmd_exists(cmd):
    return shutil.which(cmd) is not None


def download_model(fn):
    if not os.path.isfile(fn):
        # Download the file if doewn't exist
        print('Downloading a pretrained model')
        call(['curl', 'ftp://cs.stanford.edu/cs/cvgl/ResidualGRUNet.npy',
              '--create-dirs', '-o', fn])


def load_input_images(d, maxn=0):
    ims = []
    for fname in os.listdir(d):
        if maxn > 0 and len(ims) >= maxn:
            break
        fullname = os.path.join(d, fname)
        try:
            print(fullname)
            im = Image.open(fullname)
            im = im.resize((127, 127), resample=Image.ANTIALIAS)
            npy = np.array(im)
            print(npy.shape)
            if npy.shape[2] == 4:
                print('rgba->rgb')
                r, g, b, a = np.rollaxis(npy, axis=-1)
                r[a < 10] = 255
                g[a < 10] = 255
                b[a < 10] = 255
                npy = np.dstack([r, g, b])
            npy = npy.transpose((2, 0, 1)).astype(np.float32) / 255.
            ims.append([npy])
        except OSError:
            pass 
    return np.array(ims)


def main():
    '''Main demo function'''
    input_dir = sys.argv[1] if len(sys.argv) > 1 else './input/chair1'
    input_num = int(sys.argv[2]) if len(sys.argv) > 2 else 0

    # Save prediction into a file named 'prediction.obj' or the given argument
    pred_file_name = sys.argv[3] if len(sys.argv) > 3 else 'prediction.obj'
    pred_txt_file_name = sys.argv[4] if len(sys.argv) > 4 else 'prediction.txt'

    # load images
    demo_imgs = load_input_images(input_dir, input_num)
    print(demo_imgs.shape)

    # Download and load pretrained weights
    download_model(DEFAULT_WEIGHTS)

    # Use the default network model
    NetClass = load_model('ResidualGRUNet')

    # Define a network and a solver. Solver provides a wrapper for the test function.
    net = NetClass(compute_grad=False)  # instantiate a network
    net.load(DEFAULT_WEIGHTS)                        # load downloaded weights
    solver = Solver(net)                # instantiate a solver

    # Run the network
    voxel_prediction, _ = solver.test_output(demo_imgs)

    # Save the prediction to an OBJ file (mesh file).
    voxel2obj(pred_file_name, voxel_prediction[0, :, 1, :, :] > cfg.TEST.VOXEL_THRESH)
    voxel2text(pred_txt_file_name, voxel_prediction[0, :, 1, :, :])


    # Use meshlab or other mesh viewers to visualize the prediction.
    # For Ubuntu>=14.04, you can install meshlab using
    # `sudo apt-get install meshlab`
    if cmd_exists('meshlab'):
        call(['meshlab', pred_file_name])
    else:
        print('Meshlab not found: please use visualization of your choice to view %s' %
              pred_file_name)


if __name__ == '__main__':
    # Set the batch size to 1
    cfg_from_list(['CONST.BATCH_SIZE', 1])
    main()
