from collections import defaultdict
import numpy as np
from lux.unit import Unit

from strategy.kits.data_controller import DataController
from strategy.kits.decorators import time_wrapper
from strategy.kits.robot_struct import ROBOT_TASK, ROBOT_TYPE
from strategy.kits.utils import *

from strategy.kits.eyes import Eyes
from strategy.kits.robot import RobotData
from strategy.kits.factory import FactoryData

from lux.kit import GameState
from lux.kit import EnvConfig

# ===============================================================================================================
# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
# ===============================================================================================================
class TaskManager:
    '''  '''
    # --- до 20 хода все лёгкие роботы идут на руду, затем остаётся 1 ---
    # --- первый тяжёлый робот всегда добывает лёд ---
    # --- если тяжёлых роботов нет, то лёд добывает лёгкий робот ---
    # --- если робот уничтожителль, то задачу он не меняет ---
    # --- до 20 хода пе меняем задачи ---
    res_count = defaultdict(dict)
    i_n = 3
    o_n = 5
    r_n = 13
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    def __init__(self) -> None:
        self.res_count = defaultdict(dict)
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    # ----- Установить задачу роботу ----------------------------------------------------------------------------
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    def setRobotNewTask(self, gs:GameState, robot:RobotData, step:int, eyes:Eyes) -> list:
        ''' Установить задачу роботу '''
        unit = robot.robot
        item = robot.factory.factory
        if item.unit_id not in self.res_count.keys():
            # --- считаем количество ресурсов возле фабрики ---
            ice_matrix = getWindow([item.pos[0]-self.i_n, item.pos[1]-self.i_n], [item.pos[0]+self.i_n, item.pos[1]+self.i_n], gs.board.ice)
            ore_matrix = getWindow([item.pos[0]-self.o_n, item.pos[1]-self.o_n], [item.pos[0]+self.o_n, item.pos[1]+self.o_n], gs.board.ore)
            self.res_count[item.unit_id]['ice'] = np.sum(ice_matrix)
            self.res_count[item.unit_id]['ore'] = np.sum(ore_matrix)
        # --- на сколько хватит воды фабрике --- 
        steps = robot.factory.waterToSteps(gs)
        # --- считаем сколько шагов до связанной фабрики --- 
        moves = getDistance(unit.pos, robot.factory.factory.pos)
        # --- за сколько ходов переработается лёд, который у нас есть ---
        f_steps = ceil((unit.cargo.ice if unit.cargo.ice >= item.env_cfg.ICE_WATER_RATIO else 0)/item.env_cfg.FACTORY_PROCESSING_RATE_WATER)
        # --- если у нас есть лёд и фабрика скоро уничтожится - везём домой лёд ---
        if f_steps > 0 and (steps <= moves*2 or step >= 999-moves-f_steps) \
            and not robot.isTask(ROBOT_TASK.RETURN):
            return True, False
        # --- если с фабрикой всё ок ---
        need_return, task_changed = False, False
        if robot.isType(ROBOT_TYPE.HEAVY):
            need_return, task_changed = self.getTaskForHeavy(gs, robot, step, eyes)
        else:
            need_return, task_changed = self.getTaskForLight(gs, robot, step, eyes)    
        return need_return, task_changed
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    # ----- Установить задачу тяжёлому роботу -------------------------------------------------------------------
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    def getTaskForHeavy(self, gs:GameState, robot:RobotData, step:int, eyes:Eyes) -> list:
        ''' Установить задачу тяжёлому роботу '''
        unit = robot.robot
        item = robot.factory.factory
        l_max = self.res_count[item.unit_id]['ore']
        need_return, task_changed = False, False
        if step < 50 and getDistance(unit.pos, findClosestTile(item.pos, gs.board.ore)) < self.o_n*2:
            task_changed = robot.setTask(ROBOT_TASK.CARRIER)
        elif robot.factory.getCount(unit=robot, type_is=ROBOT_TYPE.HEAVY, task_is=ROBOT_TASK.ICE_MINER) < 1: #self.res_count[item.unit_id]['ice']:
            task_changed = robot.setTask(ROBOT_TASK.ICE_MINER)
        elif robot.factory.getCount(unit=robot, type_is=ROBOT_TYPE.HEAVY, task_is=ROBOT_TASK.ORE_MINER) < min(1, l_max): #max(min(round(280+700-step)/280*l_max, l_max), 1):
            task_changed = robot.setTask(ROBOT_TASK.ORE_MINER)
        elif getDistance(unit.pos, findClosestTile(item.pos, gs.board.rubble)) < self.r_n*2: #self.res_count['rubble'] > 0:
            task_changed = robot.setTask(ROBOT_TASK.CLEANER)
            need_return = task_changed
        else:
            task_changed = robot.setTask(ROBOT_TASK.DESTROYER)
        return need_return, task_changed
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    # ----- Установить задачу лёгкому роботу --------------------------------------------------------------------
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    def getTaskForLight(self, gs:GameState, robot:RobotData, step:int, eyes:Eyes) -> list:
        ''' Установить задачу лёгкому роботу '''
        unit = robot.robot
        item = robot.factory.factory
        l_max = self.res_count[item.unit_id]['ore']
        need_return, task_changed = False, False
        if robot.factory.getCount(unit=robot, task_is=ROBOT_TASK.ICE_MINER) < 1: #self.res_count[item.unit_id]['ice']:
            task_changed = robot.setTask(ROBOT_TASK.ICE_MINER)
        elif robot.factory.getCount(unit=robot, task_is=ROBOT_TASK.ORE_MINER) < min(1, l_max) : #max(min(round(280+700-step)/280*l_max, l_max), 1):
            task_changed = robot.setTask(ROBOT_TASK.ORE_MINER)
        elif getDistance(unit.pos, findClosestTile(item.pos, gs.board.rubble)) < self.r_n*2:
            task_changed = robot.setTask(ROBOT_TASK.CLEANER)
            need_return = task_changed
        else:
            task_changed = robot.setTask(ROBOT_TASK.DESTROYER)
        return need_return, task_changed
# ===============================================================================================================
# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
# ===============================================================================================================