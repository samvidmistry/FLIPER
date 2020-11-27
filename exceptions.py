class FliperError(Exception):
    '''
    Base class for all errors in Fliper
    '''
    pass


class CanvasNotSetError(FliperError):
    '''
    Exception raised when drawing commands start appearing before
    canvas size is set.
    '''
    def __init__(self, message):
        self.message = message


class CanvasReadjustError(FliperError):
    '''
    Exception raised when canvas size is changed in between the
    program rather than at the start of it.
    '''
    def __init__(self, message):
        self.message = message


class ImagePathError(FliperError):
    '''
    Exception raised when there is some problem with loading a
    specified image.
    '''
    def __init__(self, message):
        self.message = message


class ColorOutOfRangeError(FliperError):
    '''
    Exception raised when the color is out of the valid range,
    i.e., color < 0 or color > 255.
    '''
    def __init__(self, message):
        self.message = message


class DuplicateIdError(FliperError):
    '''
    Exception raised when an image is already associated with given ID.
    '''
    def __init__(self, message):
        self.message = message


class IdNotFoundError(FliperError):
    '''
    Exception raised when there is no image associated with provided ID.
    '''
    def __init__(self, message):
        self.message = message


class InvalidDurationError(FliperError):
    '''
    Exception raised when the duration specified for a transition is invalid,
    i.e., duration <= 0.
    '''
    def __init__(self, message):
        self.message = message


class NestedBlockError(FliperError):
    '''
    Exception raised when a block construct is specified inside another
    block construct. I don't see any point of nested blocks because all
    animations in a block are going to run parallelly anyway.
    '''
    def __init__(self, message):
        self.message = message


class BlockEndWithoutBeginError(FliperError):
    '''
    Exception raised when a block end command is encountered without
    the pairing begin command.
    '''
    def __init__(self, message):
        self.message = message
