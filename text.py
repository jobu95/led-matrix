#!/usr/bin/env python

import sys
import time
from PIL import Image, ImageColor, ImageDraw, ImageFont

# TODO this is a priori knowledge. Query this from font object, somehow
xCharSz = 6
yCharSz = 10
font = ImageFont.truetype('MONACO.TTF', yCharSz)

# Render lines of text, where lines is an iterable of strings.
# xAlignment \elem { 'LEFT', 'CENTER' }
# yAlignment \elem { 'TOP', 'CENTER' }
# yOffsetPx may be negative
def renderLines(image, lines, yCharSz=10, xAlignment='LEFT', yAlignment='TOP', yOffsetPx=0):

    draw = ImageDraw.Draw(image)

    # Handle yAlignment
    xDim = image.size[0]
    yDim = image.size[1]
    if yAlignment is 'CENTER':
        numLines = min(len(lines), int(yDim / yCharSz))
        yOccupancyPx = numLines * yCharSz # number of y pixels the message occupies
        yMin = int((yDim - yOccupancyPx) / 2)
        yOffsetPx += int((yDim - yOccupancyPx) / 2)
    elif yAlignment is 'TOP':
        # Nothing to do
        pass
    else:
        # TODO throw
        print("Invalid yAlignment")
        return

    curline = 0
    for line in lines:
        xOffsetPx = 0
        if xAlignment is 'CENTER':
            numChars = min(len(line), int(xDim / xCharSz))
            xOccupancyPx = xCharSz * numChars
            xOffsetPx = int((xDim - xOccupancyPx) / 2)
        elif xAlignment is 'LEFT':
            # Nothing to do
            pass
        else:
            # TODO throw
            print("Invalid xAlignment")

        draw.text((xOffsetPx, yOffsetPx + curline * yCharSz), line, font=font)
        curline += 1

def breakTextIntoLines(image, text, maxLines=-1):
    xDim = image.size[0]
    maxCharsPerLine = int(xDim / xCharSz)

    lines = []

    while len(text) > 0:

        if len(text) <= maxCharsPerLine:
            lines.append(text)
            text = ""
            continue

        # Line needs to be broken
        maxIdx = maxCharsPerLine

        # Find last space
        while text[maxIdx] != " " and maxIdx > 0:
            maxIdx -= 1

        if maxIdx == 0:
            # Word is > maxCharsPerLine long. Check if it has a hyphen
            maxIdx = maxCharsPerLine
            while text[maxIdx] != "-" and maxIdx > 0:
                maxIdx -= 1

            if maxIdx == 0:
                # Word does not contain a hyphen. Break it
                maxIdx = maxCharsPerLine - 1
                lines.append(text[:maxIdx] + "-")
                text = text[maxIdx:]
            else:
                # Word has a hyphen
                lines.append(text[:maxIdx + 1])
                text = text[maxIdx + 1:]
        else:
            # Found a space
            lines.append(text[:maxIdx])
            text = text[maxIdx + 1:]

        if maxLines > 0 and len(lines) == maxLines:
            break

    return lines

# Render text from a string. Lines are automatically broken at whitespace, and
# words are broken with hyphens if necessary.
# This will generate as many images as necessary until the entire message has
# been displayed.
# * pause{Start,End}Frames control how many identical frames will be rendered at
#   the start and end.
# * yStepPx controls how many pixels each frame will shift up by while scrolling.
def renderScrollingText(image, text, yStepPx=4, pauseStartFrames=4, pauseEndFrames=4):
    lines = breakTextIntoLines(image, text)

    start_image = image.copy()

    yDim = image.size[1]
    maxLinesPerScreen = int(yDim / yCharSz)

    curYPx = 0
    while True:
        curLine = int(curYPx / yCharSz)
        if curLine > len(lines):
            break

        line_slice = lines[curLine:curLine+maxLinesPerScreen+1]

        image = start_image.copy()
        yOffsetPx = -1 * (curYPx % yCharSz)
        renderLines(image, line_slice, yOffsetPx=yOffsetPx)

        if curLine % 7 == 0:
            image.show()

        curYPx += yStepPx

xdim = 64
ydim = 64
image = Image.new('RGB', size=(xdim, ydim))

renderScrollingText(image, "A spectre is haunting Europe - the spectre of communism. " +
        "All the powers of old Europe have entered into a holy alliance to " +
        "exorcise this spectre: Pope and Tsar, Metternich and Guizot, French " +
        "Radicals and German police-spies.")

#text = ["I", "LOVE", "YOU"]
#renderLines(image, text, xAlignment='LEFT', yAlignment='TOP')

#image.save(sys.stdout, "PNG")

