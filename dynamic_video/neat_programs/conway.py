#!/usr/bin/env python

import cv2
import numpy as np
import sys
from time import sleep

if len(sys.argv) != 2:
    print("Usage: %s state_file" % sys.argv[0])
    sys.exit(1)

state_file=sys.argv[1]
print("Using state file %s" % state_file)

xdim = 64
ydim = 64
chan = 3

# We flip between two boards. One is used as the reference to calculate the
# next frame, then we switch them.
# By convention, board will be indexed like board[y][x].
board = np.zeros((xdim, ydim), np.bool)

with open(state_file, 'r') as state_f:
    y = 0
    for line in state_f:
        if y + 1 > ydim:
            print("State file has >= %d lines, need at most %d" % (y, ydim))
            sys.exit(1)
        if len(line.strip()) != xdim:
            print("State file has line of length %d, need %d" % (len(line.strip()), xdim))
            sys.exit(1)

        x = 0
        for char in line:
            if char == '\n':
                break
            if char != '.':
                board[y][x] = 1
            x += 1
        y += 1

def getNeighbors(board, x, y):
    left_x  = x - 1
    right_x = (x + 1) % xdim
    up_y    = y - 1
    down_y  = (y + 1) % ydim

    if left_x < 0:
        left_x = xdim - 1
    if up_y < 0:
        up_y = ydim - 1

#    if board[y][x] == 1:
#        print("%d,%d has neighbors at %d,%d,%d,%d" % (x, y, left_x, right_x, up_y, down_y))
#
#        print("%d,%d has neighbor at %d,%d: %d" % (x, y, up_y, x, board[up_y][x]))
#        print("%d,%d has neighbor at %d,%d: %d" % (x, y, up_y, right_x, board[up_y][right_x]))
#        print("%d,%d has neighbor at %d,%d: %d" % (x, y, y, right_x, board[y][right_x]))
#        print("%d,%d has neighbor at %d,%d: %d" % (x, y, down_y, right_x, board[down_y][right_x]))
#        print("%d,%d has neighbor at %d,%d: %d" % (x, y, down_y, x, board[down_y][x]))
#        print("%d,%d has neighbor at %d,%d: %d" % (x, y, down_y, left_x, board[down_y][left_x]))
#        print("%d,%d has neighbor at %d,%d: %d" % (x, y, y, left_x, board[y][left_x]))
#        print("%d,%d has neighbor at %d,%d: %d" % (x, y, up_y, left_x, board[up_y][left_x]))

    # Start at 12 o'clock position, add up moving clockwise
    return (int(board[up_y][x] == 1) +
            (board[up_y][right_x] == 1) +
            (board[y][right_x] == 1) +
            (board[down_y][right_x] == 1) +
            (board[down_y][x] == 1) +
            (board[down_y][left_x] == 1) +
            (board[y][left_x] == 1) +
            (board[up_y][left_x] == 1))

def color(neighbors):
    if False:
        if neighbors == 2 or neighbors == 3:
            return [0xff,0xff,0xff]
        else:
            return [0x00,0x00,0x00]
    else:
        if neighbors == 0:
            return [0x00,0x00,0x00]
        elif neighbors == 1:
            return [0x00,0x00,0x00]
        elif neighbors == 2:
            # dcf5ff, white
            return [0xdc,0xf5,0xff]
        elif neighbors == 3:
            # e6c86e, gold
            return [0xe6,0xc8,0x6e]
        elif neighbors == 4:
            # 508cd7, blue
            return [0x50,0x8c,0xd7]
        elif neighbors == 5:
            return [0x00,0x00,0x00]
        elif neighbors == 6:
            return [0x00,0x00,0x00]
        elif neighbors == 7:
            return [0x00,0x00,0x00]
        elif neighbors == 8:
            return [0x00,0x00,0x00]
        # d77355, red
        #return [0xe7,0x7c,0x55]
        # 646964, gray
        #return [0x00,0x00,0x00]
        # 55415f, purple
        #return [0x55,0x41,0x5f]
        # dcf5ff, white
        #return [0xdc,0xf5,0xff]

def step(board_in, board_out, frame):
    for y in range(0, len(board_in)):
        for x in range(0, len(board_in[0])):
            neighbors = getNeighbors(board_in, x, y)
            #if neighbors > 0:
            #    print("%d,%d has %d neighbors" % (x, y, neighbors))
            if board_in[y][x] == 0:
                # Looking at a dead cell
                if neighbors == 3:
                    # It's fuck time
                    board_out[y][x] = 1
                    frame[y][x] = color(neighbors)
            else:
                # Looking at a live cell
                if neighbors < 2:
                    # Death by underpopulation
                    board_out[y][x] = 0
                elif neighbors > 3:
                    # Death by overpopulation
                    board_out[y][x] = 0
                else:
                    board_out[y][x] = 1
                    frame[y][x] = color(neighbors)

def boardRow2Str(row):
    res = ""
    for x in row:
        if x == 0:
            res += '.'
        else:
            res += 'x'
    return res

def printBoard(board):
    for y in range(0, len(board)):
        line = boardRow2Str(board[y])
        print(line)

frame_delay_ms = 16
cv2.namedWindow('conway', cv2.WINDOW_NORMAL)
cv2.resizeWindow('conway', 640, 640)
frame_count = 0
alt_board = np.zeros((xdim, ydim), np.bool)
frame = np.zeros((xdim, ydim, chan), np.uint8)

scale = 10
scaled_frame = np.zeros((xdim * scale, ydim * scale, chan), np.uint8)
#scaled_frame = np.zeros((640, 640, chan), np.uint8)

#fourcc = cv2.VideoWriter_fourcc('X', '2', '6', '4') # mp4
fourcc = cv2.VideoWriter_fourcc('M', 'J', 'P', 'G') # avi
#fourcc = cv2.VideoWriter_fourcc('g', 'i', 'f', '') # gif
out = cv2.VideoWriter('conway.avi', fourcc, 24, (xdim * scale, ydim * scale))
#out = cv2.VideoWriter('conway.avi', fourcc, 60, (640,640))
#for i in range(1,600):
#    out.write(scaled_frame)

while True:
    # Display current frame
    if frame_count % 100 == 0:
        print(frame_count)
    frame_count += 1
    #printBoard(board)
    cv2.imshow('conway', frame)
    cv2.resize(frame, (xdim * scale, ydim * scale), scaled_frame, scale, scale, cv2.INTER_NEAREST)
    out.write(scaled_frame)
    if (cv2.waitKey(frame_delay_ms) & 0xFF) == ord('q'):
        break

    # Calculate next frame
    frame.fill(0)
    step(board, alt_board, frame)
    tmp_board = board
    board = alt_board
    alt_board = tmp_board
    alt_board.fill(0)

    if frame_count == 128 * 4:
        break



