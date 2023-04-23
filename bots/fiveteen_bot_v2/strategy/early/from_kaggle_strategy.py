import numpy as np
from strategy.kits.utils import *
from math import ceil

from lux.kit import GameState
from lux.config import EnvConfig

try:
    from utils.tools import toImage
except:
    def toImage(imgs:np.ndarray, filename:str='_blank', *, render:bool=False, return_:bool=False, palette=None, frames:int=5): pass

def count_region_cells(array, start, min_dist=2, max_dist=np.inf, exponent=1):
    
    def dfs(array, loc):
        distance_from_start = abs(loc[0]-start[0]) + abs(loc[1]-start[1])
        if not (0<=loc[0]<array.shape[0] and 0<=loc[1]<array.shape[1]):   # check to see if we're still inside the map
            return 0
        if (not array[loc]) or visited[loc]:     # we're only interested in low rubble, not visited yet cells
            return 0
        if not (min_dist <= distance_from_start <= max_dist):      
            return 0
        
        visited[loc] = True

        count = 1.0 * exponent**distance_from_start
        count += dfs(array, (loc[0]-1, loc[1]))
        count += dfs(array, (loc[0]+1, loc[1]))
        count += dfs(array, (loc[0], loc[1]-1))
        count += dfs(array, (loc[0], loc[1]+1))

        return count

    visited = np.zeros_like(array, dtype=bool)
    return dfs(array, start)

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
    #@time_wrapper('lux_early_init', 3)
    def __init__(self, env_cfg:EnvConfig) -> None:
        self.env_cfg = env_cfg
        self.spreadResource = 2
        self.spreadRubble = 6
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
    #@time_wrapper('lux_early_update', 4)
    def update(self, game_state, step:int):
        self.game_state = game_state
        self.step = step
        if self.weighted is None:
            self.calcWeightedMatrix()
        return self
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    # ----- Рассчитываем матрицу весов для расстановки фабрик ---------------------------------------------------
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    #@time_wrapper('lux_early_calcWeightedMatrix', 4)
    def calcWeightedMatrix(self):
        # получаем массивы ресурсов
        ice, ore, rubble, valid = getResFromState(self.game_state)
        # получаем позицию для установки фабрики
        resource = spreadCell(ice, self.spreadResource, max=self.spreadResource*2)
        low_rubble = (rubble<25)
        low_rubble_scores = np.zeros_like(low_rubble, dtype=float)
        for i in range(low_rubble.shape[0]):
            for j in range(low_rubble.shape[1]):
                low_rubble_scores[i,j] = count_region_cells(low_rubble, (i,j), min_dist=0, max_dist=self.spreadResource, exponent=0.1)
        rubble = normalize(low_rubble_scores, self.spreadResource*2)
        res = resource + rubble
        self.weighted = res
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    # ----- Получить позицию расположения фабрики ---------------------------------------------------------------
    # ------- Возвращаем массив из двух значений ----------------------------------------------------------------
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    #@time_wrapper('lux_early_getSpawnPos', 4)
    def getSpawnPos(self) -> dict:
        ''' Получить позицию расположения фабрики '''
        # если фабрики есть для расстановки
        n_factories = self.game_state.teams[self.player].factories_to_place
        if n_factories > 0:
            # получаем массивы ресурсов
            valid = self.game_state.board.valid_spawns_mask.astype(int)
            # определяем сколько ресурсов давать фабрике
            metal = ceil(self.game_state.teams[self.player].metal / n_factories)
            water = ceil(self.game_state.teams[self.player].water / n_factories)
            # получаем позицию для установки фабрики
            res = self.weighted * valid + valid
            #toImage(res, 'log/res_2_s', render=True, frames=5)
            res = conv(res, self.factory_size)
            #toImage(res, 'log/res_3_s', render=True, frames=5)
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