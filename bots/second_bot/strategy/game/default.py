import numpy as np
from strategy.utils_func import *
from math import ceil, floor

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
    def update(self, name:str, index:list[int|list[int]]|np.ndarray, value:int|np.ndarray=1, *, check_keys:bool=True):
        ''' Установить значение {value} в таблице {name} в точках {index}'''
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
# ===============================================================================================================
# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
# ===============================================================================================================



class RobotData:
    ''' Класс данных робота '''

    class TYPE:
        ''' Тип робота LIGHT - 0, HEAVY - 1 '''
        LIGHT = 0
        HEAVY = 1

        def getType(type_name:str) -> int:
            return 0 if type_name == 'LIGHT' else 1

    class TASK:
        ''' Тип работы робота: MINER - 0, CLEANER - 1'''
        JOBLESS = -1
        MINER = 0
        CLEANER = 1
        # COURIER = 2
        # WARRION = 3

        def getTask(task_name:str) -> int:
            return 0 if task_name == 'MINER' else 1

    robot = None
    robot_type: TYPE = -1
    robot_task: TASK = -1
    min_task: int = 0 # сколько раз, минимально, нужно выполнить task
    
    def __init__(self, robot) -> None:
        self.robot = robot
        self.robot_type = RobotData.TYPE.getType(robot.unit_type)
        self.robot_task = RobotData.TASK.JOBLESS

    def on_position(self, pos:np.ndarray,*, size:int=1) -> bool:
        size = floor(size/2) + 1
        loc = self.robot.pos - pos
        return True if loc[0] > -size and loc[1] > -size and loc[0] < size and loc[1] < size else False

class FactoryData:
    ''' Класс данных фабрики '''
    factory = None
    robots: dict[str, RobotData] = []
    alive = False

    def __init__(self, factory) -> None:
        self.factory = factory
        self.robots = dict[str, RobotData]()
        self.alive = True

    def getRobotsOnType(self, robot_type: int = 0) -> int:
        result = []
        if type(robot_type) is str: robot_type = RobotData.TYPE.getType(robot_type)
        for unit in self.robots.values():
            if unit.robot_type == robot_type: result.append(unit)
        return result

    def getRobotstOnTask(self, robot_task: int = 0) -> int:
        result = []
        if type(robot_task) is str: robot_task = RobotData.TASK.getTask(robot_task)
        for unit in self.robots.values():
            if unit.robot_task == robot_task: result.append(unit)
        return result

    def getCountOnType(self, robot_type: int = 0) -> int:
        n = 0
        if type(robot_type) is str: robot_type = RobotData.TYPE.getType(robot_type)
        for unit in self.robots.values():
            if unit.robot_type == robot_type: n += 1
        return n

    def getCountOnTask(self, robot_task: int = 0) -> int:
        n = 0
        if type(robot_task) is str: robot_task = RobotData.TASK.getTask(robot_task)
        for unit in self.robots.values():
            if unit.robot_task == robot_task: n += 1
        return n

    def getFreeLocation(self):
        matrix = np.ones((3,3), dtype=int)
        for unit in self.robots.values():
            loc = unit.robot.pos - self.factory.pos
            if loc[0] > -2 and loc[1] > -2 and loc[0] < 2 and loc[1] < 2:
                matrix[loc[0]+1, loc[1]+1] = 0
        return matrix
    
    def getNeareastPoint(self, point: np.ndarray) -> np.ndarray:
        minX, minY = self.factory.pos[0], self.factory.pos[1]
        min = abs(point[0]-minX) + abs(point[1]-minY)
        x, y = getRect(minX, minY, 1)
        for x, y in zip(x, y):
            if abs(point[0]-x) + abs(point[1]-y) < min:
                minX, minY = x, y
        return np.array([minX, minY])

