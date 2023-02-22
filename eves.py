import numpy as np

class Eyes:
    ''' Класс "глазок", т.е. работа с информацией на карте. Сбор, преобразование и т.д.
        * Матрицы: 1 - что-то есть, 0 - ничего нет'''
    map_size: tuple[int, int] = (48, 48)
    data: dict[str, np.ndarray] = None

    def __init__(self, map_size:int|list[int]|tuple[int,int]=None) -> None:
        if map_size is None:
            self.map_size = (48,48)
        elif type(map_size) is int:
            self.map_size = (map_size, map_size)
        elif type(map_size) is tuple or type(map_size) is list:
            self.map_size = (map_size[0], map_size[1])
        self.data = {}
    
    def update(self, name:str, index:list[int], value:int=1, *, check_keys:bool=True):
        if name not in self.data.keys(): 
            if check_keys: raise Exception(f'Field {name} not found!')
            self.clear(name)
        if index[0] < self.data[name].shape[0] and index[1] < self.data[name].shape[1]:
            self.data[name][index[0], index[1]] = value

    def clear(self, name:str|dict[str, int]|list[str|dict[str, int]], *, value:int=0): # ['fields', 'fields'] or [{'fields': 1, 'fields': 0}]
        if type(name) is str:
            self.data[name] = np.ones(self.map_size, dtype=int) * value
        elif type(name) is list:
            for key in name:
                if type(key) is str:
                    self.data[key] = np.ones(self.map_size, dtype=int) * value
                elif type(key) is dict and len(key) > 0:
                    for key, value in key.items():
                        self.data[key] = np.ones(self.map_size, dtype=int) * value
        elif type(name) is dict:
            for key, value in name.items():
                self.data[key] = np.ones(self.map_size, dtype=int) * value
        return self

    def sum(self, names:list[str|np.ndarray]) -> np.ndarray: # ['fields', 'fields', np.ndarray[48, 48]]
        result = np.zeros(self.map_size, dtype=int)
        for name in names:
            if type(name) is str:
                if name in self.data.keys():
                    result = result + self.data.get(name)
            elif type(name) is np.ndarray:
                result = result + name
        return result
    
    def diff(self, names:list[str|np.ndarray]) -> np.ndarray: # ['fields', 'fields', np.ndarray[48, 48]]
        result = None
        for name in names:
            if type(name) is str:
                if name in self.data.keys():
                    result = result - self.data.get(name) if result is not None else self.data.get(name)
            elif type(name) is np.ndarray:
                result = result - name
        return result

    def getValue(self, matrix:np.ndarray, how:str, default:int=1, condition=lambda x: x is not None) -> int:
        result = None
        if how == 'max':
            result = np.max(matrix)
        elif how == 'min':
            result = np.min(matrix)
        if condition is not None:
            if not condition(result):
                return default
        return result

    def norm(self, name:str|np.ndarray, *, value:int=None, how:str='max') -> np.ndarray:
        result = None
        if type(name) is str:
            if name in self.data.keys():
                result = self.data[name] / (value if value is not None else self.getValue(self.data[name], how, 1, lambda x: x != 0))
        elif type(name) is np.ndarray:
            result = name / (value if value is not None else self.getValue(name, how, 1, lambda x: x != 0))
        return result

    def neg(self, name: str|np.ndarray, *, cond=lambda x: 1 if x == 0 else 0, find:int=None, to:int=None) -> np.ndarray:
        result = None
        if type(name) is str:
            if name in self.data.keys():
                result = self.data.get(name).copy()
        elif type(name) is np.ndarray:
            result = name.copy()
        for i in range(result.shape[0]):
            for j in range(result.shape[1]):
                if find is not None and to is not None:
                    if result[i, j] == find: result[i, j] = to
                    elif result[i, j] == to: result[i, j] = find
                else:
                    result[i, j] = cond(result[i, j])
        return result

    def get(self, name:str) -> np.ndarray:
        return self.data.get(name)

    def getLocketField(self, names:list[str]=None) -> np.ndarray:
        ''' Получить матрицу запрещённых ходов
            0 - блокирован проход, 1 - проход возможен '''
        locked_field = np.zeros(self.map_size, dtype=int)
        energy = self.data['e_energy'] - self.data['u_energy'] # < 0 - у нас больше, > 0 - у противника больше
        energy = np.where(energy > 0, energy, 0)
        if np.max(energy) > 0: energy = energy / np.max(energy)
        locked_field = np.where(self.data['factory'] + self.data['robots'] + energy > 0, locked_field, 1)
        return self.neg(locked_field)
    
    def getLockedFieldMax(self) -> np.ndarray:
        locked_field = np.zeros(self.map_size, dtype=int)
        locked_field = np.where(self.sum(['factory', 'robots', self.norm(self.diff(['e_energy', 'u_energy']))]) > 0, locked_field, 1)
        return locked_field

