class GameException(BaseException):
    """
    Base game exception.
    """


class GameWinException(GameException):
    """
    Raises when the game finishes by win condition.
    """

class GameDefeatException(GameException):
    """
    Raises when the game finishes by defeat condition
    """