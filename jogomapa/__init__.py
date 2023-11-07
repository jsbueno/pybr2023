from pathlib import Path
import weakref

import pygame
from pygame import Vector2 as V2
from jogomapa.contants import HEIGTH, RESOLUTION, WIDTH, GRID

from jogomapa.game_exceptions import (
    GameDefeatException,
    GameWinException,
    GameClosedException,
)

class MyVector(pygame.Vector2):
    def __init__(self, *args, owner=None):
        super().__init__(*args)
        self.jogo = owner
        self.jogo.jogo.positions[self.x, self.y] = self.jogo

    def __iadd__(self, other):
        if self.check(other):
            prev = self.x, self.y
            super().__iadd__(other)
            del self.jogo.jogo.positions[prev]
            self.jogo.jogo.positions[self.x, self.y] = self.jogo
        return self

    def __isub__(self, other):
        other = V2(other)
        if self.check(-other):
            prev = self.x, self.y
            super().__isub__(other)
            del self.jogo.jogo.positions[prev]
            self.jogo.jogo.positions[self.x, self.y] = self.jogo
        return self

    def check(self, other):
        if self.jogo is None:
            return True
        return self.jogo.check(V2(self) + V2(other))


class Objeto(pygame.sprite.Sprite):
    color = (128, 128, 128)

    def __init__(self, dono, pos):
        super().__init__()
        self.jogo = dono
        self.pos = MyVector(pos, owner=self)

    @property
    def coord_tela(self):
        return V2(
            (self.pos.x - self.jogo.offsets.x) * HEIGTH,
            (self.pos.y - self.jogo.offsets.y) * WIDTH,
        )


    def check(self, coord):
        result = 0 <= coord.x < GRID.x and 0 <= coord.y < GRID.y
        return result


class Catch(Objeto):
    points = 0

    def catched(self):
        self.jogo.score += self.points
        self.kill()


class Treasure(Catch):
    color = (0, 0, 255)
    points = 10

    def __init__(self, *args, **kw):
        super().__init__(*args, **kw)
        self.jogo.treasures.add(self)


class Wall(Objeto):
    color = (255, 255, 255)


class Bomb(Catch):
    color = (255, 255, 0)
    points = -10

    def catched(self):
        super().catched()
        self.jogo.p1.vidas -= 1
        if self.jogo.p1.vidas == 0:
            raise GameDefeatException
        self.jogo.bombs += 1

class Candy(Catch):
    color = (148, 0, 211)

    def catched(self):
        super().catched()
        if self.jogo.p1.vidas < 3:
            self.jogo.p1.vidas += 1

class Personagem(Objeto):
    atraso = 3
    vidas = 3
    color = (255, 0, 0)

    def __init__(self, *args, **kw):
        super().__init__(*args, **kw)
        self.ultima_atualizacao = self.jogo.current_frame
        self.jogo.p1 = self

    def mover(self, keys):
        if self.jogo.current_frame - self.ultima_atualizacao < self.atraso:
            return
        self.ultima_atualizacao = self.jogo.current_frame
        if keys[pygame.K_DOWN]:
            self.pos += (0, 1)
        if keys[pygame.K_UP]:
            self.pos -= (0, 1)
        if keys[pygame.K_RIGHT]:
            self.pos += (1, 0)
        if keys[pygame.K_LEFT]:
            self.pos -= (1, 0)

    def check(self, pos):
        result = super().check(pos)
        if result:
            objeto_aqui = self.jogo[pos]

            if objeto_aqui and not isinstance(objeto_aqui, Personagem):
                # Lugar ideal pra usar o
                # comando match/case (py 3.10)
                if isinstance(objeto_aqui, Catch):
                    objeto_aqui.catched()
                elif isinstance(objeto_aqui, Wall):
                    result = False

        return result

    def set_vidas(self, vidas):
        if vidas > 0 and vidas <= 3:
            self.vidas = vidas


tabela = {
    "@": Treasure,
    "*": Personagem,
    "w": Wall,
    "b": Bomb,
    "c": Candy,
}