def getRect(X:int, Y:int, rad:int=1, borders:bool=True) -> tuple[list, list]:
    ''' Получить квадрат координат вокруг точки '''
    x, y = [], []
    for r in range(-rad, rad + 1):
        for k in range(-rad, rad + 1):
            ny, nx = X-k, Y-r
            if not borders or nx > -1 and ny > -1:
                x.append(X-k)
                y.append(Y-r)
    return x, y

def getRange(pos=[], size=10):
    res = [0 for i in range(size)]
    if len(pos) > 0:
        for i in pos: res[i] = 1
    return res

size=10
ev = Eyes(size).clear('new1')
fabric = []
for i in [  [               ],
            [               ],
            [ 1,2,3         ],
            [ 1,2,3,  6,7,8 ],
            [ 1,2,3,  6,7,8 ],
            [         6,7,8 ],
            [               ],
            [               ],
            [               ],
            [               ]
        ]:
    fabric.append(getRange(i, size))
fabric = np.array(fabric)
print('-'*50)
robots = []
for i in [  [           7   ],
            [               ],
            [               ],
            [          6    ],
            [   2           ],
            [               ],
            [               ],
            [            8  ],
            [               ],
            [1              ]
        ]:
    robots.append(getRange(i, size))
robots = np.array(robots)
print('-'*50)
enemies = []
for i in [  [        4      ],
            [               ],
            [               ],
            [        4      ],
            [               ],
            [               ],
            [   2           ],
            [               ],
            [               ],
            [    3          ]
        ]:
    enemies.append(getRange(i, size))
enemies = np.array(enemies)

ev.clear(['factory', 'robots', 'enemy', 'u_energy', 'e_energy'])


for i in range(fabric.shape[0]):
    for j in range(fabric.shape[1]):
        if fabric[i, j] == 1:
            ev.update('factory', [i, j])

for i in range(robots.shape[0]):
    for j in range(robots.shape[1]):
        if robots[i, j] == 1:
            ev.update('robots', [i, j])
            x, y = getRect(i, j)
            en = np.random.random_integers(15, 125)
            for x, y in zip(x, y):
                ev.update('u_energy', [x, y], en)

for i in range(enemies.shape[0]):
    for j in range(enemies.shape[1]):
        if enemies[i, j] == 1:
            ev.update('enemy', [i, j])
            x, y = getRect(i, j)
            en = np.random.random_integers(35, 150)
            for x, y in zip(x, y):
                ev.update('e_energy', [x, y], en)


for name in ['factory', 'robots', 'enemy', 'u_energy', 'e_energy']:
    print('--', name,'-'*(46-len(name)),'\n', ev.get(name))

print('--', 'locked Field','-'*(46-len('locked Field')),'\n', ev.getLockedFieldMax())

#print('--', 'negate','-'*(46-len('negate')),'\n', ev.neg('u_energy'))
