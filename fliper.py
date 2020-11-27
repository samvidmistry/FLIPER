from argparse import ArgumentParser
from lark import Lark
import PIL
from PIL import Image
from exceptions import CanvasReadjustError, ImagePathError, CanvasNotSetError
from exceptions import ColorOutOfRangeError, DuplicateIdError, IdNotFoundError
from exceptions import InvalidDurationError
from os import path
from moviepy.editor import ImageSequenceClip
import math

with open('grammar.lark', 'r') as f:
    fliperGrammer = "\n".join(f.readlines())

parser = Lark(fliperGrammer)

canvasWidth, canvasHeight, canvasBackground = None, None, None
canvasImage = None
canvas = None

# A dictionary containing image ID and their corresponding image object
imageData = {}
# A dictionary containing image's location on the canvas
imageLocation = {}

# A list containing frames for the flipbook
frames = []


def error(message, line, column):
    return "At {}:{}, {}".format(line, column, message)


def errorAtToken(message, tok):
    return error(message, tok.line, tok.column)


def checkCanvas(tok):
    if canvasWidth is None or canvasHeight is None:
        raise CanvasNotSetError(
            errorAtToken("Canvas size not set before drawing.", tok))


def checkDuration(tok):
    if int(tok) <= 0:
        raise InvalidDurationError(
            errorAtToken("Duration must be strictly greater than 0", tok))


def checkId(tok):
    idStr = tok.children[0][1:-1]
    if idStr not in imageData:
        raise IdNotFoundError(
            errorAtToken("No image is associated with ID {}".format(idStr),
                         tok))


def alphaOutOfRangeError(tok):
    raise ColorOutOfRangeError(errorAtToken("0 <= alpha value <= 255", tok))


def drawFrame():
    canvasImage = Image.new("RGBA", (canvasWidth, canvasHeight),
                            canvasBackground)

    for k, v in imageData.items():
        canvasImage.paste(v, box=(imageLocation[k]))

    frames.append(canvasImage)


