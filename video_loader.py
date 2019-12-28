#!/usr/bin/env python
import imageio
import re
import sys
import time

from rgbmatrix import RGBMatrix, RGBMatrixOptions
from PIL import Image, ImageColor, ImageDraw, ImageFont

if len(sys.argv) != 2:
    print("Usage: %s <filename>" % (sys.argv[0]))
    sys.exit(1)

filename = sys.argv[1]
print("Filename: %s" % (filename))

class Renderable:
    def __init__(self):
        return

    def getFrames(self):
        return

class Video(Renderable):
    def __init__(self, filename, n_repetitions):
        t_start = time.time()
        self.im = imageio.mimread(filename)

        self.n_frames = 0
        self.n_repetitions = 0

        frame_dur_ms = self.im[0].meta['duration']
        self.frame_dur_s = frame_dur_ms / 1000.0
        self.cur_frame = 0
        self.n_frames = len(self.im)
        self.cur_repetition = 0
        self.n_repetitions  = n_repetitions

        print("n_reps: %d" % self.n_repetitions)

        print("Frame duration (ms): %d" % (frame_dur_ms))
        print("Resolution:          %d x %d" % (len(self.im[0]), len(self.im[0][0])))
        print("# of frames:         %d" % (len(self.im)))
        print("Duration (s):        %f" % (frame_dur_ms * len(self.im) / 1000.0))
        print("Load time (s):       %f" % (time.time() - t_start))
        print("")

    def hasFrame(self):
        return self.cur_frame < self.n_frames or self.cur_repetition < self.n_repetitions

    def iterateFrame(self):
        if self.cur_frame < self.n_frames:
            # Partway through video
            self.cur_frame += 1
            return True

        # Finished one repetition
        self.cur_repetition += 1
        if self.cur_repetition < self.n_repetitions:
            # Need to run another time
            self.cur_frame = 1
            return True
        # Ran as many times as desired
        return False

    def getFrames(self):
        while self.hasFrame():
            for frame in self.im:
                if not self.iterateFrame():
                    return
                image = Image.fromarray(frame).convert('RGB')
                #print("(rep: %d/%d) (frame: %d/%d)" %
                #        (self.cur_repetition, self.n_repetitions, self.cur_frame, self.n_frames))
                yield image

class ScrollingText(Renderable):
    def __init__(self, font_filename, text_filename):
        framerate = 60
        self.frame_dur_s = (1.0 / framerate)
        self.xCharSz = 5
        self.yCharSz = 8
        self.font = ImageFont.truetype(font_filename, self.yCharSz)

        xdim = 64
        ydim = 64
        self.image = Image.new('RGB', size=(xdim, ydim), color=(0,0,0))

        print("frame duration (s): %f" % self.frame_dur_s)

    def renderLines(self, lines, xAlignment='LEFT', yAlignment='TOP', yOffsetPx=0):

        # Handle yAlignment
        xDim = self.image.size[0]
        yDim = self.image.size[1]
        if yAlignment is 'CENTER':
            numLines = min(len(lines), int(yDim / self.yCharSz))
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

        line_str = ""
        for line in lines:
            line_str += (line + "\n")

        xOffsetPx = 0
        if xAlignment is 'CENTER':
            numChars = min(len(line), int(xDim / self.xCharSz))
            xOccupancyPx = self.xCharSz * numChars
            xOffsetPx = int((xDim - xOccupancyPx) / 2)
        elif xAlignment is 'LEFT':
            # Nothing to do
            pass
        else:
            # TODO throw
            print("Invalid xAlignment")

        draw = ImageDraw.Draw(self.image)
        t0 = time.time()
        draw.text((xOffsetPx, yOffsetPx), line_str,
                font=self.font)
        t1 = time.time()
        print("renderLines dur: %f" % (t1 - t0))

    def breakTextIntoLines(self, text, maxLines=-1):
        xDim = self.image.size[0]
        maxCharsPerLine = int(xDim / self.xCharSz)

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

            line = ""

            if maxIdx == 0:
                # Word is > maxCharsPerLine long. Check if it has a hyphen
                maxIdx = maxCharsPerLine
                while text[maxIdx] != "-" and maxIdx > 0:
                    maxIdx -= 1

                if maxIdx == 0:
                    # Word does not contain a hyphen. Break it
                    maxIdx = maxCharsPerLine - 1
                    line = (text[:maxIdx] + "-")
                    text = text[maxIdx:]
                else:
                    # Word has a hyphen
                    line = text[:maxIdx + 1]
                    text = text[maxIdx + 1:]
            else:
                # Found a space
                line = text[:maxIdx]
                text = text[maxIdx + 1:]

            line = line.strip()
            line = re.sub(r'([^\n])\n', r'\1', line)

            if len(line) == 0:
                continue

            lines.append(line)

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
    def renderScrollingText(self, text, yStepPx=1):
        lines = self.breakTextIntoLines(text)

        start_image = self.image.copy()

        yDim = self.image.size[1]
        maxLinesPerScreen = int(yDim / self.yCharSz)

        curYPx = 0
        while True:
            curLine = int(curYPx / self.yCharSz)
            if curLine > len(lines) + 1:
                break

            line_slice = lines[curLine:curLine+maxLinesPerScreen+1]

            self.image = start_image.copy()
            yOffsetPx = -1 * (curYPx % self.yCharSz)
            self.renderLines(line_slice, yOffsetPx=yOffsetPx)
            yield self.image
            curYPx += yStepPx

    def getFrames(self):
        return self.renderScrollingText(
            "A spectre is haunting Europe - the spectre of communism. \
            All the powers of old Europe have entered into a holy alliance to \
            exorcise this spectre: Pope and Tsar, Metternich and Guizot, French \
            Radicals and German police-spies.")

class FramePacer:
    def __init__(self, frame_dur_s):
        self.t0 = 0
        self.frame_dur_fudge_s = 0.002
        self.frame_dur_s = frame_dur_s

    def waitFrame(self):
        now = time.time()
        if self.t0 == 0:
            self.t0 = now
        while (now - self.t0 < (self.frame_dur_s - self.frame_dur_fudge_s)):
            now = time.time()
            time.sleep(0.0005)
        self.t0 = now

class Screen:
    def __init__(self):
        options = RGBMatrixOptions()
        options.cols = 64
        options.rows = 64
        options.chain_length = 1
        options.parallel = 1
        options.hardware_mapping = 'adafruit-hat-pwm'  # If you have an Adafruit HAT: 'adafruit-hat'
        #print(options.scan_mode)
        self.matrix = RGBMatrix(options = options)

video = Video(filename, 4)
#video = ScrollingText('MONACO.TTF', 'manifesto.txt')

pacer = FramePacer(video.frame_dur_s)
screen = Screen()

if True:
    for frame in video.getFrames():
        screen.matrix.SetImage(frame)
        # Sleep until it's time for the next frame
        pacer.waitFrame()

