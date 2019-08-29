#!/usr/bin/env python

from PIL import Image

im = Image.open("IMG_1153.JPG")

orig_bb     = im.getbbox()
print("Img bbox: %s" %(orig_bb,))

orig_wd = orig_bb[2] - orig_bb[0]
orig_ht = orig_bb[3] - orig_bb[1]
orig_xcent = orig_wd / 2
orig_ycent = orig_ht / 2

if True:
    desired_bb_xcent = orig_xcent
    desired_bb_ycent = orig_ycent

    opt = 1
    if opt == 0:
        # Zoom in
        desired_bb_wd  = orig_wd / 2
        desired_bb_ht  = orig_ht / 2
    elif opt == 1:
        # Just square it up, don't zoom
        desired_bb_dim = min(orig_wd, orig_ht)
        desired_bb_wd  = desired_bb_dim
        desired_bb_ht  = desired_bb_dim
    elif opt == 2:
        # Use original
        desired_bb_wd  = orig_wd
        desired_bb_ht  = orig_ht

    # format: left, up, right, down
    desired_bb = (desired_bb_xcent - desired_bb_wd / 2,
            desired_bb_ycent - desired_bb_ht / 2,
            desired_bb_xcent + desired_bb_wd / 2,
            desired_bb_ycent + desired_bb_ht / 2)

    print("New bbox: %s" %(desired_bb,))
    im = im.crop(desired_bb)

save_sz = (64, 64)
im.thumbnail(save_sz, resample=Image.BILINEAR)

im.save("out.jpg")

# x 656
# y 940

