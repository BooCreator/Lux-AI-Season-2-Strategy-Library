import numpy as np
from math import ceil, floor, sqrt

from strategy.kits.decorators import time_wrapper

#from strategy.kits.decorators import time_wrapper

# a[1] = direction (0 = center, 1 = up, 2 = right, 3 = down, 4 = left)
move_deltas = np.array([[0, 0], [0, -1], [1, 0], [0, 1], [-1, 0]])
moves_list = np.array([[0,  3,  1], [2, -1, -1], [4, -1, -1]])

from lux.config import EnvConfig
from lux.kit import GameState
from lux.unit import Unit
env = EnvConfig()

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

# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
# ----- Получить список действий движения со стоимостью по энергии (old strategies) -------------------------
# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
def getMoveActions(game_state:GameState, unit:Unit, *, path:list=None, dec:np.ndarray=None, to:np.ndarray=None, 
                    locked_field:np.ndarray=None, repeat:int=0, n:int=1, has_points: bool=False,
                    steps:int=25):
    ''' Получить список действий движения со стоимостью по энергии 
        * locked_field: 0 - lock, 1 - alloy '''
    actions, points, move_cost, pos  = [], [], 0, unit.pos
    if path is None: path = findPath(pos if dec is None else dec, pos if to is None else to, locked_field, steps=steps, old=True)
    for direction in path:
        unit.pos = direction['loc']
        move_cost += unit.move_cost(game_state, direction['d']) or 0
        actions.append(unit.move(direction['d'], repeat=repeat, n=n))
        points.append(direction['loc'])
    unit.pos = pos
    return (actions, move_cost, points) if has_points else (actions, move_cost)
# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
# ----- Получить координаты следующего шага робота ----------------------------------------------------------
# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
def getNextMovePos(unit:Unit) -> np.ndarray:
    ''' Получить координаты следующего шага робота '''
    result = unit.pos.copy()
    if len(unit.action_queue) > 0:
        action = unit.action_queue[0]
        if action[0] == 0:
            return result + move_deltas[action[1]]
    return result
# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
# ----- Получить цену в энергии шага робота -----------------------------------------------------------------
# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
def getNextMoveEnergyCost(gs:GameState, unit:Unit) -> int:
    result = 0
    if len(unit.action_queue) > 0:
        action = unit.action_queue[0]
        if action[0] == 0:
            return unit.move_cost(gs, action[1])
    return result
# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
# ----- Вернуть матрицу ходов робота ------------------------------------------------------------------------
# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
def getMoveMap(unit:Unit, shape:tuple=(48,48)) -> np.ndarray:
    result = np.zeros(shape, dtype=int)
    pt, n = unit.pos, 0
    for action in unit.action_queue:
        n += action[5]
        if action[0] == 0:
            pt += move_deltas[action[1]]
            result[pt[0], pt[1]] = n
    return result
# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
# ----- Получить расстояние между клетками в шагах ----------------------------------------------------------
# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
def getDistance(dec:np.ndarray, to:np.ndarray) -> int:
    ''' Получить расстояние между клетками в шагах '''
    dec = dec if type(dec) is np.ndarray else np.array(dec)
    to = to if type(to) is np.ndarray else np.array(to)
    return np.sum(np.abs(dec-to))
# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
# ----- Найти ближайшую фабрику -----------------------------------------------------------------------------
# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
def findClosestFactory(dec:np.ndarray, tiles:np.ndarray, units:np.ndarray):
    ''' Найти ближайшую фабрику '''
    distances = np.mean((tiles - dec) ** 2, 1)
    closest_factory = units[np.argmin(distances)]
    return closest_factory
# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
# ----- Найти ближайший тайл/ресурс -------------------------------------------------------------------------
# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
def findClosestTile(dec:np.ndarray, tile_map:np.ndarray, *, lock_map:np.ndarray=None, dec_is_none:bool=True):
    ''' Найти ближайший тайл/ресурс '''
    if lock_map is None: lock_map = np.ones(tile_map.shape, dtype=int)
    tile_locations = np.argwhere((tile_map * lock_map) > 0)
    closest_tile = dec if dec_is_none else None
    if len(tile_locations) > 0:
        tile_distances = np.mean((tile_locations - dec) ** 2, 1)
        closest_tile: np.ndarray = tile_locations[np.argmin(tile_distances)]
    return closest_tile
# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
# ----- Получить из игровой среди все массивы с данными -----------------------------------------------------
# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
def getResFromState(game_state:GameState):
    ''' Получить из игровой среди все массивы с данными '''
    return game_state.board.ice, game_state.board.ore, game_state.board.rubble, game_state.board.valid_spawns_mask.astype(int)
# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
# ----- Объединить списки -----------------------------------------------------------------------------------
# ----- [[1, 2, 3], [4, 5], ...] -> [1, 2, 3, 4, 5] ---------------------------------------------------------
# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
def extended(arr:list) -> list:
    ''' Объединить списки '''
    res = []
    for item in arr: 
        res.extend(item)
    return res
# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
# ----- Объединить словари ----------------------------------------------------------------------------------
# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
def dict_extended(arr:list) -> dict:
    ''' Объединить списки '''
    res = {}
    for key, value in arr.items(): 
        res[key] = value
    return res
# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
# ----- Определить направление движения до точки (из кода Lux) ----------------------------------------------
# ------- Направления (0 = center, 1 = up, 2 = right, 3 = down, 4 = left) -----------------------------------
# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
def direction_to(dec:np.ndarray, to:np.ndarray, block=None) -> int:
    ''' Определить направление движения до точки (из кода Lux) 
        * 0 - center, 1 - up, 2 - right, 3 - down, 4 - left '''
    if type(dec) is list: dec = np.array(dec)
    if type(to) is list: to = np.array(to)
    block = block if block is not None else []
    ds = to - dec
    res = int(moves_list[ds[0], ds[1]])
    return 0 if res in block else res
# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
# ----- Получить квадрат координат вокруг точки -------------------------------------------------------------
# ------- Пример: X  X  X  X --------------------------------------------------------------------------------
# -------         X [0, 0] X --------------------------------------------------------------------------------
# -------         X  X  X  X --------------------------------------------------------------------------------
# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
def getRect(dec:np.ndarray, rad:int=1, borders:bool=True, as_matrix:bool=False):
    ''' Получить квадрат координат вокруг точки '''
    if as_matrix: return np.zeros((rad*2+1, rad*2+1), dtype=int)
    result = []
    for r in range(-rad, rad + 1):
        for k in range(-rad, rad + 1):
            ny, nx = dec[0]-k, dec[1]-r
            if not borders or nx > -1 and ny > -1:
                result.append([dec[0]-k, dec[1]-r])
    return result
# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
# ----- Получить круг координат вокруг точки ----------------------------------------------------------------
# ------- Пример:    X  X    --------------------------------------------------------------------------------
# -------         X [0, 0] X --------------------------------------------------------------------------------
# -------            X  X    --------------------------------------------------------------------------------
# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
def radFunc(x:int, y:int, dec:np.ndarray) -> int:
    return pow(x-dec[0], 2)+pow(y-dec[1], 2)
