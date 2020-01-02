#!/usr/bin/env python3

import moviepy.editor
import sys
import os

if len(sys.argv) != 2:
    print("Usage: %s filename" % sys.argv[0])
    sys.exit(1)

orig_filename = sys.argv[1]
orig_basename = os.path.basename(orig_filename)
orig_path = os.path.dirname(orig_filename)

clip = moviepy.editor.VideoFileClip(orig_filename)
segment_length_s = 5
cur_segment_offset_s = 0
i = 0
while cur_segment_offset_s < clip.duration:
    new_filename = os.path.join(orig_path, str(i).zfill(3) + "_" +
            orig_basename)
    print(new_filename)
    clip.subclip(cur_segment_offset_s,
            cur_segment_offset_s + segment_length_s).write_gif(new_filename)
    cur_segment_offset_s += segment_length_s
    i += 1