class Mapa:
    def __init__(self, caminho):
        self.caminho = Path(caminho)
        dados = list(self.caminho.open())
        self.le_cabecalho(dados)
        self.le_dados(dados)

    def le_cabecalho(self, dados):
        linha_HEIGTH_larg = dados[0]
        larg_txt, alt_txt = linha_HEIGTH_larg.split(",")
        self.HEIGTH = int(alt_txt.strip())
        self.WIDTH = int(larg_txt.strip())

    def le_dados(self, dados):
        for i, linha in enumerate(dados):
            if linha.rstrip() == "-":
                i += 1
                break
        else:
            raise ValueError(
                "O arquivo de mapa deve conter uma linha com um \
                    unico '-' indicando o inicio dos dados"
            )
        self.dados = [linha.rstrip("\n") for linha in dados[i:]]

    def __getitem__(self, indice):
        indice = V2(indice)
        x = int(indice[0])
        y = int(indice[1])
        if not (0 <= x < self.WIDTH and 0 <= y < self.HEIGTH):
            raise IndexError()
        if y >= len(self.dados):
            return " "
        if len(self.dados[y]) <= x:
            return " "
        return self.dados[y][x]

    def __iter__(self):
        for linha in range(self.HEIGTH):
            for col in range(self.WIDTH):
                yield V2(col, linha), self[col, linha]

    def __repr__(self):
        linhas = []
        for linha in range(self.HEIGTH):
            linha_tmp = ""
            for col in range(self.WIDTH):
                linha_tmp += self[col, linha]
            linhas.append(linha_tmp)
        return "\n".join(linhas)


class Game:
    def __init__(self, maps, score=None, lives=3):
        pygame.init()
        self.positions = weakref.WeakValueDictionary()

        self.current_frame = 0
        self.score = score if score else 0
        self.screen = pygame.display.set_mode(RESOLUTION)
        self.font = pygame.font.SysFont("Arial", int(HEIGTH))

        self.objects = pygame.sprite.Group()
        self.treasures = pygame.sprite.Group()
        self.bombs = 0

        self.load_maps(f"maps/{maps}", lives)

    def __getitem__(self, pos):
        return self.positions.get((pos[0], pos[1]))

    def load_maps(self, arq_mapa, vidas):
        caminho = Path(__file__).parent
        mapa = Mapa(caminho / arq_mapa)
        for pos, character in mapa:
            if character == " ":
                continue
            item = tabela[character](self, pos)
            if isinstance(item, Personagem):
                item.set_vidas(vidas)
            self.objects.add(item)
        self.offsets = V2(0,0)  # WIP

    def run(self):
        while True:
            self.screen.fill((0, 0, 0))
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    raise GameClosedException

            keys = pygame.key.get_pressed()
            self.p1.mover(keys)

            if not any(self.treasures):
                raise GameWinException

            if keys[pygame.K_p]:
                print(dict(self.positions))

            self.renderizar()

            for objeto in self.objects:
                pygame.draw.rect(
                    self.screen,
                    objeto.color,
                    (*objeto.coord_tela, WIDTH, HEIGTH)
                )

            self.show_score()
            self.show_lives()
            pygame.display.update()
            self.current_frame += 1
            pygame.time.delay(30)

    def show_score(self):
        text = self.font.render(f"{self.score}", True, (255, 255, 255))

    def renderizar(self):
        for objeto in self.objects:
            pygame.draw.rect(
                self.screen, objeto.color, (*objeto.coord_tela, WIDTH, HEIGTH)
            )

    def mostrar_pontuacao(self):
        texto = self.fonte.render(f"{self.pontuacao}", True, (255, 255, 255))
        x = 0
        y = RESOLUTION.y - HEIGTH
        self.screen.blit(text, (x, y))

    def show_lives(self):
        texto = self.font.render(f"{self.p1.vidas}", True, (255, 0, 0))
        self.screen.blit(texto, (RESOLUTION.x / 3, RESOLUTION.y - HEIGTH))

    def win_screen(self):
        while True:
            self.screen.fill((0, 0, 0))
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return
                if event.type == pygame.KEYDOWN:
                    return

            texto = self.font.render("PRÓXIMA FASE", True, (255, 255, 255))
            self.screen.blit(texto, (RESOLUTION.x / 2, RESOLUTION.y / 2))

            pygame.display.update()
            self.current_frame += 1
            pygame.time.delay(30)

    def game_over(self):
        while True:
            self.screen.fill((0, 0, 0))
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return
                if event.type == pygame.KEYDOWN:
                    return

            texto = self.font.render(
                f"{self.score}", True, (255, 255, 255)
            )
            self.screen.blit(texto, (RESOLUTION.x / 2, RESOLUTION.y / 2))

            pygame.display.update()
            self.current_frame += 1
            pygame.time.delay(30)
