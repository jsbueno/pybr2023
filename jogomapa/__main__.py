import os

import pygame

from jogomapa import Game
from jogomapa.game_exceptions import (
    GameWinException,
    GameDefeatException,
    GameClosedException,
)

maps_path = os.path.join(os.path.dirname(__file__), "maps")
maps = os.listdir(maps_path)
game_data = {
    "score": 0,
    "lives": 3
}

while True:
    try:
        game = Game(maps=maps.pop(0), **game_data)
        game.run()
    except GameWinException:
        game.win_screen()
        game_data["score"] = game.score
        game_data["lives"] = game.p1.vidas
    except GameDefeatException:
        game.game_over()
        pygame.quit()
        break
    except (IndexError, GameClosedException):
        pygame.quit()
        break
