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
    
    def onResourcePoint(self, tile_map:np.ndarray) -> bool:
        return tile_map[self.robot.pos[0], self.robot.pos[1]] == 1

    def isType(self, r_type:int)->bool:
        if type(r_type) is str: r_type = ROBOT_TYPE.getType(r_type)
        return self.robot_type == r_type

    def setType(self, new_type:int):
        if type(new_type) is str: new_type = ROBOT_TYPE.getType(new_type)
        self.robot_type = new_type

    def isTask(self, task:int)->bool:
        if type(task) is str: task = ROBOT_TASK.getTask(task)
        return self.robot_task == task

    def setTask(self, task:int):
        if type(task) is str: task = ROBOT_TASK.getTask(task)
        self.robot_task = task

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

    def getFree(self, res_id:int) -> int:
        if res_id == RES.ice or res_id == RES.ore or res_id == RES.water or res_id == RES.metal:
            return self.robot.unit_cfg.CARGO_SPACE - (self.robot.cargo.ice + self.robot.cargo.ore + self.robot.cargo.water + self.robot.cargo.metal)
        elif res_id == RES.energy:
            return self.robot.unit_cfg.BATTERY_CAPACITY - self.robot.power
        else: return 0
# ===============================================================================================================
# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
# ===============================================================================================================