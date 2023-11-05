import pygame

import jogomapa
from jogomapa.game_exceptions import GameWinException

try:
    jogo = jogomapa.Jogo()
    jogo.executar()
except GameWinException:
    jogo.mostrar_vitoria()
finally:
    pygame.quit()
