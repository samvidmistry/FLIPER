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
