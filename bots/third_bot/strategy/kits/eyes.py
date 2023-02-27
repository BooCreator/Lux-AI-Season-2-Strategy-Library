import numpy as np

try:
    from utils.tools import toImage
except: 
    def toImage(*args, **kwargs):
        pass

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
    def update(self, name:str|list[str]|np.ndarray, index:list[int|list[int]]|np.ndarray, value:int|np.ndarray=1, 
                *, check_keys:bool=True) -> np.ndarray|list[np.ndarray]:
        ''' Установить значение {value} в таблице {name} в точках {index}'''
        if type(name) is list:
            result = []
            for val in name:
                result.append(self.update(val, index, value, check_keys=check_keys))
                return result
        elif type(name) is np.ndarray:
            name[index[0], index[1]] = value
            return name
        elif type(name) is str:
            if name not in self.data.keys(): 
                if check_keys: raise Exception(f'Field {name} not found!')
                self.clear(name)
            if type(index) is list and len(index) == 2:
                if type(index[0]) is list:
                    for ind in index:
                        self.update(name, ind, value, check_keys=check_keys)
                else:
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
            return self.data[name]
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
                result = result - name if result is not None else name
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
    # ------- name - название матрицы ---------------------------------------------------------------------------
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    def get(self, name:str) -> np.ndarray:
        return self.data.get(name)
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    # ----- Вернуть матрицу значений ----------------------------------------------------------------------------
    # ------- value - значение для заполнения -------------------------------------------------------------------
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    def getFree(self, value:int=0) -> np.ndarray:
        return np.ones(self.map_size, dtype=int) * value
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    # ----- Сохранить матрицу как изображение -------------------------------------------------------------------
    # ------- value - значение для заполнения -------------------------------------------------------------------
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    def log(self, name: str|list[str]|np.ndarray, path:str=''):
        if type(name) is str:
            toImage(self.get(name), f'{path}_{name}', render=True)
        elif type(name) is np.ndarray:
            toImage(name, f'{path}_{name}', render=True)
        elif type(name) is list:
            for table in name:
                if type(table) is str:
                    toImage(self.get(table), f'{path}_{table}', render=True)
                elif type(table) is np.ndarray:
                    toImage(table, f'{path}_table', render=True)
# ===============================================================================================================
# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
# ===============================================================================================================