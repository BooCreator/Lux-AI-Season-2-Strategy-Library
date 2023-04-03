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
    def getRobots(self, *, type_is:int=-1, task_is:int=-1, condition=lambda x: x == x):
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
            if condition(unit): result.append(unit)
        return result
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    # ----- Получить количество роботов по условию ---------------------------------------------------------------
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    def getCount(self,*, type_is:int=-1, task_is:int=-1, condition=lambda x: x == x) -> int:
        ''' Получить количество роботов по условию '''
        return len(self.getRobots(type_is=type_is, task_is=task_is, condition=condition))
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    # ----- Получить матрицу свободных ячеек на фабрике ---------------------------------------------------------
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    def getFreeLocation(self) -> np.ndarray:
        ''' Получить матрицу свободных ячеек на фабрике '''
        matrix = np.ones((3,3), dtype=int)
        for unit in self.robots.values():
            loc = unit.robot.pos - self.factory.pos
            if loc[0] > -2 and loc[1] > -2 and loc[0] < 2 and loc[1] < 2:
                matrix[loc[0]+1, loc[1]+1] = 0
        return matrix
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    # ----- Получить ближайшую ячейку фабрики -------------------------------------------------------------------
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    def getNeareastPoint(self, point:np.ndarray) -> np.ndarray:
        ''' Получить ближайшую ячейку фабрики '''
        pt = self.factory.pos
        mln = getDistance(point, pt)
        for f_points in getRect(self.factory.pos, 1):
            min = getDistance(point, f_points)
            if min < mln:
                mln = min
                pt = f_points
        return pt
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    # ----- Получить ближайшую ячейку фабрики -------------------------------------------------------------------
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    def getMeanWaterOnStep(self) -> int:
        return floor(sum(self.water)/len(self.water))

    def waterToSteps(self, game_state:GameState) -> int:
        water_cost = self.factory.water_cost(game_state)+1
        return floor(self.factory.cargo.water/water_cost)
# ===============================================================================================================
# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
# ===============================================================================================================