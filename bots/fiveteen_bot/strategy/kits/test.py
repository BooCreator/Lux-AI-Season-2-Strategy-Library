from datetime import datetime
from math import ceil, floor, sqrt
from random import randint
import random

import numpy as np

from pathfinding.core.diagonal_movement import DiagonalMovement
from pathfinding.core.grid import Grid
#from pathfinding.finder.a_star import AStarFinder as Finder
#from pathfinding.finder.best_first import BestFirst as Finder
#from pathfinding.finder.bi_a_star import BiAStarFinder as Finder
from pathfinding.finder.breadth_first import BreadthFirstFinder as Finder

from decorators import time_wrapper

moves_list = np.array([[0,  3,  1], [2, -1, -1], [4, -1, -1]])
def direction_to(dec:np.ndarray, to:np.ndarray, block=None) -> int:
    ''' Определить направление движения до точки (из кода Lux) 
        * 0 - center, 1 - up, 2 - right, 3 - down, 4 - left '''
    if type(dec) is list: dec = np.array(dec)
    if type(to) is list: to = np.array(to)
    block = block if block is not None else []
    ds = to - dec
    res = int(moves_list[ds[0], ds[1]])
    return 0 if res in block else res
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
def extended(arr:list) -> list:
    ''' Объединить списки '''
    res = []
    for item in arr: 
        res.extend(item)
    return res


#from pathfinding.finder.dijkstra import DijkstraFinder as Finder
#from pathfinding.finder.ida_star import IDAStarFinder as Finder
#from pathfinding.finder.msp import MinimumSpanningTree as Finder

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

    @time_wrapper('find')
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

def findPath(dec:np.ndarray, to:np.ndarray, lock_map:np.ndarray=None, steps:int=20):
    ''' Получить маршрут движения для робота по навправлениям
        * [4 (left), 1 (up), 1 (up), 2 (right), ...] '''
    if dec == to: return []
    field = lock_map.copy() if lock_map is not None else np.ones((env.map_size, env.map_size), dtype=int)
    field[dec[0], dec[1]] = 0
    result, prev_step = [], dec

    path = Path(dec, field, steps)

    for step in path.find(to)[1:]:
        d = direction_to(prev_step, step)
        if len(result) > 0 and result[-1][0] == d: result[-1][2] += 1
        else: result.append([d, step, 1])
        prev_step = step
    return result




#print(findClosestFactory([2, 3], [0,0]))
##[0, 0] -> [0, 1] -> [0, 2] -> [1, 2]
##[0, 0] -> [0, 1] -> [0, 2] -> [1, 2] -> [2, 2]
##[0, 0] -> [0, 1] -> [0, 2] -> [0, 3] -> [1, 3] -> [2, 3]

def getRange(pos=[], size=10, vals=[0,1]):
    res = [vals[0] for i in range(size)]
    if len(pos) > 0:
        for i in pos: res[i] = vals[1]
    return res

def wnd(arr, s, e):
    const = 5
    s_x = min(s[0], e[0])
    e_x = min(s[1], e[1])
    s_y = max(s[0], e[0])+1
    e_y = max(s[1], e[1])+1
    if s_y-s_x < const:
        x = const-(s_y-s_x)
        a = ceil(x/2)
        s_x -= a
        s_y += x-a
    if e_y-e_x < const:
        x = const-(e_y-e_x)
        a = ceil(x/2)
        e_x -= x-a
        e_y += a
    return arr[max(s_x, 0):max(s_y, 0), max(e_x, 0):max(e_y, 0)]

def basicPaths(arr, s, e):    
        s_0 = s[0]+1 if s[0] < e[0] else e[0]
        e_0 = e[0]+1 if s[0] < e[0] else s[0]
        s_1 = s[1]+1 if s[1] < e[1] else e[1]
        e_1 = e[1]+1 if s[1] < e[1] else s[1]

        print('-'*50)
        print(arr[s[0]:s[0]+1, s_1:e_1])
        print(arr[s_0:e_0, e[1]:e[1]+1])
        
        print('-'*50)
        print(arr[e[0]:e[0]+1, s_1:e_1])
        print(arr[s_0:e_0, s[1]:s[1]+1])

        print('-'*50)

size=100
random.seed(100)
dec = [[0, 0], [5, 5], [2, 5], [2, 9], [4, 2], [2, 5], [5, 0], [0, 0]]
to =  [[5, 5], [0, 0], [2, 9], [2, 5], [2, 5], [4, 2], [4, 2], [0, 0]]
ln = len(dec)

map = np.array([[0 for __ in range(size)] if i%2 != 0 else [1 if randint(0, 100) < 25 else 0 for __ in range(size)] for i in range(size)])

for ind in range(ln):

    [sx, sy] = dec[ind]
    [ex, ey] = to[ind]
    [x, y] = dec[ind]
    ore = map.copy()

    for [d, step, n] in findPath(dec=dec[ind], to=to[ind], lock_map=np.ones((size, size), dtype=int)-ore, steps=1000):
        for i in range(n):
            if d == 1:
                y -= 1
            elif d == 2:
                x += 1
            elif d == 3:
                y += 1
            elif d == 4:
                x -= 1
            ore[x, y] = 2
    ore[sx, sy] = 8
    ore[ex, ey] += 3

    #print(wnd(ore, [sx, sy], [ex, ey]))
    print('-'*3, f'step {ind+1} of {ln}', '-'*15)
    #print(ore)

    