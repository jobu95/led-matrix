#!/usr/bin/env python

from moviepy.editor import *
from moviepy.video.fx.all import *

clip = VideoFileClip("harambe.mp4")

#clip = clip.subclip(38, 52)

(clip_wd, clip_ht) = clip.size
print("Input is %d x %d" % (clip_wd, clip_ht,))

clip_xcent = clip_wd / 2
clip_ycent = clip_ht / 2
output_dim = min(clip_wd, clip_ht)
print("Output is %d x %d" % (output_dim, output_dim))

clip = crop(clip,
        x1=clip_xcent - output_dim/2,
        x2=clip_xcent + output_dim/2,
        y1=clip_ycent - output_dim/2,
        y2=clip_ycent + output_dim/2)

clip = resize(clip, height=64, width=64)

clip.write_gif("out.gif")

