from pathlib import Path
import random
import weakref

import pygame
from pygame import Vector2 as V2

resolucao = V2(800, 600)
grade = V2(32, 24)

escala = resolucao.x // grade.x 
largura, altura = resolucao.x // grade.x, resolucao.y // grade.y

class MyVector(pygame.Vector2):
    def __init__(self, *args, owner=None):
        super().__init__(*args)
        self.dono = owner
        self.dono.dono.posicoes[self.x, self.y] = self.dono

    def __iadd__(self, other):
        if self.check(other):
            prev = self.x, self.y
            super().__iadd__(other)
            del self.dono.dono.posicoes[prev]
            self.dono.dono.posicoes[self.x, self.y] = self.dono
        return self
    
    def __isub__(self, other):
        other = V2(other)
        if self.check(-other):
            prev = self.x, self.y
            super().__isub__(other)
            del self.dono.dono.posicoes[prev]
            self.dono.dono.posicoes[self.x, self.y] = self.dono
        return self
    
    def check(self, other):
        if self.dono is None:
            return True
        return self.dono.check(V2(self) + V2(other))

class Objeto(pygame.sprite.Sprite):
    cor = (128, 128, 128)

    def __init__(self, dono, pos):
        super().__init__()
        self.dono = dono
        self.pos = MyVector(pos, owner=self)
  
    @property
    def coord_tela(self):
        return V2(self.pos.x * altura, self.pos.y * largura)
    
    def check(self, coord):
        result = 0 <= coord.x < grade.x and 0 <= coord.y < grade.y
        return result 

class Pegavel(Objeto):
    pontos = 0
    def pegou(self):
        self.dono.pontuacao += self.pontos
        self.kill()

class Tesouro(Pegavel):
    cor = (0, 0, 255)
    pontos = 10

    def __init__(self, *args, **kw):
        super().__init__(*args, **kw)
        self.dono.tesouros.add(self)

class Parede(Objeto):
    cor = (255, 255, 255)

class Bomba(Pegavel):
    cor = (255, 255, 0)
    pontos = -10

    def pegou(self):
        super().pegou()
        self.dono.total_bombas += 1


class Personagem(Objeto):
    atraso = 3
    cor = (255, 0, 0)
    def __init__(self, *args, **kw):
        super().__init__(*args, **kw)
        self.ultima_atualizacao = self.dono.frame_atual
        self.dono.p1 = self

    def mover(self, keys):
        if self.dono.frame_atual - self.ultima_atualizacao < self.atraso:
            return
        self.ultima_atualizacao = self.dono.frame_atual
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
            objeto_aqui = self.dono[pos]
    
            if objeto_aqui and not isinstance(objeto_aqui, Personagem):
                # Lugar ideal pra usar o
                # comando match/case (py 3.10)
                if isinstance(objeto_aqui, Pegavel):
                    objeto_aqui.pegou()
                elif isinstance(objeto_aqui, Parede):
                    result = False


        return result

tabela = {
"@": Tesouro,
"*": Personagem,
"p": Parede,
"b": Bomba,
}

class Mapa:
    def __init__(self, caminho):
        self.caminho = Path(caminho)
        dados = list(self.caminho.open())
        self.le_cabecalho(dados)
        self.le_dados(dados)

    def le_cabecalho(self, dados):
        linha_altura_larg = dados[0]
        larg_txt, alt_txt = linha_altura_larg.split(",")
        self.altura = int(alt_txt.strip())
        self.largura = int(larg_txt.strip())
    
    def le_dados(self, dados):
        for i, linha in enumerate(dados):
            if linha.rstrip() == "-":
                i += 1
                break
        else: 
            raise ValueError("O arquivo de mapa deve conter uma linah com um unico '-' indicando o inicio dos dados")
        self.dados = [linha.rstrip("\n") for linha in dados[i:]]

    def __getitem__(self, indice):
        indice = V2(indice)
        x = int(indice[0])
        y = int(indice[1])
        if not (0 <= x < self.largura and 0 <= y < self.altura):
            raise IndexError()
        if y >= len(self.dados):
            return " "
        if len(self.dados[y]) <= x:
            return " "
        return self.dados[y][x]
     
    def __iter__(self):
        for linha in range(self.altura):
            for col in range(self.largura):
                yield V2(col, linha), self[col, linha]

    def __repr__(self):
        linhas = []
        for linha in range(self.altura):
            linha_tmp = ""
            for col in range(self.largura):
                linha_tmp += self[col, linha]   
            linhas.append(linha_tmp)
        return "\n".join(linhas)
        

class Jogo:
    def __init__(self):
        pygame.init()
        self.posicoes = weakref.WeakValueDictionary()

        self.frame_atual = 0
        self.pontuacao = 0
        self.tela = pygame.display.set_mode(resolucao)
        self.fonte = pygame.font.SysFont("Arial", int(altura))

        self.objetos = pygame.sprite.Group()
        self.tesouros = pygame.sprite.Group()
        self.total_bombas = 0

        self.ler_mapa("mapa_0.txt")


    def __getitem__(self, pos):
        return self.posicoes.get((pos[0], pos[1]))

    def ler_mapa(self, arq_mapa):
        caminho = Path(__file__).parent
        mapa = Mapa(caminho / arq_mapa)
        for pos, character in mapa:
            if character == " ":
                continue
            item = tabela[character](self, pos)
            self.objetos.add(item)

    def executar(self):
        while True:
            self.tela.fill((0,0,0))
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return

            keys = pygame.key.get_pressed()
            self.p1.mover(keys)
            if keys[pygame.K_p]:
                print (dict(self.posicoes))

            for objeto in self.objetos:
                pygame.draw.rect(self.tela, objeto.cor, (*objeto.coord_tela, largura, altura))

            self.mostrar_pontuacao()
            pygame.display.update()
            self.frame_atual += 1
            pygame.time.delay(30)
    

    def mostrar_pontuacao(self):
        texto = self.fonte.render(f"{self.pontuacao}", True, (255, 255,255) )
        x = 0
        y = resolucao.y - altura
        self.tela.blit(texto, (x,y))

def inicio():
    try:
        jogo = Jogo()
        jogo.executar()
    finally:
        pygame.quit()


if __name__ == "__main__":
    try:
        jogo = Jogo()
        jogo.executar()
    finally:
        pygame.quit()
