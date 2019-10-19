#!/usr/bin/env python

import cv2
import numpy as np
import sys

xdim = 64
ydim = 64
chan = 3

frame_count = 0
frame_delay_ms = 16
frame = np.zeros((xdim, ydim, chan), np.uint8)
cv2.namedWindow('lines', cv2.WINDOW_NORMAL)
cv2.resizeWindow('lines', 640, 640)
while True:
    pxval = (frame_count % 256)
    frame_count += 1
    for y in range(0,64):
        pxval += y*3
        for x in range(0,64):
            for c in range(0,3):
                frame[x][y][c] = (pxval + x) % 256
    cv2.imshow('lines', frame)
    if (cv2.waitKey(frame_delay_ms) & 0xFF) == ord('q'):
        break

cv2.destroyAllWindows()

