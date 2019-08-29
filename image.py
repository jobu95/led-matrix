#!/usr/bin/env python

from PIL import Image

im = Image.open("IMG_1142.JPG")

orig_bb     = im.getbbox()
print("Img bbox: %s" %(orig_bb,))

orig_wd = orig_bb[2] - orig_bb[0]
orig_ht = orig_bb[3] - orig_bb[1]
orig_xcent = orig_wd / 2
orig_ycent = orig_ht / 2

if True:
    desired_bb_xcent = orig_xcent
    desired_bb_ycent = orig_ycent
    desired_bb_wd  = orig_wd / 2
    desired_bb_ht  = orig_ht / 2
    # format: left, up, right, down
    desired_bb = (desired_bb_xcent - desired_bb_wd / 2,
            desired_bb_ycent - desired_bb_ht / 2,
            desired_bb_xcent + desired_bb_wd / 2,
            desired_bb_ycent + desired_bb_ht / 2)

    im = im.crop(desired_bb)

save_sz = (64, 64)
im.thumbnail(save_sz, resample=Image.BILINEAR)

im.save("foo.jpg")

# x 656
# y 940

