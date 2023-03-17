import numpy as np
from math import floor

from lux.unit import Unit
from strategy.kits.factory import FactoryData

from strategy.kits.robot_struct import ROBOT_TASK, ROBOT_TYPE

from strategy.kits.utils import RES

# ===============================================================================================================
# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
# ===============================================================================================================
class RobotData:
    ''' Класс данных робота '''
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    TYPE = ROBOT_TYPE
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    TASK = ROBOT_TASK
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    robot: Unit = None
    robot_type: TYPE = -1
    robot_task: TASK = -1
    min_task: int = 0 # сколько раз, минимально, нужно выполнить task
    persecution: int = 0 # счётчик преследования
    max_persecution: int = 0 # максимальное количество шагов преследования
    factory: FactoryData = None # какой фабрике принадлежит
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    # ----- Конструктор -----------------------------------------------------------------------------------------
    # -------- factory - экземпляр робота из Lux ----------------------------------------------------------------
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    def __init__(self, robot, persecution:int=5) -> None:
        self.robot = robot
        self.robot_type = RobotData.TYPE.getType(robot.unit_type)
        self.robot_task = RobotData.TASK.JOBLESS
        self.persecution = 0
        self.max_persecution = persecution
        self.factory = None
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    # ----- Проверить, что робот находится на позиции -----------------------------------------------------------
    # -------- size - радиус области ----------------------------------------------------------------------------
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    def on_position(self, pos:np.ndarray, *, size:int=1) -> bool:
        ''' Проверить, что робот находится на позиции '''
        size = floor(size/2) + 1
        loc = self.robot.pos - pos
        return True if loc[0] > -size and loc[1] > -size and loc[0] < size and loc[1] < size else False
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    # ----- Проверить, что мы ещё можем преследовать противника -------------------------------------------------
    # -------- update - изменять ли значеие преследования ----------------------------------------------------------------------------
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    def getHasPerpecution(self, update:bool=False) -> bool:
        return self.persecution < self.max_persecution
    
    def getFactory(self)->FactoryData:
        return self.factory
    
    def getResource(self):
        res, count = [], []
        if self.robot.cargo.ice > 0:
            res.append(RES.ice)
            count.append(self.robot.cargo.ice)
        if self.robot.cargo.ore > 0:
            res.append(RES.ore)
            count.append(self.robot.cargo.ore)
        if self.robot.cargo.metal > 0:
            res.append(RES.metal)
            count.append(self.robot.cargo.metal)
        if self.robot.cargo.water > 0:
            res.append(RES.water)
            count.append(self.robot.cargo.water)
        return res, count
# ===============================================================================================================
# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
# ===============================================================================================================