#!/usr/bin/env python

from moviepy.editor import *
from moviepy.video.fx.all import *

clip = VideoFileClip("out.gif")

clip = clip.subclip(0, 31)

clip.write_gif("out2.gif")

