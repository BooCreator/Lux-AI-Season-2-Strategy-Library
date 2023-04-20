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
        if self.weighted is None:
            self.calcWeightedMatrix()
        return self
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    # ----- Рассчитываем матрицу весов для расстановки фабрик ---------------------------------------------------
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    #@time_wrapper('best_early_calcWeightedMatrix', 4)
    def calcWeightedMatrix(self):
        self.spread = {'ice':(2, 60), 'ore':(4, 5)}
        # получаем массивы ресурсов
        ice, ore, __, valid = getResFromState(self.game_state)
        # получаем веса поля для установки фабрики
        r_ice = spreadCell(ice, self.spread['ice'][0], val=self.spread['ice'][1])
        r_ore = spreadCell(ore, self.spread['ore'][0], val=self.spread['ore'][1], max=self.spread['ice'][1]/3)
        self.weighted = r_ice + r_ore
        self.weighted[:, 0:self.border] = -100
        self.weighted[:, -self.border:] = -100
        self.weighted[0:self.border, ] = -100
        self.weighted[-self.border:, ] = -100
        # --- лог картинок ---
        log_path = createFolder(['log', 'step'])
        toImage(r_ice, f'{log_path}{self.player}_ice', render=True, frames=1)
        toImage(r_ore, f'{log_path}{self.player}_ore', render=True, frames=1)
        toImage(self.weighted, f'{log_path}{self.player}_weighted', render=True, frames=1)
        toImage(self.weighted*valid + valid, f'{log_path}{self.player}_weighted_valid', render=True, frames=1)
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
            if self.f_max < n_factories: self.f_max = n_factories
            self.wgt = n_factories / self.f_max
            # получаем матрицу свободных мест
            valid = self.game_state.board.valid_spawns_mask.astype(int)
            rubble = self.game_state.board.rubble
            # определяем сколько ресурсов давать фабрике
            metal = ceil(self.game_state.teams[self.player].metal / n_factories)
            water = ceil(self.game_state.teams[self.player].water / n_factories)
            # получаем позицию для установки фабрики
            res = self.weighted * valid + valid
            # правим веса на основе щебня
            # TODO
            potential_spawns = np.array(list(zip(*np.where(res==np.max(res)))))
            spawn_i, min = 0, 1000
            #for i, spawn in enumerate(potential_spawns):
            #    slice = rubble[spawn[0]-1:spawn[0]+2, spawn[1]-1:spawn[1]+2]
            #    sum = np.sum(slice)
            #    if sum < min:
            #        spawn_i = i
            #        min = sum
            spawn_loc = potential_spawns[spawn_i]
            
            # --- лог картинок ---
            log_path = createFolder(['log', 'step'])
            toImage(res, f'{log_path}{self.player}_weighted_valid', render=True, frames=self.f_max)
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