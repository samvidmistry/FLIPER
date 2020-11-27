import math


class Transition:
    '''
    Base class for all transitions available in FLIPER
    '''
    def apply(image, sx, sy):
        raise NotImplementedError("Subclasses must implement this")


class Move(Transition):
    '''
    Transition class for MOV.
    '''
    def __init__(self, sx, sy, dx, dy, duration):
        self.index = 1
        self.sx = sx
        self.sy = sy
        self.dx = dx
        self.dy = dy
        self.duration = duration
        # If we are crossing the x or y axis and going to the negative
        # side, we'll first have to come to 0 and then go to the destination
        distx = abs(sx - dx) if sx * dx >= 0 else (abs(sx) + abs(dx))
        disty = abs(sy - dy) if sy * dy >= 0 else (abs(sy) + abs(dy))
        self.stepx = distx / duration
        self.stepy = disty / duration
        self.signx = -1 if dx < sx else 1
        self.signy = -1 if dy < sy else 1

    def apply(self, image, sx, sy):
        if self.index > self.duration:
            return (image, sx, sy)

        if self.index == self.duration:
            res = (image, self.dx, self.dy)
            self.index += 1
        else:
            res = (image,
                   self.sx + math.ceil(self.stepx * self.signx * self.index),
                   self.sy + math.ceil(self.stepy * self.signy * self.index))
            self.index += 1

        return res


class Rotate(Transition):
    '''
    Transition class for ROT.
    '''
    def __init__(self, degrees, duration, fillBackground):
        self.index = 1
        self.destDegrees = degrees
        self.duration = duration
        self.step = degrees / duration
        self.fillBackground = fillBackground

    def apply(self, image, sx, sy):
        if self.index > self.duration:
            return (image, sx, sy)

        res = (image.rotate(angle=(self.destDegrees -
                                   (self.index - 1) * self.step)
                            if self.index == self.duration else self.step,
                            fillcolor=self.fillBackground), sx, sy)
        self.index += 1
        return res


class Scale(Transition):
    '''
    Transition class for SCL.
    '''
    def __init__(self, sWidth, sHeight, duration, scalex, scaley):
        self.index = 1
        self.sWidth = sWidth
        self.sHeight = sHeight
        self.duration = duration
        self.dWidth = math.ceil(sWidth * scalex)
        self.dHeight = math.ceil(sHeight * scaley)
        self.stepx = abs(self.dWidth - sWidth) / duration
        self.stepy = abs(self.dHeight - sHeight) / duration
        self.signx = -1 if self.dWidth < sWidth else 1
        self.signy = -1 if self.dHeight < sHeight else 1

    def apply(self, image, sx, sy):
        if self.index > self.duration:
            return (image, sx, sy)

        if self.index == self.duration:
            self.index += 1
            return (image.resize((self.dWidth, self.dHeight)), sx, sy)

        res = (image.resize(
            (self.sWidth + math.ceil(self.signx * self.stepx * self.index),
             self.sHeight + math.ceil(self.signy * self.stepy * self.index))),
               sx, sy)
        self.index += 1
        return res


class Alpha(Transition):
    '''
    Transition class for ALP.
    '''
    def __init__(self, srcAlpha, destAlpha, duration):
        self.srcAlpha = srcAlpha
        self.duration = duration
        self.index = 1
        self.destAlpha = destAlpha
        self.step = abs(destAlpha - srcAlpha) / duration
        self.sign = -1 if srcAlpha > destAlpha else 1

    def apply(self, image, sx, sy):
        if self.index > self.duration:
            return (image, sx, sy)

        cp = image.copy()

        if self.index == self.duration:
            cp.putalpha(self.destAlpha)
            self.index += 1
            return (cp, sx, sy)

        # Since the alpha channel is changed for the whole
        # image, taking alpha value from any pixel should work
        cp.putalpha(self.srcAlpha +
                    math.ceil(self.sign * self.step * self.index))
        self.index += 1
        return (cp, sx, sy)