def runInstruction(instr):
    global canvasWidth
    global canvasHeight
    global canvas
    global canvasImage
    global canvasBackground

    if instr.data == 'canvas_size':
        if canvasWidth is not None and canvasHeight is not None:
            raise CanvasReadjustError(
                errorAtToken("Canvas size changed after drawing commands.",
                             instr.children[0]))
        width = int(instr.children[0].children[0])
        height = int(instr.children[1].children[0])
        color = (255, 255, 255, 255)
        if len(instr.children) == 6:
            red = int(instr.children[2].children[0])
            if red < 0 or red > 255:
                raise ColorOutOfRangeError(
                    errorAtToken("0 <= color value <= 255", instr.children[2]))
            green = int(instr.children[3].children[0])
            if green < 0 or green > 255:
                raise ColorOutOfRangeError(
                    errorAtToken("0 <= color value <= 255", instr.children[3]))
            blue = int(instr.children[4].children[0])
            if blue < 0 or blue > 255:
                raise ColorOutOfRangeError(
                    errorAtToken("0 <= color value <= 255", instr.children[4]))
            alpha = int(instr.children[5].children[0])
            if alpha < 0 or alpha > 255:
                alphaOutOfRangeError(instr.children[5])
            color = (red, green, blue, alpha)
        canvasWidth = int(width)
        canvasHeight = int(height)
        canvasBackground = color

    elif instr.data == 'declare_image':
        checkCanvas(instr.children[0].children[0])
        children = instr.children
        iPath = children[0].children[0][1:-1]
        id = children[1].children[0][1:-1]

        if id in imageData:
            raise DuplicateIdError(
                errorAtToken(
                    "ID {} is already associated with an image.".format(id),
                    children[1].children[0]))

        x = 0 if len(children) != 4 else int(children[2].children[0])
        y = 0 if len(children) != 4 else int(children[3].children[0])

        if not path.exists(iPath):
            raise ImagePathError(
                errorAtToken("Image at {} does not exist.".format(iPath),
                             children[0].children[0]))

        if not path.isfile(iPath):
            raise ImagePathError(
                errorAtToken("{} is not a file".format(iPath),
                             children[0].children[0]))

        try:
            im = Image.open(iPath).convert("RGBA")
            imageData[id] = im
            imageLocation[id] = (x, y)
            drawFrame()
        except PIL.UnidentifiedImageError:
            raise ImagePathError(
                errorAtToken(
                    "Image at {} cannot be opened or identified.".format(
                        iPath), children[0].children[0]))

    elif instr.data == 'move_object':
        checkCanvas(instr.children[0])
        id = instr.children[0].children[0][1:-1]
        checkId(instr.children[0])

        sx, sy = imageLocation[id]
        dx = int(instr.children[1].children[0])
        dy = int(instr.children[2].children[0])
        duration = instr.children[3].children[0]

        checkDuration(duration)
        duration = int(duration)

        # If we are crossing the x or y axis and going to the negative
        # side, we'll first have to come to 0 and then go to the destination
        distx = abs(sx - dx) if sx * dx >= 0 else (abs(sx) + abs(dx))
        disty = abs(sy - dy) if sy * dy >= 0 else (abs(sy) + abs(dy))
        stepx = distx / duration
        stepy = disty / duration
        signx = -1 if dx < sx else 1
        signy = -1 if dy < sy else 1
        for i in range(1, duration + 1):
            imageLocation[id] = (sx + math.ceil(stepx * signx * i),
                                 sy + math.ceil(stepy * signy * i))
            drawFrame()

        if abs(sx - dx) % duration != 0 or abs(sy - dy) % duration != 0:
            #################################################
            # TODO: Give a warning when the duration is not #
            # evenly divisible                              #
            #################################################
            imageLocation[id] = (dx, dy)
            drawFrame()

    elif instr.data == 'rotate_object':
        checkCanvas(instr.children[0])
        id = instr.children[0].children[0][1:-1]
        checkId(instr.children[0])

        degrees = float(instr.children[1].children[0])
        duration = instr.children[2].children[0]
        checkDuration(duration)
        duration = int(duration)

        image = imageData[id]
        step = degrees / duration
        for i in range(1, duration + 1):
            imageData[id] = image.rotate(angle=step * i,
                                         fillcolor=canvasBackground)
            drawFrame()

        if degrees % duration != 0:
            imageData[id] = image.rotate(angle=degrees,
                                         fillcolor=canvasBackground)
            drawFrame()

    elif instr.data == 'change_opacity':
        checkCanvas(instr.children[0])
        id = instr.children[0].children[0][1:-1]
        checkId(instr.children[0])

        destAlpha = int(instr.children[1].children[0])
        if destAlpha < 0 or destAlpha > 255:
            alphaOutOfRangeError(instr.children[1])

        duration = instr.children[2].children[0]
        checkDuration(duration)
        duration = int(duration)

        image = imageData[id]
        # Since the alpha channel is changed for the whole
        # image, taking alpha value from any pixel should work
        _, _, _, srcAlpha = image.getpixel((0, 0))
        step = abs(destAlpha - srcAlpha) / duration
        sign = -1 if srcAlpha > destAlpha else 1

        for i in range(1, duration + 1):
            image.putalpha(srcAlpha + math.ceil(sign * step * i))
            drawFrame()

        if abs(destAlpha - srcAlpha) % duration != 0:
            image.putalpha(destAlpha)
            drawFrame()

    elif instr.data == 'scale_object':
        checkCanvas(instr.children[0])
        id = instr.children[0].children[0][1:-1]
        checkId(instr.children[0])

        sx = float(instr.children[1].children[0])
        sy = float(instr.children[2].children[0])

        duration = instr.children[3].children[0]
        checkDuration(duration)
        duration = int(duration)

        sWidth = imageData[id].width
        sHeight = imageData[id].height
        dWidth = math.ceil(sWidth * sx)
        dHeight = math.ceil(sHeight * sy)

        stepx = abs(dWidth - sWidth) / duration
        stepy = abs(dHeight - sHeight) / duration
        signx = -1 if dWidth < sWidth else 1
        signy = -1 if dHeight < sHeight else 1

        for i in range(1, duration + 1):
            imageData[id] = imageData[id].resize(
                (sWidth + math.ceil(signx * stepx * i),
                 sHeight + math.ceil(signy * stepy * i)))
            drawFrame()

        if imageData[id].width != dWidth or imageData[id].height != dHeight:
            imageData[id] = imageData[id].resize((dWidth, dHeight))
            drawFrame()

    elif instr.data == 'wait':
        checkCanvas(instr.children[0])
        duration = instr.children[0].children[0]
        checkDuration(duration)
        duration = int(duration)

        for i in range(duration):
            drawFrame()

    elif instr.data == 'delete_object':
        checkCanvas(instr.children[0])
        id = instr.children[0].children[0][1:-1]
        checkId(instr.children[0])

        del imageData[id]
        del imageLocation[id]

        drawFrame()

def runFliper(program, out="out.mp4"):
    parseTree = parser.parse(program)

    for instr in parseTree.children:
        runInstruction(instr)

    frameNames = []
    for i, f in enumerate(frames):
        fName = "/tmp/frame_{}.png".format(i)
        f.save(fName)
        frameNames.append(fName)
    clip = ImageSequenceClip(frameNames, fps=15, with_mask=True)
    clip.write_videofile(out, audio=False)


def main():
    parser = ArgumentParser()
    parser.add_argument('program', help='Program to create flipbook')
    args = parser.parse_args()

    with open(args.program, 'r') as f:
        runFliper("\n".join(f.readlines()))


if __name__ == '__main__':
    main()
