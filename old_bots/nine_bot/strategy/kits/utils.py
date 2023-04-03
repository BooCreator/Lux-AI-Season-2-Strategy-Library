import numpy as np
from math import ceil, floor, sqrt
from datetime import datetime

#from pathfinding.core.diagonal_movement import DiagonalMovement
#from pathfinding.core.grid import Grid
#from pathfinding.finder.a_star import AStarFinder as Finder
#from pathfinding.finder.best_first import BestFirst as Finder
#from pathfinding.finder.bi_a_star import BiAStarFinder as Finder
#from pathfinding.finder.breadth_first import BreadthFirstFinder as Finder
#from pathfinding.finder.dijkstra import DijkstraFinder as Finder
#from pathfinding.finder.ida_star import IDAStarFinder as Finder
#from pathfinding.finder.msp import MinimumSpanningTree as Finder

#from strategy.kits.decorators import time_wrapper

try:
    from lux.config import EnvConfig
    from lux.kit import GameState
    from lux.unit import Unit

    env = EnvConfig()
except:
    env = None
    class Unit: pass
    class GameState: pass
# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
# ----- Номера ресурсов для удобства (в Lux не указаны)
# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
class RES:
    ice = 0
    ore = 1
    water = 2
    metal = 3
    energy = 4
# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
# ----- Сохранить матрицу как pandas.csv --------------------------------------------------------------------
# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
def toPandas(mx:np.ndarray, name:str) -> bool:
    ''' Сохранить матрицу как pandas.csv '''
    try:
        import pandas as pd
        pd.DataFrame(mx).to_csv(f'log/{name}.csv', index=False)
        return True
    except:
        return False
# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
# ----- Получить квадрат координат вокруг точки -------------------------------------------------------------
# ------- Пример: X  X  X  X --------------------------------------------------------------------------------
# -------         X [0, 0] X --------------------------------------------------------------------------------
# -------         X  X  X  X --------------------------------------------------------------------------------
# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
def getRect(X:int, Y:int=None, rad:int=1, borders:bool=True, as_matrix:bool=False):
    ''' Получить квадрат координат вокруг точки '''
    if Y is None and (type(X) is np.ndarray or type(X) is list):
        X, Y = X[0], X[1]
    if as_matrix:
        res = np.zeros((rad*2+1, rad*2+1),dtype=int)
        x,y = getRect(1, 1, rad=rad, borders=borders, as_matrix=False)
        for x,y in zip(x, y):
            res[x, y] = 1
        return res
    else:
        x, y = [], []
        for r in range(-rad, rad + 1):
            for k in range(-rad, rad + 1):
                ny, nx = X-k, Y-r
                if not borders or nx > -1 and ny > -1:
                    x.append(X-k)
                    y.append(Y-r)
        return x, y
# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
# ----- Получить круг координат вокруг точки ----------------------------------------------------------------
# ------- Пример:    X  X    --------------------------------------------------------------------------------
# -------         X [0, 0] X --------------------------------------------------------------------------------
# -------            X  X    --------------------------------------------------------------------------------
# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
def getRad(X:int, Y:int=None, rad:int=1, borders:bool=True, as_matrix:bool=False):
    ''' Получить круг координат вокруг точки '''
    if Y is None and (type(X) is np.ndarray or type(X) is list):
        X, Y = X[0], X[1]
    if as_matrix:
        res = np.zeros((rad*2+1, rad*2+1),dtype=int)
        x,y = getRad(1, 1, rad=rad, borders=borders, as_matrix=False)
        for x,y in zip(x, y):
            res[x, y] = 1
        return res
    else:
        x, y = [], []
        for r in range(-rad, rad + 1):
            for k in range(-rad, rad + 1):
                if abs(r)+abs(k) < (rad*rad)/2 + 1:
                    ny, nx = X-k, Y-r
                    if not borders or nx > -1 and ny > -1:
                        x.append(X-k)
                        y.append(Y-r)
        return x, y
# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
# ----- Распространение ячейки ------------------------------------------------------------------------------
# ------- Пример:    3  3    --- ищем find = 1 --------------------------------------------------------------
# -------         2 [1, 1] 2 --- распространяем по val = 2 --------------------------------------------------
# -------            3  3    --- ограничивая всё max = 3 ----------------------------------------------------
# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
def spreadCell(matrix:np.ndarray, rad:int=3, *, find:int=1, val:int=1, max:int=100, func=getRad)->np.ndarray:
    ''' Распространение ячейки '''
    result = matrix.copy()
    for z in range(rad, 0, -1):
        for x, y in zip(*np.where(matrix == find)):
            for rx, ry in zip(*func(x, y, z)):
                if (rx > -1 and ry > -1) and (rx < matrix.shape[0] and ry < matrix.shape[1]):
                    result[rx,ry] += val
    if val < 0: result *= -1
    result = np.where(result <= abs(max), result, abs(max))
    if val < 0: result *= -1
    return result
# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
# ----- Нормализация таблицы --------------------------------------------------------------------------------
# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
def normalize(matrix:np.ndarray, mMax:int=None) -> np.ndarray:
    ''' Нормализация таблицы '''
    mMax = mMax if mMax is not None else np.max(matrix)
    result = matrix / np.max(matrix) * mMax
    return result
# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
# ----- Сжатие данных матрицы -------------------------------------------------------------------------------
# ------ Пример: 1 0 1 2    0 0 8 0 --- берётся срез size размера, центр - центр матрицы size X size --------
# ------         2 1 2 3 -\ 0 6 7 0 --- если есть 0, то в центральную позицию среза ставится 0 --------------
# ------         0 2 1 1 -/ 0 0 9 0 --- если 0 нет, то в центральную позицию добавляем сумму среза ----------
# ------         2 0 4 3    0 0 0 0 -------------------------------------------------------------------------
# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
def conv(matrix:np.ndarray, size:int, func=np.sum) -> np.ndarray:
    ''' Сжатие данных матрицы '''
    result = matrix.copy()
    for x in range(2, matrix.shape[0] - 1):
        for y in range(2, matrix.shape[1] - 1):
            s, e = x - floor(size[0]/2), y - floor(size[1]/2)
            mx = [i for i in range(s, min(matrix.shape[0], size[0]+s))]
            my = [i for i in range(e, min(matrix.shape[1], size[1]+e))]
            res = []
            for ry in my:
                res.append(list(matrix[[ry], mx]))
            res = np.array(res)
            result[y, x] = 0 if len(np.where(res==0)[0]) > 0 else func(res)
    return result
# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
# ----- Определить направление движения до точки (из кода Lux) ----------------------------------------------
# ------- Направления (0 = center, 1 = up, 2 = right, 3 = down, 4 = left) -----------------------------------
# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
def direction_to(src:np.ndarray, target:np.ndarray, block=None) -> int:
    ''' Определить направление движения до точки (из кода Lux) 
        * 0 - center, 1 - up, 2 - right, 3 - down, 4 - left '''
    block = block if block is not None else []
    ds = target - src
    dx, dy = ds[0], ds[1]
    if dx == 0 and dy == 0: return 0

    if (abs(dx) > abs(dy)) and not (2 in block or 4 in block):
        return 2 if dx > 0 else 4
    elif not (3 in block or 1 in block):
        return 3 if dy > 0 else 1
    else: return 0
# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
# ----- Получить маршрут движения для робота по навправлениям [left, up, up, right, ...] --------------------
# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
def getPath(dec:np.ndarray, to:np.ndarray, locked_field:np.ndarray=None, steps:int=20):
    ''' Получить маршрут движения для робота по навправлениям
        * [4 (left), 1 (up), 1 (up), 2 (right), ...] '''
    path, block, n = [], [], 0
    move_from = dec.copy()
    direction = direction_to(move_from, to, block)
    while(direction != 0 and n < steps):
        n, x, y = n+1,  move_from[0], move_from[1]
        if direction == 1:
            y -= 1
        elif direction == 3:
            y += 1
        elif direction == 2:
            x += 1
        elif direction == 4:
            x -= 1
        if locked_field is None or locked_field[x, y] != 0:
            move_from = np.array([x, y])
            if direction > 0:
                path.append({'d':direction, 'loc':move_from.copy()})
            block.clear()
        elif len(block) < 4:
            block.append(direction)
        else: break
        direction = direction_to(move_from, to, block=block)
    return path
# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
# ----- Поиск маршрута движения для робота по навправлениям [left, up, up, right, ...] ----------------------
# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
def checkMove(x:int, y: int, size=(3,3)) -> bool:
    return not (x < 0 or y < 0 or x >= size[0] or y >= size[1])
class Path:
    paths = []
    complete_paths = []
    def __init__(self, start:np.ndarray) -> None:
        self.paths = [[start]]
        self.result = []
        self.complete_paths = []

    def move(self, field:np.ndarray, to: np.ndarray) -> bool:
        new_paths = []
        comp_paths = []
        for path in self.paths:
            alloy = []
            for x, y in zip(*getRad(path[-1][0], path[-1][1])):
                if checkMove(x, y, field.shape) and field[x, y] == 1:
                    if x == to[0] and y == to[1]:
                        alloy = [[x, y]]
                        break
                    elif not (x == path[-1][0] and y == path[-1][1]):
                        alloy.append([x, y])
            if len(alloy) > 0:
                for i in range(len(alloy) - 1):
                    tmp = path.copy()
                    tmp.append(alloy[i])
                    new_paths.append(tmp)
                    field[alloy[i][0], alloy[i][1]] = 2
                path.append(alloy[-1])
                field[alloy[-1][0], alloy[-1][1]] = 2
                if alloy[-1][0] == to[0] and alloy[-1][1] == to[1]:
                    self.result = path
                    comp_paths.append(path)
            else:
                comp_paths.append(path)
        for path in new_paths:
            self.paths.append(path)
        for path in comp_paths:
            self.complete_paths.append(path)
            self.paths.remove(path)
    
    def has_paths(self) -> bool:
        return len(self.paths) > 0

    def get_result(self, to: np.ndarray = None) -> np.ndarray:
        paths = extended([self.complete_paths, self.paths])
        if len(self.result) == 0 and to is not None:
            min_path, min_pos, min_len = 0, 0, 10_000
            for i, path in enumerate(paths):
                for j, xy in enumerate(path):
                    vec = np.array([xy[0] - to[0], xy[1] - to[1]], dtype=np.int32)
                    vec_len = sqrt(vec[0]*vec[0] + vec[1]*vec[1])
                    if vec_len < min_len:
                        min_path, min_pos, min_len = i, j, vec_len
            self.result = paths[min_path][:min_pos+1]
        return self.result

def findPathOld(dec:np.ndarray, to:np.ndarray, locked_field:np.ndarray=None, steps:int=20):
    ''' Получить маршрут движения для робота по навправлениям
        * [4 (left), 1 (up), 1 (up), 2 (right), ...] '''
    paths = Path(dec)
    field = locked_field.copy() if locked_field is not None else np.ones((env.map_size, env.map_size), dtype=int)
    field[dec[0], dec[1]] = 0

    while paths.has_paths() and np.min(field) != np.max(field) and steps > 0:
        paths.move(field, to)
        steps -= 1
    result = paths.get_result(to)
    if len(result) > 0:
        tmp = []
        for i in range(1, len(result)):
            tmp.append({'d': direction_to(np.array(result[i-1]), np.array(result[i])), 'loc': np.array(result[i])})
        result = tmp
    return result
# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
# ----- Поиск маршрута движения для робота по навправлениям [left, up, up, right, ...] ----------------------
# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
#def setPathType(arr):
#    if len(arr) > 0:
#        if type(arr[0]) is tuple or type(arr[0]) is list: return arr
#        elif hasattr(arr[0], 'x') and hasattr(arr[0], 'y'):
#            return [[item.x, item.y] for item in arr]
#    return []
#def toLuxlist(arr):
#    return [arr[1], arr[0]]
#def findPath(dec:np.ndarray, to:np.ndarray, locked_field:np.ndarray=None, steps:int=20):
#    ''' Получить маршрут движения для робота по навправлениям
#        * [4 (left), 1 (up), 1 (up), 2 (right), ...] '''
#    field = locked_field.copy() if locked_field is not None else np.ones((env.map_size, env.map_size), dtype=int)
#    field[dec[0], dec[1]] = 0
#
#    grid = Grid(matrix=field.transpose())
#    start = grid.node(dec[1], dec[0])
#    end = grid.node(to[1], to[0])
#    finder = Finder(diagonal_movement=DiagonalMovement.never)
#    
#    result, __ = finder.find_path(start, end, grid)
#    if len(result) > 0:
#        tmp = []
#        if type(result[0]) is tuple or type(result[0]) is list:
#            for i in range(1, len(result)):
#                tmp.append({'d': direction_to(np.array(toLuxlist(result[i-1])), np.array(toLuxlist(result[i]))), 'loc': np.array(toLuxlist(result[i]))})
#        #elif hasattr(result[0], 'x') and hasattr(result[0], 'y'):
#        #    for i in range(1, len(result)):
#        #        tmp.append({'d': direction_to(np.array([result[i-1].x, result[i-1].y]), np.array([result[i].x, result[i].y])), 'loc': np.array([result[i].x, result#[i].y])})
#        result = tmp
#    return result
# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
# ----- Найти ближайшую фабрику -----------------------------------------------------------------------------
# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
def findClosestFactory(pos:np.ndarray, factory_tiles:np.ndarray, factory_units:np.ndarray):
    ''' Найти ближайшую фабрику '''
    factory_distances = np.mean((factory_tiles - pos) ** 2, 1)
    closest_factory_tile = factory_tiles[np.argmin(factory_distances)]
    closest_factory = factory_units[np.argmin(factory_distances)]
    adjacent_to_factory:bool = np.mean((closest_factory_tile - pos) ** 2) == 0
    return closest_factory, adjacent_to_factory
# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
# ----- Найти ближайший тайл/ресурс -------------------------------------------------------------------------
# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
def findClosestTile(pos:np.ndarray, tile_map:np.ndarray, *, lock_map:np.ndarray=None):
    ''' Найти ближайший тайл/ресурс '''
    if lock_map is None: lock_map = np.ones(tile_map.shape, dtype=int)
    closest_tile = pos
    tile_locations = np.argwhere((tile_map * lock_map) > 0)
    if len(tile_locations) > 0:
        tile_distances = np.mean((tile_locations - pos) ** 2, 1)
        closest_tile: np.ndarray = tile_locations[np.argmin(tile_distances)]
    return closest_tile
# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
# ----- Проверит что робот на ресурсе -----------------------------------------------------------------------
# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
def onResourcePoint(pos:np.ndarray, tile_map:np.ndarray):
    ''' Найти ближайший тайл/ресурс '''
    return tile_map[pos[0], pos[1]] == 1
# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
# ----- Рассчитать, сколько мы можем копнуть ----------------------------------------------------------------
# ------- count - сколько мы хотим накопать, по умолчанию и макс - грузоподъёмность робота ------------------
# ------- has_energy - сколько энергии у нас есть -----------------------------------------------------------
# ------- dig_type - тип копания ----------------------------------------------------------------------------
# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
class DIG_TYPES:
    ''' Тип копания - RESOURCE - 0, RUBBLE = 1, LICHEN = 2 '''
    RESOURCE = 0
    RUBBLE = 1
    LICHEN = 2
def calcDigCount(unit: Unit, *, count:int=1000, has_energy:int=None, reserve_energy:int=0, dig_type:int = DIG_TYPES.RESOURCE):
    ''' Рассчитать, сколько мы можем копнуть '''
    dig_cost = env.ROBOTS[unit.unit_type].DIG_COST
    energy = min(unit.power, has_energy or env.ROBOTS[unit.unit_type].BATTERY_CAPACITY) - reserve_energy
    gain = 1
    if dig_type == DIG_TYPES.LICHEN:
        gain = env.ROBOTS[unit.unit_type].DIG_LICHEN_REMOVED
    elif dig_type == DIG_TYPES.RUBBLE:
        gain = env.ROBOTS[unit.unit_type].DIG_RUBBLE_REMOVED
    # --- если копаем ресурс, то ограничиваем тем, сколько можем накопать ---
    else: # elif dig_type == DIG_TYPES.RESOURCE:
        space = env.ROBOTS[unit.unit_type].CARGO_SPACE
        free = space - (unit.cargo.ice + unit.cargo.ore + unit.cargo.water + unit.cargo.metal)
        count = min(free, count) if count is not None else min(free, space)
        gain = env.ROBOTS[unit.unit_type].DIG_RESOURCE_GAIN
    
    dig_count = min(floor(energy/dig_cost), ceil(count/gain))
    return dig_count, dig_count*dig_cost, dig_count*gain
    
