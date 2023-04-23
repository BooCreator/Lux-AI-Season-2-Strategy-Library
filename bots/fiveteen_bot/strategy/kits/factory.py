import numpy as np
from strategy.kits.eyes import Eyes
from strategy.kits.utils import *
from strategy.kits.robot_struct import ROBOT_TASK, ROBOT_TYPE

from lux.factory import Factory
# ===============================================================================================================
# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
# ===============================================================================================================
class FactoryData:
    ''' Класс данных фабрики '''
    factory:Factory = None
    robots:dict = {}
    alive:bool = False
    params:dict = {}
    water:list = []
    energy_cost:int = 0
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    # ----- Конструктор -----------------------------------------------------------------------------------------
    # -------- factory - экземпляр фабрики из Lux ---------------------------------------------------------------
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    def __init__(self, factory:Factory) -> None:
        self.factory = factory
        self.robots = {}
        self.alive = True
        self.params = {}
        self.water = []
        self.energy_cost = 0
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    # ----- Выбрать роботов фабрики по условию ------------------------------------------------------------------
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    def setParam(self, param:str, value):
        self.params[param] = value
    def getParam(self, param:str):
        return self.params.get(param)
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    # ----- Выбрать роботов фабрики по условию ------------------------------------------------------------------
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    def getRobots(self, *, ignore: list=None, type_is:int=-1, task_is:int=-1, condition=lambda x: x == x):
        ''' Выбрать роботов фабрики по условию '''
        result = []
        if type(type_is) is str: type_is = ROBOT_TYPE.getType(type_is)
        if type(task_is) is str: task_is = ROBOT_TASK.getTask(task_is)
        if type_is > -1 and task_is > -1:
            condition = lambda x: x.robot_type == type_is and x.robot_task == task_is
        elif type_is > -1:
            condition = lambda x: x.robot_type == type_is
        elif task_is > -1:
            condition = lambda x: x.robot_task == task_is
        for unit in self.robots.values():
            if ignore is None or unit.robot.unit_id not in ignore:
                if condition(unit): 
                    result.append(unit)
        return result
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    # ----- Получить количество роботов по условию ---------------------------------------------------------------
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    def getCount(self,*, unit=None, type_is:int=-1, task_is:int=-1, condition=lambda x: x == x) -> int:
        ''' Получить количество роботов по условию '''
        cond = 0
        if type(type_is) is str: type_is = ROBOT_TYPE.getType(type_is)
        if type(task_is) is str: task_is = ROBOT_TASK.getTask(task_is)
        if unit is not None:
            if type_is > -1 and task_is > -1:
                if unit.isType(type_is) and unit.isTask(task_is): cond = 1
            elif type_is > -1:
                if unit.isType(type_is): cond = 1
            elif task_is > -1:
                if unit.isTask(task_is): cond = 1
        return len(self.getRobots(type_is=type_is, task_is=task_is, condition=condition)) - cond
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    # ----- Получить матрицу свободных ячеек на фабрике ---------------------------------------------------------
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    def getFreeLocation(self, ignore:list=None) -> np.ndarray:
        ''' Получить матрицу свободных ячеек на фабрике '''
        matrix = np.ones((3,3), dtype=int)
        for unit in self.robots.values():
            if ignore is None or (unit.robot.pos[0] != ignore[0] or unit.robot.pos[1] != ignore[1]):
                loc = unit.robot.pos - self.factory.pos
                if loc[0] > -2 and loc[1] > -2 and loc[0] < 2 and loc[1] < 2:
                    matrix[loc[0]+1, loc[1]+1] = 0
        return matrix
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    # ----- Получить ближайшую ячейку фабрики -------------------------------------------------------------------
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    def getNeareastPoint(self, point:np.ndarray, ignore:bool=False) -> np.ndarray:
        ''' Получить ближайшую ячейку фабрики '''
        points = getRect(self.factory.pos, 1)
        lock_map = np.ones((3, 3), dtype=int) if ignore else self.getFreeLocation(point)
        distances = np.mean((points - point) ** 2, 1)
        for i, point in enumerate(points):
            f_pt = point - (self.factory.pos-1)
            if lock_map[f_pt[0], f_pt[1]] == 0:
                distances[i] += np.max(distances)
        pt = points[np.argmin(distances)]
        return pt
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    # ----- Получить ближайшую ячейку фабрики -------------------------------------------------------------------
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    def getMeanWaterOnStep(self, start:int=0) -> int:
        to = len(self.water[start:])
        to = 1 if to == 0 else to
        v = sum(self.water[start:])
        return v/to
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    # ----- На сколько ходов ещё хватит воды --------------------------------------------------------------------
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    def waterToSteps(self, game_state:GameState) -> float:
        water_cost = 1 + self.factory.water_cost(game_state)*1.5
        return self.factory.cargo.water/water_cost
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    # ----- Сколько собираемся потратить энергии на этом ходу ---------------------------------------------------
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    def getActionEnergyCost(self) -> int:
        return self.energy_cost
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    # ----- Ищем связанного робота по позиции -------------------------------------------------------------------
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    def findRobotOnPos(self, pos:np.ndarray) -> Unit:
        ''' Ищем связанного робота по позиции '''
        for unit in self.robots.values():
            if unit.robot.pos[0] == pos[0] and unit.robot.pos[1] == pos[1]:
                return unit
        return None
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    # ----- Ищем ближайшего робота без заряжателя ---------------------------------------------------------------
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    def findClosestRobot(self, pos:np.ndarray, task_is:ROBOT_TASK=-1, type_is:ROBOT_TYPE=-1):
        result = None
        for unit in self.robots.values():
            unit.robot.pos - pos
        return result
# ===============================================================================================================
# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
# ===============================================================================================================