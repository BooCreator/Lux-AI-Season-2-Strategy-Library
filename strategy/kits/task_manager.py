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

class TaskManager:

    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    # ----- Проверить и изменить задачу для роботов -------------------------------------------------------------
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    def setRobotNewTask(self, gs:GameState, robot:RobotData, step:int) -> list:
        # --- до 20 хода все лёгкие роботы идут на руду, затем остаётся 1 ---
        # --- первый тяжёлый робот всегда добывает лёд ---
        # --- если тяжёлых роботов нет, то лёд добывает лёгкий робот ---
        # --- если робот уничтожителль, то задачу он не меняет ---
        # --- до 20 хода пе меняем задачи ---
        unit = robot.robot
        item = robot.factory.factory
        # --- считаем сколько шагов до связанной фабрики --- 
        moves = getDistance(unit.pos, robot.factory.factory.pos)
        # --- считаем через сколько фабрика уничтожится --- 
        steps = robot.factory.waterToSteps(gs)
        # --- если у нас есть лёд и фабрика скоро уничтожится - везём домой лёд ---
        if unit.cargo.ice >= item.env_cfg.ICE_WATER_RATIO and (steps <= moves+3 or step >= 990 - moves) \
            and not robot.isTask(ROBOT_TASK.RETURN):
            return True, False
        need_return, task_changed = False, False
        if not robot.isTask(ROBOT_TASK.DESTROYER):
            if robot.isType(ROBOT_TYPE.HEAVY):
                if step < 50 and not robot.isTask(ROBOT_TASK.ICE_MINER):
                    task_changed = robot.setTask(ROBOT_TASK.CARRIER)
                elif robot.factory.getCount(unit=robot, type_is=ROBOT_TYPE.HEAVY, task_is=ROBOT_TASK.ICE_MINER) == 0:
                    task_changed = robot.setTask(ROBOT_TASK.ICE_MINER)
                elif robot.factory.getCount(unit=robot, type_is=ROBOT_TYPE.HEAVY, task_is=ROBOT_TASK.ORE_MINER) == 0:
                    task_changed = robot.setTask(ROBOT_TASK.ORE_MINER)
                else:
                    task_changed = robot.setTask(ROBOT_TASK.CLEANER)
                    need_return = task_changed
            else:
                if robot.factory.getCount(unit=robot, task_is=ROBOT_TASK.ICE_MINER) == 0:
                    task_changed = robot.setTask(ROBOT_TASK.ICE_MINER)
                elif robot.factory.getCount(unit=robot, task_is=ROBOT_TASK.ORE_MINER) == 0:
                    task_changed = robot.setTask(ROBOT_TASK.ORE_MINER)
                else:
                    task_changed = robot.setTask(ROBOT_TASK.CLEANER)
                    need_return = task_changed
        return need_return, task_changed