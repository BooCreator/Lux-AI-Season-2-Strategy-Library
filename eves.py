import numpy as np

# ===============================================================================================================
# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
# ===============================================================================================================
class Eyes:
    ''' Класс "глазок", т.е. работа с информацией на карте. Сбор, преобразование и т.д.
        * Матрицы: 1 - что-то есть, 0 - ничего нет'''
    map_size: tuple[int, int] = (48, 48)
    data: dict[str, np.ndarray] = None
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    # ----- Конструктор -----------------------------------------------------------------------------------------
    # ------- Примеры: 48, [48, 48], (48,48), 48,48 -------------------------------------------------------------
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    def __init__(self, axis:int|list[int]|tuple[int,int]=None, axis2:int=None) -> None:
        ''' Примеры аргументов: 48; [ 48, 48 ]; ( 48,48 ); 48,48 '''
        if axis is None:
            self.map_size = (48,48)
        elif type(axis) is int:
            self.map_size = (axis, axis if axis2 is None else axis2)
        elif type(axis) is tuple or type(axis) is list:
            self.map_size = (axis[0], axis[1])
        self.data = {}
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    # ----- Очистить матрицу. Если не существует, то создать ----------------------------------------------------
    # ------- name - название матрицы ----------------------------------------------------------------------------
    # ------- Примеры аргументов: name='field', name=['field1', 'field2'], --------------------------------------
    # --------------------------- name={'field1': 1, 'field2': 0}, name=['field1', {'field2': 3}] ---------------
    # ------- value - значение, которым нужно заполнить матрицу -------------------------------------------------
    # ------- Если name задан как словарь, то value игнорируется ------------------------------------------------
    # ------- return -> self, чтобы можно было сразу создавать матрицы: Eves(10).clear(['field1', 'field2']) ----
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    def clear(self, name:str|dict[str, int]|list[str|dict[str, int]], value:int=0): # ['fields', 'fields'] or [{'fields': 1, 'fields': 0}]
        ''' Очистить матрицу. Если не существует, то создать '''
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
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    # ----- Обновить значения в матрице -------------------------------------------------------------------------
    # ------- name - название матрицы ---------------------------------------------------------------------------
    # ------- index - по каким координатам меняем ---------------------------------------------------------------
    # ------- Примеры аргументов: index=[0,0], index=[[0,1], [1,1]], index=np.array([0,1]) ----------------------
    # ------- value - значение для вставки, может быть матрицей -------------------------------------------------
    # ------- check_keys - проверка названий. Если пытаемся обьновить не существующую матрицу, то будет ошика ---
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    def update(self, name:str, index:list[int|list[int]]|np.ndarray, value:int|np.ndarray=1, *, check_keys:bool=True):
        ''' Установить значение {value} в таблице {name} в точках {index}'''
        if name not in self.data.keys(): 
            if check_keys: raise Exception(f'Field {name} not found!')
            self.clear(name)
        if type(index) is list and len(index) == 2 and type(index[0]) is int and type(index[1]) is int:
            if type(value) is int:
                if index[0] < self.data[name].shape[0] and index[1] < self.data[name].shape[1]:
                    self.data[name][index[0], index[1]] = value
            elif type(value) is np.ndarray:
                for i in range(value.shape[0]):
                    for j in range(value.shape[1]):
                        if index[0]+i < self.data[name].shape[0] and index[1]+j < self.data[name].shape[1]:
                            self.data[name][index[0]+i, index[1]+j] = value[i, j]
        elif type(index) is np.ndarray and len(index) == 2:
            if type(value) is int:
                if index[0] < self.data[name].shape[0] and index[1] < self.data[name].shape[1]:
                    self.data[name][index[0], index[1]] = value
            elif type(value) is np.ndarray:
                for i in range(value.shape[0]):
                    for j in range(value.shape[1]):
                        if index[0]+i < self.data[name].shape[0] and index[1]+j < self.data[name].shape[1]:
                            self.data[name][index[0]+i, index[1]+j] = value[i, j]
        elif type(index) is list:
            for ind in index:
                if type(ind) is list and len(ind) == 2 and type(ind[0]) is int and type(ind[1]) is int:
                    if type(value) is int:
                        if ind[0] < self.data[name].shape[0] and ind[1] < self.data[name].shape[1]:
                            self.data[name][ind[0], ind[1]] = value
                    elif type(value) is np.ndarray:
                        for i in range(value.shape[0]):
                            for j in range(value.shape[1]):
                                if ind[0]+i < self.data[name].shape[0] and ind[1]+j < self.data[name].shape[1]:
                                    self.data[name][ind[0]+i, ind[1]+j] = value[i, j]
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    # ----- Сумировать матрицы ----------------------------------------------------------------------------------
    # ------- names - массив матриц -----------------------------------------------------------------------------
    # ------- Примеры аргументов: names['field1', np.array([[0,1],[1,1]]), Eyes.norm('field2')] -----------------
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    def sum(self, names:list[str|np.ndarray]) -> np.ndarray:
        ''' Сумировать матрицы '''
        result = np.zeros(self.map_size, dtype=int)
        for name in names:
            if type(name) is str:
                if name in self.data.keys():
                    result = result + self.data.get(name)
            elif type(name) is np.ndarray:
                result = result + name
        return result
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    # ----- Разница матриц ----------------------------------------------------------------------------------
    # ------- names - массив матриц -----------------------------------------------------------------------------
    # ------- Примеры аргументов: names['field1', np.array([[0,1],[1,1]]), Eyes.norm('field2')] -----------------
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    def diff(self, names:list[str|np.ndarray]) -> np.ndarray:
        ''' Разница матриц '''
        result = None
        for name in names:
            if type(name) is str:
                if name in self.data.keys():
                    result = result - self.data.get(name) if result is not None else self.data.get(name)
            elif type(name) is np.ndarray:
                result = result - name
        return result
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    # ----- Получить вычисляемое значение матрицы (min, max) ----------------------------------------------------
    # ------- matrix - матрица ----------------------------------------------------------------------------------
    # ------- how - какой метод (min, max) ----------------------------------------------------------------------
    # ------- default - значение по умолчанию -------------------------------------------------------------------
    # ------- condition - функция проверки. Если ложно, то возвращаем default -----------------------------------
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    def getValue(self, matrix:str|np.ndarray, how:str, default:int=1, condition=lambda x: x is not None) -> int:
        ''' Получить вычисляемое значение матрицы (min, max) '''
        result = None
        if type(matrix) is str:
            if matrix not in self.data.keys():
                return default
            matrix = self.data[matrix]
        if how == 'max':
            result = np.max(matrix)
        elif how == 'min':
            result = np.min(matrix)
        if condition is not None:
            if not condition(result):
                return default
        return result if result is not None else default
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    # ----- Нормализация матрицы --------------------------------------------------------------------------------
    # ------- name - матрица ------------------------------------------------------------------------------------
    # ------- to - до какого значения ---------------------------------------------------------------------------
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    def norm(self, name:str|np.ndarray, *, to:int=None) -> np.ndarray:
        ''' Нормализация матрицы '''
        result = None
        if type(name) is str:
            if name in self.data.keys():
                result = self.data[name] / self.getValue(self.data[name], 'max', 1, lambda x: x != 0)
        elif type(name) is np.ndarray:
            result = name / self.getValue(name, 'max', 1, lambda x: x != 0)
        return result * to if to is not None else result
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    # ----- Обратить значения матрицы (0->1, 1->0) --------------------------------------------------------------
    # ------- name - матрица ------------------------------------------------------------------------------------
    # ------- func - функция обращения. По умолчанию обращает 0->1, x>0->0 --------------------------------------
    # ------- find - какое значение -----------------------------------------------------------------------------
    # ------- to - с каким --------------------------------------------------------------------------------------
    # --------- При указании find и to func игнорируется
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    def neg(self, name: str|np.ndarray, *, func=lambda x: 1 if x == 0 else 0, find:int=None, to:int=None) -> np.ndarray:
        ''' Обратить значения матрицы (0->1, 1->0) '''
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
                    result[i, j] = func(result[i, j])
        return result
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    # ----- Вернуть матрицу по названию -------------------------------------------------------------------------
    # ------- name - название матрицы ------------------------------------------------------------------------------------
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    def get(self, name:str) -> np.ndarray:
        return self.data.get(name)

    #def getLocketField(self, names:list[str]=None) -> np.ndarray:
    #    ''' Получить матрицу запрещённых ходов
    #        0 - блокирован проход, 1 - проход возможен '''
    #    locked_field = np.zeros(self.map_size, dtype=int)
    #    energy = self.data['e_energy'] - self.data['u_energy'] # < 0 - у нас больше, > 0 - у противника больше
    #    energy = np.where(energy > 0, energy, 0)
    #    if np.max(energy) > 0: energy = energy / np.max(energy)
    #    locked_field = np.where(self.data['factory'] + self.data['robots'] + energy > 0, locked_field, 1)
    #    return self.neg(locked_field)
    
    #def getLockedField(self, names:list[str]=None) -> np.ndarray:
    #    locked_field = np.zeros(self.map_size, dtype=int)
    #    locked_field = np.where(self.sum(['factory', 'robots', self.norm(self.diff(['e_energy', 'u_energy']))]) > 0, locked_field, 1)
    #    return locked_field
# ===============================================================================================================
# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
# ===============================================================================================================

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
ev = Eyes(10, 10).clear('new1')
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


#for name in ['factory', 'robots', 'enemy', 'u_energy', 'e_energy']:
#    print('--', name,'-'*(46-len(name)),'\n', ev.get(name))

#print('--', 'locked Field','-'*(46-len('locked Field')),'\n', ev.getLockedFieldMax() + ev.get('robots')*3 + ev.get('enemy')*4)

#print('--', 'negate','-'*(46-len('negate')),'\n', ev.neg('u_energy'))

ev.update('fact', [[1,1], [-4,-4]], value=np.ones((3,3),dtype=int), check_keys=False)
print('--', 'fact','-'*(46-len('fact')),'\n', ev.get('fact'))