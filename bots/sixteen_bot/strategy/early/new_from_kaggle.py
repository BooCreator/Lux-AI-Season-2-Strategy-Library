import numpy as np
from strategy.kits.utils import *
from math import ceil

from lux.kit import GameState
from lux.config import EnvConfig

from scipy.ndimage import distance_transform_cdt

try:
    from utils.tools import toImage
    from utils.competition import createFolder
except:
    #toImage(r_ice, 'log/step/r_ice', frames=1, render=True)
    def toImage(imgs:np.ndarray, filename:str='_blank', *, render:bool=False, return_:bool=False, palette=None, frames:int=5): pass
    def createFolder(arr:list): pass

from scipy.spatial import KDTree

def manhattan_dist_to_nth_closest(arr, n):
    if n == 1:
        distance_map = distance_transform_cdt(1-arr, metric='taxicab')
        return distance_map
    else:
        true_coords = np.transpose(np.nonzero(arr))
        tree = KDTree(true_coords)
        dist, _ = tree.query(np.transpose(np.nonzero(~arr)), k=n, p=1)
        return np.reshape(dist[:, n-1], arr.shape)

def count_region_cells(array, start, min_dist=2, max_dist=np.inf, exponent=1):
    
    def dfs(array, loc):
        distance_from_start = abs(loc[0]-start[0]) + abs(loc[1]-start[1])
        if not (0<=loc[0]<array.shape[0] and 0<=loc[1]<array.shape[1]):
            return 0
        if (not array[loc]) or visited[loc]:
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
    r_weighted:np.ndarray = None
    spread_ice = 2
    f_max = 0
    r_ice = None
    r_ore = None
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    def __init__(self, env_cfg:EnvConfig) -> None:
        self.env_cfg = env_cfg
        self.weighted = None
        self.r_weighted = None
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
    # ----- Распространение для ресурсов ------------------------------------------------------------------------
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    def calcMap(self, map:np.ndarray, spread:int, title:str='', multiplier:int=1):
        result = manhattan_dist_to_nth_closest(map, 1)
        result = np.where(result > spread, 0, (spread+1)-result)
        if self.player == 'player_0': toImage(result*multiplier, f'log/step/{title}', render=True, frames=1)
        return result
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    # ----- Рассчитываем матрицу весов для расстановки фабрик ---------------------------------------------------
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    def calcWeightedMatrix(self, ice_spread:int=2, ore_spread:int=7):
        # --- рассчитываем матрицы ---
        ice_map, ore_map, rubble, valid = getResFromState(self.game_state)
        self.weighted, self.r_weighted = np.zeros(ice_map.shape), np.zeros(ice_map.shape)
        self.r_ice = self.calcMap(ice_map, ice_spread, 'ice', 25)*valid
        if self.player == 'player_0': toImage(self.r_ice*valid*25, 'log/step/ice_valid', render=True, frames=1)
        self.r_ore = self.calcMap(ore_map, ore_spread, 'ore', 25)*valid
        if self.player == 'player_0': toImage(self.r_ore*valid*25, 'log/step/ore_valid', render=True, frames=1)
        self.r_ice, self.r_ore = self.setBorder(self.r_ice), self.setBorder(self.r_ore)
        # --- выбираем лучшие позиции для расстановки ---
        size = (6, 7)
        for [x, y] in np.argwhere(self.r_ice > 0):
            s_a = [max(x-size[0], 3), min(x+size[0]+1, rubble.shape[0]-4)]
            e_a = [max(y-size[0], 3), min(y+size[0]+1, rubble.shape[1]-4)]
            slice = np.where(self.r_ice > 0, 50, rubble)[s_a[0]:s_a[1], e_a[0]:e_a[1]]
            arg = len(slice)/len(np.argwhere(slice > 25))
            s_b = [max(x-size[1], 3), min(x+size[1]+1, rubble.shape[0]-4)]
            e_b = [max(y-size[1], 3), min(y+size[1]+1, rubble.shape[1]-4)]
            ln = np.sum(self.r_ore[s_b[0]:s_b[1], e_b[0]:e_b[1]])
            self.weighted[x, y] = arg
            self.r_weighted[x, y] = ln
        if self.player == 'player_0': toImage(self.weighted*25, f'log/step/wgt', render=True, frames=1)
        if self.player == 'player_0': toImage(self.r_weighted*25, f'log/step/r_wgt', render=True, frames=1)
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
            self.wgt = max(1-n_factories / self.f_max, 0.15)
            valid = self.game_state.board.valid_spawns_mask.astype(int)
            while np.max(self.weighted*valid) <= 0:
                self.calcWeightedMatrix(self.spread_ice+1)

            res = (self.weighted + normalize(self.r_weighted, np.max(self.weighted))*self.wgt)*valid
            if self.player == 'player_0': toImage(res*25, f'log/step/res', render=True, frames=3)
            spawn_loc = np.argwhere(res == np.max(res))[0]
            for [x, y] in getRadV2(spawn_loc, 10):
                self.weighted[x, y] -= np.max(res)/2
            if self.player == 'player_0': toImage(self.weighted*25, f'log/step/wgt_new', render=True, frames=3)
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