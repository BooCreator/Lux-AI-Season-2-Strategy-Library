import numpy as np
from strategy.kits.utils import *
from math import ceil

from lux.kit import GameState
from lux.config import EnvConfig

from utils.tools import toImage

# ===============================================================================================================
# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
# ===============================================================================================================
class EarlyStrategy:
    ''' Класс стратегии ранней игры '''
    spreadRubble = 3
    spreadResource = 3
    factory_size = (3,3)

    player = ''
    game_state: GameState = None
    env_cfg: EnvConfig = None
    step = 0

    weighted:np.ndarray = None

    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    def __init__(self, env_cfg:EnvConfig) -> None:
        self.env_cfg = env_cfg
        self.spreadResource = 9
        self.spreadRubble = 9
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    # ----- Ставка для выбора позиции ---------------------------------------------------------------------------
    # ------- Если ставка == 0, то очередь по умолчанию. Ресурсы не тратятся ------------------------------------
    # ------- Если ставка > 0, то ставим на первый ход. Ресурсы тратятся ----------------------------------------
    # ------- Если ставка < 0, то ставим на второй ход. Ресурсы тратятся ----------------------------------------
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    def getBid(self) -> dict:
        ''' Ставка для выбора позиции '''
        return dict(faction="AlphaStrike", bid=0)
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    # ----- Обновить состояние стратегии ------------------------------------------------------------------------
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    def update(self, game_state, step:int):
        self.game_state = game_state
        self.step = step
        if self.weighted is None:
            self.calcWeightedMatrix()
        return self
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    # ----- Рассчитываем матрицу весов для расстановки фабрик ---------------------------------------------------
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    def calcWeightedMatrix(self):
        # получаем массивы ресурсов
        ice, ore, rubble, valid = getResFromState(self.game_state)
        #toImage(ice, 'log/1_ice_s', render=True, frames=1)
        #toImage(ore, 'log/3_ore_s', render=True, frames=1)
        #toImage(rubble, 'log/5_rubble_s', render=True, frames=1)
        # получаем позицию для установки фабрики
        resource = spreadCell(ice, self.spreadResource, max=self.spreadResource*2)
        r_ore = spreadCell(ore, self.spreadResource, max=self.spreadResource*2)
        rubble = normalize(rubble, np.max(resource)/self.spreadRubble)
        rubble = spreadCell(rubble, self.spreadRubble, find=0, val=-1)
        #toImage(resource, 'log/2_spread_ice_s', render=True, frames=1)
        #toImage(r_ore, 'log/4_spread_ore_s', render=True, frames=1)
        #toImage(rubble, 'log/7_spread_rubble_s', render=True, frames=1)
        res = resource - r_ore - rubble
        #toImage(res, 'log/res_1_s', render=True, frames=1)
        self.weighted = res
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    # ----- Получить позицию расположения фабрики ---------------------------------------------------------------
    # ------- Возвращаем массив из двух значений ----------------------------------------------------------------
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    # --> "getSpawnPos" time: 0:00:00.070436
    def getSpawnPos(self) -> dict:
        ''' Получить позицию расположения фабрики '''
        # если фабрики есть для расстановки
        n_factories = self.game_state.teams[self.player].factories_to_place
        if n_factories > 0:
            # получаем массивы ресурсов
            ice, ore, rubble, valid = getResFromState(self.game_state)
            # определяем сколько ресурсов давать фабрике
            metal = ceil(self.game_state.teams[self.player].metal / n_factories)
            water = ceil(self.game_state.teams[self.player].water / n_factories)
            # получаем позицию для установки фабрики
            res = self.weighted * valid + valid
            #toImage(res, 'log/res_2_s', render=True, frames=1)
            res = conv(res, self.factory_size)
            #toImage(res, 'log/res_3_s', render=True, frames=1)
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