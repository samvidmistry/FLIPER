from argparse import ArgumentParser
from tempfile import gettempdir
from lark import Lark
import PIL
from PIL import Image
from exceptions import CanvasReadjustError, ImagePathError, CanvasNotSetError
from exceptions import ColorOutOfRangeError, DuplicateIdError, IdNotFoundError
from exceptions import NestedBlockError
from exceptions import BlockEndWithoutBeginError
from os import path
from moviepy.editor import ImageSequenceClip
from transitions import Move, Rotate, Scale, Alpha
from utils import alphaOutOfRangeError, checkDuration
from utils import error, errorAtToken

with open('grammar.lark', 'r') as f:
    fliperGrammer = "\n".join(f.readlines())

parser = Lark(fliperGrammer)

canvasWidth, canvasHeight, canvasBackground = None, None, None
canvasImage = None
canvas = None
# Flag indicating whether we are in a block or not
inBlock = False
# maximum duration from all transitions in a block
maxDuration = 0
# Queue of animations found in a block
animationQueue = []

# A dictionary containing image ID and their corresponding image object
imageData = {}
# A dictionary containing image's location on the canvas
imageLocation = {}

# A list containing frames for the flipbook
frames = []


def checkCanvas(tok):
    '''
    Make sure that the canvas is initialized. If not,
    raise CanvasNotSetError.
    '''
    if canvasWidth is None or canvasHeight is None:
        raise CanvasNotSetError(
            errorAtToken("Canvas size not set before drawing.", tok))


def checkId(tok):
    '''
    Check if we have an object/image associated with the provided ID. If not,
    raise IdNotFoundError.
    '''
    idStr = tok.children[0][1:-1]
    if idStr not in imageData:
        raise IdNotFoundError(
            errorAtToken("No image is associated with ID {}".format(idStr),
                         tok))


def drawFrame():
    '''
    State of the canvas is saved in the `imageData` and `imageLocation`.
    Extract all the objects, draw them on a fresh canvas and save the image as
    a new frame.
    '''
    canvasImage = Image.new("RGBA", (canvasWidth, canvasHeight),
                            canvasBackground)

    for k, v in imageData.items():
        canvasImage.paste(v, box=(imageLocation[k]))

    frames.append(canvasImage)


def applyAnimation(id, animation):
    '''
    Given the ID of the object, give it to the animation along with
    its location and save the resulting image and location back into
    the dictionary.
    '''
    image, x, y = animation.apply(imageData[id], imageLocation[id][0],
                                  imageLocation[id][1])
    imageData[id] = image
    imageLocation[id] = (x, y)


def applyAnimationsForDuration(animations, duration):
    '''
    Run the provided animations for provided duration.
    '''
    for i in range(1, duration + 1):
        for id, anim in animations:
            applyAnimation(id, anim)
            drawFrame()


def applyOrQueue(id, animation, duration):
    '''
    If we are not in a block, apply the animation directly.
    Otherwise, queue the animation to be executed when the block ends.
    '''
    global maxDuration
    global animationQueue

    if inBlock:
        maxDuration = max(maxDuration, duration)
        animationQueue.append((id, animation))
    else:
        applyAnimationsForDuration([(id, animation)], duration)


def runInstruction(instr):
    '''
    Run the given instruction. In case of block begin, the instructions
    will be collected and ran when the block end command is encountered.
    '''
    global canvasWidth
    global canvasHeight
    global canvas
    global canvasImage
    global canvasBackground
    global inBlock
    global maxDuration
    global animationQueue

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

        animation = Move(sx, sy, dx, dy, duration)
        applyOrQueue(id, animation, duration)

    elif instr.data == 'rotate_object':
        checkCanvas(instr.children[0])
        id = instr.children[0].children[0][1:-1]
        checkId(instr.children[0])

        degrees = float(instr.children[1].children[0])
        duration = instr.children[2].children[0]
        checkDuration(duration)
        duration = int(duration)

        animation = Rotate(degrees, duration, canvasBackground)
        applyOrQueue(id, animation, duration)

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
        _, _, _, srcAlpha = image.getpixel((0, 0))
        animation = Alpha(srcAlpha, destAlpha, duration)
        applyOrQueue(id, animation, duration)

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

        animation = Scale(sWidth, sHeight, duration, sx, sy)
        applyOrQueue(id, animation, duration)

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

    elif instr.data == 'block_begin':
        if inBlock:
            raise NestedBlockError(
                error("Nested blocks are not supported", instr.line, 0))

        inBlock = True

    elif instr.data == 'block_end':
        if not inBlock:
            raise BlockEndWithoutBeginError(
                error("No pairing begin block statement present", instr.line,
                      0))

        applyAnimationsForDuration(animationQueue, maxDuration)
        inBlock = False
        maxDuration = 0
        animationQueue.clear()


def runFliper(program, out="out.mp4", fps=15):
    '''
    Run the provided program and write the resulting
    video to the file provided in `out`. Beware that this will
    export all frame into the temporary directory of your OS
    so make sure you have enough space.
    '''
    parseTree = parser.parse(program)

    for instr in parseTree.children:
        runInstruction(instr)

    frameNames = []
    for i, f in enumerate(frames):
        fName = gettempdir() + "/frame_{}.png".format(i)
        f.save(fName)
        frameNames.append(fName)
    clip = ImageSequenceClip(frameNames, fps=fps, with_mask=True)
    clip.write_videofile(out, audio=False)


def main():
    parser = ArgumentParser()
    parser.add_argument('program', help='Program to create flipbook')
    parser.add_argument(
        '-o',
        '--out',
        default='out.mp4',
        help='Name of the output file. Beware that changing the ' +
        'extension in the output file will also change the encoding' +
        ' used by FLIPER to create the video.'
    )
    parser.add_argument('-fps', default=15, type=int, help='Frames per second')
    args = parser.parse_args()

    with open(args.program, 'r') as f:
        runFliper("\n".join(f.readlines()), out=args.out, fps=args.fps)


if __name__ == '__main__':
    main()
