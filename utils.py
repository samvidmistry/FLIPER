from exceptions import ColorOutOfRangeError, InvalidDurationError


def alphaOutOfRangeError(tok):
    '''
    Raise an error if alpha channel value is out of range.
    '''
    raise ColorOutOfRangeError(errorAtToken("0 <= alpha value <= 255", tok))


def checkDuration(tok):
    '''
    Check if the duration is >= 0. If not, throw InvalidDurationError.
    '''
    if int(tok) <= 0:
        raise InvalidDurationError(
            errorAtToken("Duration must be strictly greater than 0", tok))


def errorAtToken(message, tok):
    '''
    Utility function to get an error string with location of the provided
    token. This will make sure that all error messages have consistent
    formatting.
    '''
    return error(message, tok.line, tok.column)


def error(message, line, column):
    '''
    Utility function to generate an error message.
    '''
    return "At {}:{}, {}".format(line, column, message)
