#!/usr/bin/env python

import sys
from PIL import Image, ImageColor, ImageDraw, ImageFont

# xAlignment \elem { 'LEFT', 'CENTER' }
# yAlignment \elem { 'TOP', 'CENTER' }
def renderText(lines, yCharSz=10, xAlignment='LEFT', yAlignment='TOP'):

    draw = ImageDraw.Draw(image)

    # max chars per line: 12
    # max lines: ????
    xCharSz = 6
    yCharSz = 10
    font = ImageFont.truetype('MONACO.TTF', yCharSz)
    print(font)

    # Handle yAlignment
    yOffset = 0
    xDim = image.size[0]
    yDim = image.size[1]
    if yAlignment is 'CENTER':
        numLines = min(len(lines), int(yDim / yCharSz))
        yOccupancyPx = numLines * yCharSz # number of y pixels the message occupies
        yMin = int((yDim - yOccupancyPx) / 2)
        print("lines in this image: %d" % (numLines))
        print("yOccupancyPx: %d" % (yOccupancyPx))
        yOffset = int((yDim - yOccupancyPx) / 2)
        print("yOffset: %d" % yOffset)
    elif yAlignment is 'TOP':
        yOffset = 0
    else:
        # TODO throw
        print("Invalid yAlignment")
        return

    #numLines = max(len(lines),

    curline = 0
    xoff = 0 # TODO implement horizontal text centering
    for line in lines:
        xOffset = 0
        if xAlignment is 'CENTER':
            numChars = min(len(line), int(xDim / xCharSz))
            xOccupancyPx = xCharSz * numChars
            print("line: %s" % (line))
            print("line len: %d" % (numChars))
            print("line occupancy: %d" % (xOccupancyPx))
            xOffset = int((xDim - xOccupancyPx) / 2)
            print("xOffset: %d" % (xOffset))

        draw.text((xOffset, yOffset + curline * yCharSz), line, font=font)
        curline += 1


xdim = 64
ydim = 64

image = Image.new('RGB', size=(xdim, ydim))

# max chars per line: 12
# max lines: 6
text = ["I", "LOVE", "YOU"]

renderText(text, xAlignment='CENTER', yAlignment='CENTER')

image.show()

#image.save(sys.stdout, "PNG")

