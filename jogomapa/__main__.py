import pygame

import jogomapa

try:
    jogo = jogomapa.Jogo()
    jogo.executar()
finally:
    pygame.quit()