def getRad(dec:np.ndarray, rad:int=1, borders:bool=True, as_matrix:bool=False, size:int=(48,48)):
    ''' Получить круг координат вокруг точки '''
    if as_matrix:
        shape = rad*2+1
        result = np.zeros((shape, shape), dtype=int)
        for x in range(shape):
            for y in range(shape):
                result[x, y] = 1 if radFunc(x, y, [floor(shape/2), floor(shape/2)]) <= pow(rad, 2) else 0
        return result
    else:
        result = []
        for r in range(-rad, rad + 1):
            for k in range(-rad, rad + 1):
                if abs(r)+abs(k) < (rad*rad)/2 + 1:
                    ny, nx = dec[0]-k, dec[1]-r
                    if not borders or nx > -1 and ny > -1 and nx < size[1] and ny < size[0]:
                        result.append([dec[0]-k, dec[1]-r])
        return result
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
        for [x, y] in np.argwhere(matrix == find):
            for [rx, ry] in func([x, y], z):
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
# ----- Поиск маршрута движения для робота по навправлениям [left, up, up, right, ...] ----------------------
# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
class Path:

    max_steps = 20
    step = 0

    def __init__(self, dec:np.ndarray, field:np.ndarray, steps:int=20) -> None:
        self.max_steps = steps
        self.field = field
        self.result = []
        self.paths = []
        self.dec = np.array(dec) if type(dec) is list else dec
        self.step = 0
        self.slice = np.array([0, 0])

    def window(self, to:np.ndarray, minW:int=5, minH:int=5):
        s_x = min(self.dec[0], to[0])
        e_x = min(self.dec[1], to[1])
        s_y = max(self.dec[0], to[0])+1
        e_y = max(self.dec[1], to[1])+1
        if s_y-s_x < minW:
            x = minW-(s_y-s_x)
            a = ceil(x/2)
            s_x -= a
            s_y += x-a
        if e_y-e_x < minH:
            x = minH-(e_y-e_x)
            a = ceil(x/2)
            e_x -= x-a
            e_y += a
        self.field = self.field[max(s_x, 0):max(s_y, 0), max(e_x, 0):max(e_y, 0)]
        self.slice = np.array([max(s_x, 0), max(e_x, 0)])
        self.dec -= self.slice
        return to - self.slice

    def find(self, to:np.ndarray) -> list:
        if not self.find_basic(to):
            to = self.window(np.array(to) if type(to) is list else to)
            self.paths = [[self.dec]]
            while not self.is_end():
                self.step += 1
                self.move(to)
        return self.get_result(to)

    def checkSlice(self, s_x, s_y, e_x, e_y):
        slice = self.field[s_x:s_y, e_x:e_y]
        return len(slice) == 0 or np.sum(slice) == max(slice.shape[0], slice.shape[1])
    
    def find_basic(self, to:np.ndarray) -> bool:
        self.result = []
        s_0 = self.dec[0]+1 if self.dec[0] < to[0] else to[0]
        e_0 = to[0]+1 if self.dec[0] < to[0] else self.dec[0]
        s_1 = self.dec[1]+1 if self.dec[1] < to[1] else to[1]
        e_1 = to[1]+1 if self.dec[1] < to[1] else self.dec[1]

        if self.checkSlice(self.dec[0], self.dec[0]+1, s_1, e_1):
            self.calcPath(self.dec, to, o='h')
            if self.checkSlice(s_0, e_0, to[1], to[1]+1):
                self.calcPath(self.paths[-1][-1], to, True, o='v')
                self.result = self.paths[-1]
                self.paths.clear()
                return True
            
        if self.checkSlice(s_0, e_0, self.dec[1], self.dec[1]+1):
            self.calcPath(self.dec, to, o='v')
            if self.checkSlice(to[0], to[0]+1, s_1, e_1):
                self.calcPath(self.paths[-1][-1], to, True, o='h')
                self.result = self.paths[-1]
                self.paths.clear()
                return True
        return False

    def calcPath(self, dec:np.ndarray, to:np.ndarray, append_last:bool=False, *, o:str='h') -> list:
        result = [] if append_last else [dec]
        if o=='h':
            s = dec[1]+1 if dec[1] < to[1] else dec[1]-1
            e = to[1]+1 if dec[1] < to[1] else to[1]-1
            i = 1 if dec[1] < to[1] else -1
            for x in range(s, e, i):
                result.append(np.array([dec[0], x]))
        else:
            s = dec[0]+1 if dec[0] < to[0] else dec[0]-1
            e = to[0]+1 if dec[0] < to[0] else to[0]-1
            i = 1 if dec[0] < to[0] else -1
            for y in range(s, e, i):
                result.append(np.array([y, dec[1]]))
        if append_last and len(self.paths) > 0:
            self.paths[-1].extend(result)
        else:
            self.paths.append(result)

    def move(self, to:np.ndarray) -> bool:
        new_paths = []
        for i, path in enumerate(self.paths.copy()):
            alloy = []
            for [x, y] in getRad(path[-1], size=self.field.shape):
                if self.field[x, y] == 1:
                    self.field[x, y] = 2
                    if x != to[0] or y != to[1]:
                        alloy.append([x, y])
                    else:
                        alloy = [[x, y]]
                        break
            if len(alloy) > 0:
                if alloy[0][0] == to[0] and alloy[0][1] == to[1]:
                    path.append(alloy[0])
                    self.result = path
                    self.paths.clear()
                    break
                for i in range(len(alloy)):
                    tmp = path.copy()
                    tmp.append(alloy[i])
                    new_paths.append(tmp)
            elif len(self.paths) > 1:
                self.paths.remove(path)
        for path in new_paths:
            self.paths.append(path)
    
    def is_end(self) -> bool:
        return len(self.paths) == 0 or self.step > self.max_steps or np.min(self.field) == np.max(self.field)

    def get_result(self, to:np.ndarray=None) -> np.ndarray:
        if len(self.result) == 0 and to is not None: 
            min_path, min_pos, min_len = 0, 0, 10_000
            for i, path in enumerate(self.paths):
                for j, xy in enumerate(path):
                    vec = np.array([xy[0] - to[0], xy[1] - to[1]], dtype=np.int32)
                    vec_len = sqrt(vec[0]*vec[0] + vec[1]*vec[1])
                    if vec_len < min_len:
                        min_path, min_pos, min_len = i, j, vec_len
            self.result = self.paths[min_path][:min_pos+1]
        return np.array([item + self.slice for item in self.result])

