#!/usr/bin/env python

from moviepy.editor import *
from moviepy.video.fx.all import *

clip = VideoFileClip("numa_numa.mp4")

#clip = clip.subclip(51, 86)

(clip_wd, clip_ht) = clip.size
print("Input is %d x %d" % (clip_wd, clip_ht,))

opt = 0
if opt == 0:
    # Cut out a square from the middle
    clip_xcent = clip_wd * 2/5
    clip_ycent = clip_ht / 2
    output_dim = min(clip_wd, clip_ht)

    clip = crop(clip,
            x1=clip_xcent - output_dim/2,
            x2=clip_xcent + output_dim/2,
            y1=clip_ycent - output_dim/2,
            y2=clip_ycent + output_dim/2)
elif opt == 1:
    # Make square by adding black bars
    xfill = 0
    yfill = 0
    if clip_wd > clip_ht:
        yfill = (clip_wd - clip_ht) / 2
    elif clip_wd < clip_ht:
        xfill = (clip_ht - clip_wd) / 2
    clip = margin(clip,
            left=xfill, right=xfill, top=yfill, bottom=yfill)

(new_wd, new_ht) = clip.size
print("Output is %d x %d" % (new_wd, new_ht,))

clip = resize(clip, width=64)

clip.write_gif("out.gif")

