#!/usr/bin/env python
import imageio
import re
import sys
import textwrap
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

# Taken from here:
# http://code.activestate.com/recipes/358228-extend-textwraptextwrapper-to-handle-multiple-para/
class DocWrapper(textwrap.TextWrapper):
    def wrap(self, text):
        para_edge = re.compile(r"(\n\n)", re.MULTILINE)
        paragraphs = para_edge.split(text)
        wrapped_lines = []
        for para in paragraphs:
            if para.isspace():
                if not self.replace_whitespace:
                    # Do not take the leading and trailing newlines since
                    # joining the list with newlines (as self.fill will do)
                    # will put them back in.
                    if self.expand_tabs:
                        para = para.expandtabs()
                    wrapped_lines.append(para[1:-1])
                else:
                    # self.fill will end up putting in the needed newline to
                    # space out the paragraphs
                    wrapped_lines.append('')
            else:
                wrapped_lines.extend(textwrap.TextWrapper.wrap(self, para))
        return wrapped_lines

class ScrollingText(Renderable):
    def __init__(self, font_filename, text_filename, framerate=12):
        self.frame_dur_s = (1.0 / framerate)
        self.xCharSz = 5
        self.yCharSz = 8
        self.lineSpacing = 1 # number of pixels between lines
        self.font = ImageFont.truetype(font_filename, self.yCharSz)

        # text is small, just load it up all at once for simplicity's sake
        with open(text_filename, 'r') as text_file:
            self.text = re.sub(r'([^\n])\n([^\n])', r'\1 \2', text_file.read())

        xdim = 64
        ydim = 64
        self.image = Image.new('RGB', size=(xdim, ydim), color=(0,0,0))
        self.draw = ImageDraw.Draw(self.image)

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

        t0 = time.time()
        self.image.paste((0,0,0), box=(0,0) + self.image.size)
        self.draw.multiline_text((xOffsetPx, yOffsetPx), line_str,
                font=self.font, spacing=self.lineSpacing)
        t1 = time.time()
        #print("renderLines dur: %f" % (t1 - t0))

    # Render text from a string. Lines are automatically broken at whitespace, and
    # words are broken with hyphens if necessary.
    # This will generate as many images as necessary until the entire message has
    # been displayed.
    # * pause{Start,End}Frames control how many identical frames will be rendered at
    #   the start and end.
    # * yStepPx controls how many pixels each frame will shift up by while scrolling.
    def renderScrollingText(self, yStepPx=1):
        #textwrap.replace_whitespace = False
        #textwrap.drop_whitespace = False
        tw = DocWrapper()
        tw.width = self.image.size[0] / self.xCharSz
        lines = tw.wrap(self.text)

        yDim = self.image.size[1]
        maxLinesPerScreen = int(yDim / self.yCharSz)

        curYPx = 0
        real_y_char_sz = self.yCharSz + self.lineSpacing
        while True:
            curLine = int(curYPx / real_y_char_sz)
            if curLine > len(lines) + 1:
                break

            line_slice = lines[curLine:curLine+maxLinesPerScreen+1]

            yOffsetPx = -1 * (curYPx % real_y_char_sz)
            self.renderLines(line_slice, yOffsetPx=yOffsetPx)
            yield self.image
            curYPx += yStepPx

    def getFrames(self):
        return self.renderScrollingText()

    def saveFrames(self, frames, filename):
        print("saving gif at %s" % filename)
        print("frames len: %d" % len(frames))
        frame_dur_ms = self.frame_dur_s * 1000
        frames[0].save(filename, format='GIF', append_images=frames[1:], save_all=True,
                duration=frame_dur_ms, loop=0)

    def save(self, filename):
        frames = []
        i = 0
        need_save = False
        # split up clip into parts if it exceeds this # of frames
        max_frames = 1000
        for frame in self.getFrames():
            need_save = True
            i += 1
            frames.append(frame.copy())
            if i % max_frames == 0:
                part_filename = str(int((i-1) / max_frames)).zfill(3) + "_" + filename
                self.saveFrames(frames, part_filename)
                need_save = False
                frames = []
        if need_save:
            part_filename = filename
            if i > max_frames:
                part_filename = str(int(i / max_frames)).zfill(3) + "_" + filename
            self.saveFrames(frames, part_filename)

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
            time.sleep(0.001)
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

if False:
    video = Video(filename, 4)
    screen = Screen()
    pacer = FramePacer(video.frame_dur_s)
    for frame in video.getFrames():
        screen.matrix.SetImage(frame)
        # Sleep until it's time for the next frame
        pacer.waitFrame()
else:
    video = ScrollingText('MONACO.TTF', filename)
    video.save(re.sub(r'.txt', r'.gif', filename))

