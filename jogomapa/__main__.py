import pygame

import jogomapa
from jogomapa.game_exceptions import GameWinException, GameDefeatException

try:
    jogo = jogomapa.Jogo()
    jogo.executar()
except GameWinException:
    jogo.mostrar_vitoria()
except GameDefeatException:
    jogo.fim_jogo()
finally:
    pygame.quit()