def findPath(dec:np.ndarray, to:np.ndarray, lock_map:np.ndarray=None, steps:int=20, old=False):
    ''' Получить маршрут движения для робота по навправлениям
        * [4 (left), 1 (up), 1 (up), 2 (right), ...] '''
    if dec[0] == to[0] and dec[1] == to[1]: return ([], []) if not old else ([])
    field = lock_map.copy() if lock_map is not None else np.ones((env.map_size, env.map_size), dtype=int)
    field[dec[0], dec[1]] = 0
    result, points, prev_step = [], [], dec

    path = Path(dec.copy(), field, steps)

    for step in path.find(to)[1:]:
        if not old:
            d = direction_to(prev_step, step)
            if len(result) > 0 and result[-1][0] == d: result[-1][2] += 1
            else: result.append([d, step, 1])
            points.append(step)
        else:
            result.append({'d': direction_to(prev_step, step), 'loc': step})
        prev_step = step
    return (points, result) if not old else (result)
# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
# ----- Получить список действий движения со стоимостью по энергии ------------------------------------------
# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
def findPathActions(unit:Unit, game_state:GameState, *, dec:np.ndarray=None, to:np.ndarray=None, 
                    lock_map:np.ndarray=None, steps:int=25, get_move_map:bool=False):
    ''' Получить список действий движения со стоимостью по энергии 
        * lock_map: 0 - lock, 1 - alloy '''
    actions, move_cost, spos = [], [], unit.pos
    lock_map = lock_map if lock_map is not None else np.ones(game_state.board.ice.shape, dtype=int)
    points, moves = findPath(spos if dec is None else dec, spos if to is None else to, lock_map, steps=steps)

    if get_move_map:
        move_map = np.zeros(lock_map.shape, dtype=int)
        for i, point in enumerate(points):
            move_map[point[0], point[1]] = i+1

    for [d, point, n] in moves:
        cost = 0
        unit.pos = point
        actions.append(unit.move(d, repeat=0, n=n))
        for i in range(n):
            cost += unit.move_cost(game_state, d) or 0
        move_cost.append(cost)

    unit.pos = spos
    return (actions, move_cost, move_map) if get_move_map else (actions, move_cost)