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
class Observer:
    ''' Класс-обозреватель состояния игры '''
    return_robots = []
    lock_map = np.ones((48, 48), dtype=int)
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    # ----- Рассчитать матрицу ходов ----------------------------------------------------------------------------
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    def calcLockMap(eyes:Eyes):
        Observer.lock_map = eyes.neg(eyes.sum(['factories', 'units']))
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    # ----- Проверить роботов и раздать задачи ------------------------------------------------------------------
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    def look(data:DataController, step:int, game_state:GameState, eyes:Eyes) -> list:
        ''' Проверить роботов и раздать задачи '''
        Observer.calcLockMap(eyes)
        robots, tasks, has_robots = [], [], []
        matrix, resource = eyes.getFree(), game_state.board.ice + game_state.board.ore
        # --- обрабатываем случаи наезда на противников ---
        for unit_id, robot in data.robots.items():
            if unit_id in has_robots: continue
            robot: RobotData
            unit = robot.robot
            item = robot.factory.factory
            # --- задавит ли нас противник ---
            pos = getNextMovePos(unit)
            e_move = eyes.get('e_move')
            # --- если может, то что-то делаем ---
            if e_move[pos[0], pos[1]] >= ROBOT_TYPE.getType(unit.unit_type):
                # --- если робот тяжелее нас или у нас нет шагов преследования - убегаем ---
                if e_move[unit.pos[0], unit.pos[1]] > ROBOT_TYPE.getType(unit.unit_type) \
                    or not robot.getHasPerpecution():
                    tasks.append(ROBOT_TASK.LEAVER)
                    has_robots.append(unit_id)
                    robot.persecution = 0
                    robots.append(robot)
                # --- если вес равный ---
                else:
                    tasks.append(ROBOT_TASK.WARRION)
                    has_robots.append(unit_id)
                    robot.persecution += 1
                    robots.append(robot)
            else:
                # --- проверяем задачу робота ---
                if robot.isTask(ROBOT_TASK.JOBLESS) or step > 50:
                    task_changed = False
                    if robot.isType(RobotData.TYPE.HEAVY):
                        task_changed = robot.setTask(ROBOT_TASK.MINER)
                    else:
                        task_changed = robot.setTask(ROBOT_TASK.MINER if step < 50 else ROBOT_TASK.CLEANER)
                    if task_changed:
                        tasks.append(ROBOT_TASK.RETURN)
                        has_robots.append(unit_id)
                        robots.append(robot)
                        continue
                robot_task = ROBOT_TASK.RETURN if unit_id in Observer.return_robots else robot.robot_task
                # --- считаем сколько шагов до связанной фабрики --- 
                moves = getDistance(unit.pos, robot.factory.factory.pos)
                # --- считаем через сколько фабрика уничтожится --- 
                steps = robot.factory.waterToSteps(game_state)
                # --- если у нас есть лёд и фабрика скоро уничтожится - везём домой лёд ---
                if unit.cargo.ice >= item.env_cfg.ICE_WATER_RATIO and steps <= moves+3 \
                    and robot_task != ROBOT_TASK.RETURN:
                    tasks.append(ROBOT_TASK.RETURN)
                    has_robots.append(unit_id)
                    robots.append(robot)
                # --- если с фабрикой всё ок ---
                else:
                    # --- выясняем, не шагаем ли мы на союзника ---
                    # --- если да, то пересчитываем маршрут ---
                    if matrix[pos[0], pos[1]] > 0:
                        has_robots.append(unit_id)
                        tasks.append(robot_task)
                        robots.append(robot)
                    else:
                        matrix[pos[0], pos[1]] = 1
                        # --- проверяем, есть ли действия у робота, если нет - задаём ---
                        if len(robot.robot.action_queue) == 0:
                            has_robots.append(unit_id)
                            tasks.append(robot_task)
                            robots.append(robot)
        return robots, tasks
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    # ----- Вернуть матрицу возможных ходов ---------------------------------------------------------------------
    # ------- lock_map: 0 - lock, 1 - alloy ---------------------------------------------------------------------
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    def getLockMap() -> np.ndarray:
        ''' Вернуть матрицу возможных ходов
            lock_map: 0 - lock, 1 - alloy '''
        return Observer.lock_map
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    # ----- Добавить робота в список возвращающихся роботов -----------------------------------------------------
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    def addReturn(unit_id:str) -> bool:
        ''' Добавить робота в список возвращающихся роботов '''
        Observer.return_robots.append(unit_id)
        return True
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    # ----- Удалить робота в список возвращающихся роботов ------------------------------------------------------
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    def removeReturn(unit_id:str) -> bool:
        ''' Удалить робота в список возвращающихся роботов '''
        if unit_id in Observer.return_robots:
            Observer.return_robots.remove(unit_id)
        return True
# ===============================================================================================================
# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
# ===============================================================================================================