def calcDigCountOld(unit, *, count:int=1000, on_factory=None, reserve_cost:int=0, dig_type:int = DIG_TYPES.RESOURCE):
    ''' Рассчитать, сколько мы можем копнуть '''
    free = 1000
    if dig_type == DIG_TYPES.RESOURCE:
        space = env.ROBOTS[unit.unit_type].CARGO_SPACE
        free = space - (unit.cargo.ice + unit.cargo.ore + unit.cargo.water + unit.cargo.metal)
    count = min(free, count) if count is not None else min(free, space)
    gain = env.ROBOTS[unit.unit_type].DIG_RESOURCE_GAIN
    dig_cost = env.ROBOTS[unit.unit_type].DIG_COST
    e_max = env.ROBOTS[unit.unit_type].BATTERY_CAPACITY
    energy = min(e_max, unit.power + on_factory.power) if on_factory is not None else unit.power
    energy -= reserve_cost
    dig_count = min(floor(energy/dig_cost), floor(count/gain))
    return dig_count, dig_count*dig_cost
# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
# ----- Объединить списки -----------------------------------------------------------------------------------
# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
def extended(arr:list) -> list:
    ''' Объединить списки '''
    res = []
    for item in arr: 
        res.extend(item)
    return res
# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
# ----- Получить из игровой среди все массивы с данными -----------------------------------------------------
# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
def getResFromState(game_state):
    ''' Получить из игровой среди все массивы с данными '''
    return game_state.board.ice, game_state.board.ore, game_state.board.rubble, game_state.board.valid_spawns_mask.astype(int)
# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
# ----- Получить список действий движения со стоимостью по энергии ------------------------------------------
# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
#@time_wrapper('getMoveActions')
def getMoveActions(game_state, unit, *, path:list=None, dec:np.ndarray=None, to:np.ndarray=None, 
                    locked_field:np.ndarray=None, repeat:int=0, n:int=1, has_points: bool=False,
                    steps:int=25):
    ''' Получить список действий движения со стоимостью по энергии 
        * locked_field: 0 - lock, 1 - alloy '''
    actions = []
    points = []
    move_cost = 0
    pos = unit.pos
    if path is None: path = findPathOld(pos if dec is None else dec, pos if to is None else to, locked_field, steps=steps)
    for direction in path:
        unit.pos = direction['loc']
        move_cost += unit.move_cost(game_state, direction['d']) or 0
        actions.append(unit.move(direction['d'], repeat=repeat, n=n))
        points.append(direction['loc'])
    unit.pos = pos
    return (actions, move_cost, points) if has_points else (actions, move_cost)

# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
# ----- Получить список действий движения со стоимостью по энергии ------------------------------------------
# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
# a[1] = direction (0 = center, 1 = up, 2 = right, 3 = down, 4 = left)
move_deltas = np.array([[0, 0], [0, -1], [1, 0], [0, 1], [-1, 0]])
#@time_wrapper('findPathActions')
def findPathActions(unit:Unit, game_state:GameState, *, dec:np.ndarray=None, to:np.ndarray=None, 
                    lock_map:np.ndarray=None, steps:int=25):
    ''' Получить список действий движения со стоимостью по энергии 
        * lock_map: 0 - lock, 1 - alloy '''
    actions, points, move_cost, pos = [], [], [], unit.pos

    for direction in findPathOld(pos if dec is None else dec, pos if to is None else to, lock_map, steps=steps):
        unit.pos = direction['loc']
        points.append(direction['loc'])
        move_cost.append(unit.move_cost(game_state, direction['d']) or 0)
        actions.append(unit.move(direction['d'], repeat=0, n=1))
        
    unit.pos = pos
    return actions, move_cost

# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
# ----- Получить список действий движения со стоимостью по энергии ------------------------------------------
# ------- * [4 (left), 1 (up), 1 (up), 2 (right), ...]
# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
def getNextMovePos(unit) -> np.ndarray:
    if len(unit.action_queue) > 0:
        action = unit.action_queue[0]
        if action[0] == 0:
            if action[1] == 1:
                return [unit.pos[0], unit.pos[1]-1]
            elif action[1] == 2:
                return [unit.pos[0]+1, unit.pos[1]]
            elif action[1] == 3:
                return [unit.pos[0], unit.pos[1]+1]
            elif action[1] == 4:
                return [unit.pos[0]-1, unit.pos[1]]
    return unit.pos
# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
# ----- Получить расстояние между клетками ------------------------------------------------------------------
# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
def getDistance(dec:np.ndarray, to:np.ndarray) -> int:
    ''' Найти ближайшую фабрику '''
    dec = dec if type(dec) is np.ndarray else np.array(dec)
    to = to if type(to) is np.ndarray else np.array(to)
    return np.sum(np.abs(dec-to))

#print(findClosestFactory([2, 3], [0,0]))
#[0, 0] -> [0, 1] -> [0, 2] -> [1, 2]
#[0, 0] -> [0, 1] -> [0, 2] -> [1, 2] -> [2, 2]
#[0, 0] -> [0, 1] -> [0, 2] -> [0, 3] -> [1, 3] -> [2, 3]

#def getRange(pos=[], size=10, vals=[0,1]):
#    res = [vals[0] for i in range(size)]
#    if len(pos) > 0:
#        for i in pos: res[i] = vals[1]
#    return res
#
#size=10
#ore = []
#for i in [[],
#            [i if i != 9 else 0 for i in range(0, size)],
#            [],
#            [i if i != 2 else 0  for i in range(0, size)],
#            [],
#            [i if i != 5 else 0  for i in range(0, size)],
#            [],
#            [i if i != 1 else 0  for i in range(0, size)],
#            [],
#            [i if i != 9 else 0  for i in range(0, size)] # 
#        ]:
#    ore.append(getRange(i, size))
#ore = np.array(ore)
#
#print(ore)
#print('-'*50)
#
#s, e = 0, 0
#x, y = s, e
#ore[x, y] = 1
## 1 - up, 2 - right, 3 - down, 4 - left
## [2, 3, 3, 2, 2, 1, 2, 2, 2]
#
#for step in findPathOld(dec=[x, y], to=[9, 4], locked_field=np.ones((size, size), dtype=int)-ore, steps=1000):
#    if step['d'] == 1:
#        y -= 1
#    elif step['d'] == 2:
#        x += 1
#    elif step['d'] == 3:
#        y += 1
#    elif step['d'] == 4:
#        x -= 1
#    ore[x, y] = 2
#ore[8, 4] = 4
#ore[s, e] = 3
#ore[x, y] = 3
#print(ore)
#
#
#
#
#size=10
#s, e = 0, 0
#x, y = s, e
#matrix = []
#for i in [[],
#            [i if i != 9 else 0 for i in range(0, size)],
#            [],
#            [i if i != 2 else 0  for i in range(0, size)],
#            [],
#            [i if i != 5 else 0  for i in range(0, size)],
#            [],
#            [i if i != 1 else 0  for i in range(0, size)],
#            [],
#            [i if i != 9 else 0  for i in range(0, size)] # 
#        ]:
#    matrix.append(getRange(i, size, vals=[1,0]))
#
#grid = Grid(matrix=matrix)
#start = grid.node(x, y)
#end = grid.node(4, 9)
#
#finder = Finder(diagonal_movement=DiagonalMovement.never)
#time = datetime.now()
#path, runs = finder.find_path(start, end, grid)
#print('time:', datetime.now()-time)
#print(grid.grid_str(path=path, start=start, end=end))