# ===============================================================================================================
# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
# ===============================================================================================================
class GameStrategy:
    ''' Класс стратегии игры '''
    f_data:dict[str,FactoryData] = {}
    free_robots: list[str] = []
    eyes: Eyes = None
    game_state = None
    player = None
    env = None
    step = 0
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    def __init__(self, env) -> None:
        self.f_data = dict[str,FactoryData]()
        self.free_robots = list[str]()
        self.eyes = Eyes(env.map_size)
        self.game_state = None
        self.env = env
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    # ----- Обновить состояние стратегии (фабрики, роботы) ------------------------------------------------------
    # ------- Инициализация происходит только при первом запуск -------------------------------------------------
    # ------- Сама функция вызывается на каждом ходу ------------------------------------------------------------
    # ------- В случае смены стратегии инициализация должна происходить -----------------------------------------
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    def update(self, game_state, player, step):
        ''' Обновить состояние стратегии (фабрики, роботы) '''
        self.checkFactories(game_state.factories[player])
        self.checkRobots(game_state.units[player])
        ft, fu = self.getFactoryInfo()
        for unit_id in self.free_robots:
            unit = game_state.units[player].get(unit_id)
            if unit is not None:
                cf, __ = findClosestFactory(unit.pos, factory_tiles=ft, factory_units=fu)
                self.f_data[cf.unit_id].robots[unit_id] = RobotData(unit)
        self.free_robots.clear()
        self.look(game_state, player)
        self.game_state = game_state
        self.player = player
        self.step = step
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    # ----- Проверить фабрики в данных стратегии ----------------------------------------------------------------
    # ------- Удаляем фабрики, если какая-то была уничтожена ----------------------------------------------------
    # ------- Если фабрик нет - заполняем массив ----------------------------------------------------------------
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    def checkFactories(self, factories):
        ''' Проверить фабрики в данных стратегии '''
        for unit_id, factory in factories.items():
            if unit_id in self.f_data.keys():
                self.f_data[unit_id].alive = True
                self.f_data[unit_id].factory = factory
            else:
                self.f_data[unit_id] = FactoryData(factory)
        to_remove = []
        for unit_id, item in self.f_data.items():
            if not item.alive: 
                for uid in item.robots.keys():
                    self.free_robots.append(uid)
                to_remove.append(unit_id)
            else:
                item.alive = False
        for unit_id in to_remove:
            del self.f_data[unit_id]
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    # ----- Проверить роботов в данных стратегии ----------------------------------------------------------------
    # ------- Удаляем робота, если он не существует -------------------------------------------------------------
    # ------- Если фабрик нет - заполняем массив ----------------------------------------------------------------
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    def checkRobots(self, robots:dict[str]):
        ''' Проверить роботов в данных стратегии '''

        # убираем удалённых роботов
        for item in self.f_data.values():
            has_robots = dict[str, RobotData]()
            for unit in robots.values():
                if unit.unit_id in item.robots.keys():
                    has_robots[unit.unit_id] = item.robots.get(unit.unit_id)
                    has_robots[unit.unit_id].robot = unit
            item.robots = has_robots
        
        # ищем свободных роботов
        for unit in robots.values():
            has_factory = False
            for item in self.f_data.values():
                if unit.unit_id in item.robots.keys():
                    has_factory = True
                    break
            if not has_factory and unit.unit_id not in self.free_robots:
                self.free_robots.append(unit.unit_id)
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    # ----- Получить информацию о фабриках (factory_tiles, factory_units) ---------------------------------------
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    def getFactoryInfo(self) -> tuple[list[list],list]:
        ''' Получить информацию о фабриках '''
        factory_tiles = []
        factory_units = []
        for item in self.f_data.values():
            factory_tiles.append(item.factory.pos)
            factory_units.append(item.factory)
        return factory_tiles, factory_units
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    # ----- Обновить карты фабрик, юнитов, лишайника TODO -------------------------------------------------------
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    def look(self, game_state, player: str):
        ''' Обновить карту юнитов '''
        self.eyes.clear(['factories', 'units', 'enemy', 'e_energy', 'u_energy', 'resources'])
        for pl in game_state.factories:
            if pl != player:
                for factory in game_state.factories.get(pl).values():
                    self.eyes.update('factories', factory.pos-1, np.ones((3,3), dtype=int))
        for pl in game_state.units:
            for unit in game_state.units.get(pl).values():
                x, y = getRad(unit.pos[0], unit.pos[1])
                for x, y in zip(x, y):
                    self.eyes.update('u_energy' if pl == player else 'e_energy', [x, y], unit.power)
                self.eyes.update('units' if pl == player else 'enemy', unit.pos, 1)
                self.eyes.update('resources', unit.pos, 1)
        
        # лишайник
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    # -----
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    def getFactoryActions(self, step:int) -> dict:
        actions = {}
        for unit_id, item in self.f_data.items():
            fact_free_loc = item.getFreeLocation()
            if step < 500 and fact_free_loc[1][1] == 1:
                if item.factory.power >= self.env.ROBOTS["LIGHT"].POWER_COST and \
                    item.factory.cargo.metal >= self.env.ROBOTS["LIGHT"].METAL_COST and item.getCountOnType('LIGHT') < 3:
                    actions[unit_id] = item.factory.build_light()
                if item.factory.power >= self.env.ROBOTS["HEAVY"].BATTERY_CAPACITY and \
                    item.factory.cargo.metal >= self.env.ROBOTS["HEAVY"].METAL_COST and item.getCountOnType('HEAVY') < 1:
                    actions[unit_id] = item.factory.build_heavy()
            elif step > 500 and fact_free_loc[1][1] == 1:
                if item.factory.power >= self.env.ROBOTS["HEAVY"].BATTERY_CAPACITY and \
                    item.factory.cargo.metal >= self.env.ROBOTS["HEAVY"].METAL_COST and item.getCountOnType('HEAVY') < 3:
                    actions[unit_id] = item.factory.build_heavy()
                if item.factory.power >= self.env.ROBOTS["LIGHT"].POWER_COST and \
                    item.factory.cargo.metal >= self.env.ROBOTS["LIGHT"].METAL_COST and item.getCountOnType('LIGHT') < 5:
                    actions[unit_id] = item.factory.build_light()
            elif item.factory.water_cost(self.game_state) <= item.factory.cargo.water / 5 - 200:
                actions[unit_id] = item.factory.water()
        return actions
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    # -----
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    return_robots = []
    clean_robots = []
    def getRobotActions(self, step:int) -> dict:
        actions = {}
        ice_map = self.game_state.board.ice
        rubble_map = self.game_state.board.rubble
        for __, item in self.f_data.items():
            for robot in item.robots.values():
                unit = robot.robot
                # если у робота пустая очередь
                if len(unit.action_queue) == 0:
                    actions[unit.unit_id] = []
                    # --- определяем цену одной смены задачи ---
                    action_cost = unit.action_queue_cost(self.game_state) 
                    # по умолчанию не берём энергии
                    take_energy = 0 # unit.unit_cfg.BATTERY_CAPACITY - unit.power
                    # --- если робот - копатель ---
                    if robot.robot_task == RobotData.TASK.MINER:
                        # --- находим ближайший ресурс ---
                        ct = findClosestTile(unit.pos, ice_map, free_resources=self.eyes.neg('resources')) 
                        # --- если робот находится на блоке с фабрикой ---
                        if robot.on_position(item.factory.pos, size=3):
                            # --- если есть ресурсы, то выгружаем ресурсы ---
                            if unit.cargo.ice > 0:
                                actions[unit.unit_id].append(unit.transfer(0, RES.ice, unit.cargo.ice))
                            if unit.cargo.ore > 0:
                                actions[unit.unit_id].append(unit.transfer(0, RES.ore, unit.cargo.ore))
                            if unit.cargo.metal > 0:
                                actions[unit.unit_id].append(unit.transfer(0, RES.metal, unit.cargo.metal))
                            if unit.cargo.water > 0:
                                actions[unit.unit_id].append(unit.transfer(0, RES.water, unit.cargo.water))
                            # --- строим маршрут к ресурсу ---
                            m_actions, move_cost = getMoveActions(self.game_state, unit, to=ct, steps=1000)
                            if len(m_actions) <= 20:
                                # --- определяем сколько будем копать ---
                                __, dig_cost, __ = calcDigCount(unit, reserve_energy=(move_cost + action_cost)*2)
                                # --- указываем сколько брать энергии ---
                                take_energy = min((move_cost + action_cost)*2 + dig_cost - unit.power, item.factory.power)
                                # --- добавляем действие "взять энергию" ---
                                if take_energy > action_cost:
                                    actions[unit.unit_id].append(unit.pickup(RES.energy, take_energy))
                                if unit.unit_id in self.return_robots: 
                                    self.return_robots.remove(unit.unit_id)
                                robot.min_task = 0
                            # --- Если ближайших ресурсов нет, то идём чистить ---
                            else:
                                robot.robot_task = RobotData.TASK.CLEANER
                        # --- если робот находится на блоке с ресурсом ---
                        if onResourcePoint(robot.robot.pos, ice_map) and unit.unit_id not in self.return_robots:
                            # --- строим маршрут к фабрике ---
                            m_actions, move_cost = getMoveActions(self.game_state, unit, to=item.factory.pos)
                            # --- определяем сколько будем копать ---
                            dig_count, __, __ = calcDigCount(unit, has_energy=unit.power, reserve_energy=move_cost+action_cost)
                            # --- если накопали сколько нужно или макс, то идём на базу ---
                            if unit.cargo.ice >= robot.min_task or unit.cargo.ice == unit.unit_cfg.CARGO_SPACE:
                                self.return_robots.append(unit.unit_id)
                            # --- если ещё не накопали, но можем капнуть больше чем 0 ---
                            elif dig_count > 0:
                                # --- добавляем действие "копать" ---
                                actions[unit.unit_id].append(unit.dig(n=dig_count))
                            else:
                                # --- иначе, копим энергию ---
                                how_energy = robot.min_task - unit.cargo.ice + action_cost
                                actions[unit.unit_id].append(unit.recharge(x=how_energy))
                        # --- если робот где-то гуляет ---
                        else:
                            # --- выясняем куда мы можем шагнуть ---
                            locked_field = np.zeros(self.eyes.map_size, dtype=int)
                            locked_field = np.where(self.eyes.sum(['factories', 'units', self.eyes.norm(self.eyes.diff(['e_energy', 'u_energy']))]) > 0, locked_field, 1)
                            #toImage(self.eyes.get('factories'), f'log/step/{self.player}_factories', render=True)
                            #toImage(self.eyes.get('units'), f'log/step/{self.player}_units', render=True)
                            #toImage(self.eyes.get('e_energy'), f'log/step/{self.player}_e_energy', render=True)
                            #toImage(self.eyes.get('u_energy'), f'log/step/{self.player}_u_energy', render=True)
                            #toImage(locked_field, f'log/step/{self.player}_locked_field', render=True)
                            points = []
                            # --- если робот - идёт на базу ---
                            if unit.unit_id in self.return_robots:
                                m_actions, move_cost, points = getMoveActions(self.game_state, unit, to=item.getNeareastPoint(unit.pos), locked_field=locked_field, has_points=True)
                            # --- иначе - идём к ресурсу ---
                            else:
                                m_actions, move_cost, points = getMoveActions(self.game_state, unit, to=ct, locked_field=locked_field, has_points=True)
                                if len(m_actions) >= 20:
                                    robot.robot_task = RobotData.TASK.CLEANER
                            # --- делаем один шаг, если можем сделать шаг ---
                            if len(points) > 0:
                                if unit.power > move_cost + action_cost:
                                    actions[unit.unit_id].extend(m_actions[:1])
                                    self.eyes.update('units', unit.pos, 0)
                                    self.eyes.update('units', points[0], 1)
                                    robot.min_task += 1
                                else:
                                    # --- иначе, копим энергию ---
                                    how_energy = move_cost + action_cost
                                    actions[unit.unit_id].append(unit.recharge(x=how_energy))
                    # --- если робот - чистильщик ---
                    elif robot.robot_task == RobotData.TASK.CLEANER:
                        # --- находим ближайший щебень ---
                        ct = findClosestTile(item.factory.pos, rubble_map, free_resources=rubble_map)
                        # --- если робот находится на блоке с фабрикой ---
                        if robot.on_position(item.factory.pos, size=3):
                            # --- строим маршрут к щебню ---
                            m_actions, move_cost = getMoveActions(self.game_state, unit, to=ct)
                            # --- определяем сколько будем копать ---
                            dig_count, dig_cost, __ = calcDigCount(unit, count=rubble_map[ct[0]][ct[1]], 
                                                                    reserve_energy=(move_cost*2)*action_cost, dig_type=DIG_TYPES.RUBBLE)
                            # --- указываем сколько брать энергии ---
                            take_energy = min((move_cost + action_cost)*2 + dig_cost - unit.power, item.factory.power)
                            # --- добавляем действие "взять энергию" ---
                            if take_energy > action_cost:
                                actions[unit.unit_id].append(unit.pickup(RES.energy, take_energy))
                            if unit.unit_id in self.return_robots: 
                                self.return_robots.remove(unit.unit_id)
                        # --- если робот находится на блоке с щебнем ---
                        if robot.on_position(ct, size=1) and unit.unit_id not in self.return_robots:
                            # --- определяем сколько энергии нужно для того, чтобы вернуться ---
                            __, move_cost = getMoveActions(self.game_state, unit, to=item.getNeareastPoint(unit.pos))
                            # --- определяем сколько будем копать ---
                            dig_count, dig_cost, gain = calcDigCount(unit, count=rubble_map[ct[0]][ct[1]], 
                                                                    has_energy=unit.power, reserve_energy=move_cost+action_cost, dig_type=DIG_TYPES.RUBBLE)
                            # --- если можем капнуть хотябы раз ---
                            if dig_count > 0:
                                # --- добавляем действие "копать" ---
                                actions[unit.unit_id].append(unit.dig(n=dig_count))
                                robot.min_task -= dig_count
                                rubble_map[ct[0]][ct[1]] = 0
                            # --- если нет, то идём на базу ---
                            else:
                                self.return_robots.append(unit.unit_id)
                        # --- если робот где-то гуляет ---
                        else:
                            # --- выясняем куда мы можем шагнуть ---
                            locked_field = np.zeros(self.eyes.map_size, dtype=int)
                            locked_field = np.where(self.eyes.sum(['factories', 'units', self.eyes.norm(self.eyes.diff(['e_energy', 'u_energy']))]) > 0, locked_field, 1)
                            points = []
                            # --- если робот - идёт на базу ---
                            if unit.unit_id in self.return_robots:
                                m_actions, move_cost, points = getMoveActions(self.game_state, unit, to=item.getNeareastPoint(unit.pos), locked_field=locked_field, has_points=True)
                            # --- иначе - идём к щебню ---
                            else:
                                m_actions, move_cost, points = getMoveActions(self.game_state, unit, to=ct, locked_field=locked_field, has_points=True)
                            # --- делаем один шаг, если можем сделать шаг ---
                            if len(points) > 0:
                                if unit.power >= move_cost + action_cost:
                                    actions[unit.unit_id].extend(m_actions[:1])
                                    self.eyes.update('units', unit.pos, 0)
                                    self.eyes.update('units', points[0], 1)
                                else:
                                    # --- иначе, копим энергию ---
                                    how_energy = move_cost + action_cost
                                    actions[unit.unit_id].append(unit.recharge(x=how_energy))
                        rubble_map[ct[0], ct[1]] = 0
                    # --- если у робота нет задачи, то назначаем её ---
                    else:
                        robot.robot_task = RobotData.TASK.MINER if step < 500 else RobotData.TASK.CLEANER
                # если действий для робота нет - удаляем массив действий, чтобы не тратить энергию
                if unit.unit_id in actions.keys() and len(actions[unit.unit_id]) == 0: 
                    del actions[unit.unit_id]
        return actions
# ===============================================================================================================
# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
# ===============================================================================================================
