import os

import pygame

import jogomapa
from jogomapa.game_exceptions import (
    GameWinException,
    GameDefeatException,
    GameClosedException,
)

diretorio_mapas = os.path.join(os.path.dirname(__file__), "mapas")
mapas = os.listdir(diretorio_mapas)
pontuacao = 0
vidas = 3

while True:
    try:
        jogo = jogomapa.Jogo(pontuacao=pontuacao, mapa=mapas.pop(0), vidas=vidas)
        jogo.executar()
    except GameWinException:
        jogo.mostrar_vitoria()
        pontuacao = jogo.pontuacao
        vidas = jogo.p1.vidas
    except GameDefeatException:
        jogo.fim_jogo()
        pygame.quit()
        break
    except (IndexError, GameClosedException):
        pygame.quit()
        break
