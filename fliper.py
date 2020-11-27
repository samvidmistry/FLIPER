from argparse import ArgumentParser
from lark import Lark
import PIL
from PIL import Image, ImageDraw
from exceptions import CanvasReadjustError, ImagePathError, CanvasNotSetError
from exceptions import ColorOutOfRangeError, DuplicateIdError
from os import path

with open('grammar.lark', 'r') as f:
    fliperGrammer = "\n".join(f.readlines())

parser = Lark(fliperGrammer)

canvasWidth, canvasHeight = None, None
canvasImage = None
canvas = None

# A dictionary containing image ID and their corresponding image object
imageData = {}

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


def runInstruction(instr):
    global canvasWidth
    global canvasHeight
    global canvas
    global canvasImage

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
                raise ColorOutOfRangeError(
                    errorAtToken("0 <= alpha value <= 255", instr.children[5]))
            color = (red, green, blue, alpha)
        canvasWidth = int(width)
        canvasHeight = int(height)
        canvasImage = Image.new("RGBA", (width, height), color)
        canvas = ImageDraw.Draw(canvasImage)

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
                             iPath))

        if not path.isfile(iPath):
            raise ImagePathError(
                errorAtToken("{} is not a file".format(iPath), iPath))

        try:
            im = Image.open(iPath).convert("RGBA")
            imageData[id] = im
            canvasImage.paste(im, box=(x, y))
            canvas = ImageDraw.Draw(canvasImage)
        except PIL.UnidentifiedImageError:
            raise ImagePathError(
                errorAtToken(
                    "Image at {} cannot be opened or identified.".format(
                        iPath), iPath))


def runFliper(program):
    parseTree = parser.parse(program)

    for instr in parseTree.children:
        runInstruction(instr)

    canvasImage.show()


def main():
    parser = ArgumentParser()
    parser.add_argument('program', help='Program to create flipbook')
    args = parser.parse_args()

    with open(args.program, 'r') as f:
        runFliper("\n".join(f.readlines()))


if __name__ == '__main__':
    main()
