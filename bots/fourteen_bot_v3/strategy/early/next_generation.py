import numpy as np
from strategy.kits.utils import *
from math import ceil

from lux.kit import GameState
from lux.config import EnvConfig

try:
    from utils.tools import toImage
    from utils.competition import createFolder
except:
    #toImage(r_ice, 'log/step/r_ice', frames=1, render=True)
    def toImage(imgs:np.ndarray, filename:str='_blank', *, render:bool=False, return_:bool=False, palette=None, frames:int=5): pass
    def createFolder(arr:list): pass

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
    factory_size = (3,3)

    border = 3

    player = ''
    game_state: GameState = None
    env_cfg: EnvConfig = None
    step = 0
    wgt = 0
    weighted:np.ndarray = None
    f_max = 0
    spread_ice = (2, 60)
    r_ice = None
    r_ore = None
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    def __init__(self, env_cfg:EnvConfig) -> None:
        self.env_cfg = env_cfg
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
        if self.r_ice is None:
            self.calcIceMap()
        if self.r_ore is None:
            self.calcOreMap()
        return self
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    # ----- Убрать зону для расстновки возле границ -------------------------------------------------------------
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    def setBorder(self, matrix:np.ndarray, border:int=-1):
        if border < 1: border = self.border
        matrix[:, 0:self.border] = -100
        matrix[:, -self.border:] = -100
        matrix[0:self.border, ]  = -100
        matrix[-self.border:, ]  = -100
        return matrix
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    # ----- Рассчитываем матрицу весов для расстановки фабрик ---------------------------------------------------
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    def calcIceMap(self, spread:tuple=(2, 60)):
        ice_map = self.game_state.board.ice
        self.r_ice = spreadCellV2(ice_map, spread[0], val=spread[1])
        self.r_ice = self.setBorder(self.r_ice)
    # -----------------------------------------------------------------------------------------------------------
    def calcOreMap(self, spread:tuple=(4, 5)):
        ore_map = self.game_state.board.ore
        self.r_ore = spreadCell(ore_map, spread[0], val=spread[1], max=20)
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    # ----- Получить позицию расположения фабрики ---------------------------------------------------------------
    # ------- Возвращаем массив из двух значений ----------------------------------------------------------------
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    #@time_wrapper('best_early_getSpawnPos', 4)
    def getSpawnPos(self) -> dict:
        ''' Получить позицию расположения фабрики '''
        # если фабрики есть для расстановки
        n_factories = self.game_state.teams[self.player].factories_to_place
        if n_factories > 0:
            # --- определяем сколько ресурсов давать фабрике ---
            metal = ceil(self.game_state.teams[self.player].metal / n_factories)
            water = ceil(self.game_state.teams[self.player].water / n_factories)
            # --- получаем веса ---
            if self.f_max < n_factories: self.f_max = n_factories
            self.wgt = n_factories / self.f_max
            # --- получаем матрицу свободных мест ---
            valid = self.game_state.board.valid_spawns_mask.astype(int)
            while np.max(self.r_ice*valid) <= 0:
                self.spread_ice = (self.spread_ice[0]+1, round(120/self.spread_ice[0]))
                self.calcIceMap(self.spread_ice)
            # --- расчитываем итоговую матрицу ---
            if np.max(self.r_ore) > np.max(self.r_ice): self.r_ore = normalize(self.r_ore, np.max(self.r_ice)/2)
            res = (self.r_ice + self.r_ore/self.wgt)*valid+valid
            # правим веса на основе щебня
            rubble = self.game_state.board.rubble
            # --- получаем позицию для установки фабрики ---
            potential_spawns = np.array(list(zip(*np.where(res==np.max(res)))))
            spawn_i, spawn_min = 0, 1000
            size = 9
            for i, spawn in enumerate(potential_spawns):
                start = [max(spawn[0]-size, 0), min(spawn[0]+size+1, rubble.shape[0])]
                end = [max(spawn[1]-size, 0), min(spawn[1]+size+1, rubble.shape[1])]
                slice = rubble[start[0]:start[1], end[0]:end[1]]
                sum = np.sum(slice)/(slice.shape[0]*slice.shape[1])
                if sum < spawn_min:
                    spawn_i = i
                    spawn_min = sum
            spawn_loc = potential_spawns[spawn_i]
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