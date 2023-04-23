import numpy as np
from strategy.kits.utils import *
from math import ceil

from lux.kit import GameState
from lux.config import EnvConfig

try:
    from utils.tools import toImage
except:
    #toImage(r_ice, 'log/step/r_ice', frames=1, render=True)
    def toImage(imgs:np.ndarray, filename:str='_blank', *, render:bool=False, return_:bool=False, palette=None, frames:int=5): pass

# ===============================================================================================================
# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
# ===============================================================================================================
class EarlyStrategy:
    ''' Класс стратегии ранней игры '''
    factory_size = (3,3)

    spread = {'ice':(2, 40), 'ore':(5, 5)}
    border = 3

    player = ''
    game_state: GameState = None
    env_cfg: EnvConfig = None
    step = 0

    weighted:np.ndarray = None

    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    def __init__(self, env_cfg:EnvConfig) -> None:
        self.env_cfg = env_cfg
        self.spreadIce = 40
        self.spreadOre = 5
        self.spreadRubble = 9
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    # ----- Ставка для выбора позиции ---------------------------------------------------------------------------
    # ------- Если ставка == 0, то очередь по умолчанию. Ресурсы не тратятся ------------------------------------
    # ------- Если ставка > 0, то ставим на первый ход. Ресурсы тратятся ----------------------------------------
    # ------- Если ставка < 0, то ставим на второй ход. Ресурсы тратятся ----------------------------------------
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    def getBid(self) -> dict:
        ''' Ставка для выбора позиции '''
        return dict(faction="MotherMars", bid=0)
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    # ----- Обновить состояние стратегии ------------------------------------------------------------------------
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    #@time_wrapper('best_early_update', 4)
    def update(self, game_state, step:int):
        self.game_state = game_state
        self.step = step
        if self.weighted is None:
            self.calcWeightedMatrix()
        return self
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    # ----- Рассчитываем матрицу весов для расстановки фабрик ---------------------------------------------------
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    #@time_wrapper('best_early_calcWeightedMatrix', 4)
    def calcWeightedMatrix(self):
        # получаем массивы ресурсов
        ice, ore, rubble, valid = getResFromState(self.game_state)
        # получаем веса поля для установки фабрики
        r_ice = spreadCell(ice, self.spread['ice'][0], val=self.spread['ice'][1])
        r_ore = spreadCell(ore, self.spread['ore'][0], val=self.spread['ore'][1], max=self.spread['ice'][1]-self.spread['ore'][1])
        rubble = normalize(rubble, min(np.max(r_ice), np.max(r_ore))) * -1
        self.weighted = r_ice + r_ore
        self.weighted[:, 0:self.border] = -100
        self.weighted[:, -self.border:] = -100
        self.weighted[0:self.border, ] = -100
        self.weighted[-self.border:, ] = -100
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    # ----- Получить позицию расположения фабрики ---------------------------------------------------------------
    # ------- Возвращаем массив из двух значений ----------------------------------------------------------------
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    #@time_wrapper('best_early_getSpawnPos', 4)
    def getSpawnPos(self) -> dict:
        ''' Получить позицию расположения фабрики '''
        # если фабрики есть для расстановки
        n_factories = self.game_state.teams[self.player].factories_to_place
        if len(self.game_state.factories[self.player]) == 0:
            # получаем матрицу свободных мест
            valid = self.game_state.board.valid_spawns_mask.astype(int)
            # определяем сколько ресурсов давать фабрике
            metal = self.game_state.teams[self.player].metal
            water = self.game_state.teams[self.player].water
            # получаем позицию для установки фабрики
            res = self.weighted * valid + valid
            potential_spawns = np.array(list(zip(*np.where(res==np.max(res)))))
            spawn_loc = potential_spawns[np.random.randint(0, len(potential_spawns))]
            return dict(spawn=spawn_loc, metal=metal, water=water)
        return {}
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    # ----- Обновить игрока для стратегии -----------------------------------------------------------------------
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    def setPlayer(self, player:str):
        self.player = player
        return self
# ===============================================================================================================
# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
# ===============================================================================================================