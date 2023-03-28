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

class MAP_TYPE:
    MOVE = 0
    FIND = 1

# ===============================================================================================================
# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
# ===============================================================================================================
class Observer:
    ''' Класс-обозреватель состояния игры '''
    return_robots = []
    moves_map = defaultdict(list)
    lock_map = np.ones((48, 48), dtype=int)
    eyes:Eyes = None
    game_state:GameState = None
    step:int = 0
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    # ----- Правим матрицу ходов для каждого шага ---------------------------------------------------------------
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    def next_step(step:int):
        r = step - Observer.step
        remove = []
        for key, maps in Observer.moves_map.items():
            for i, map in enumerate(maps):
                map = np.where((map-r) < 0, 0, map)
                if np.max(map) <= 0:
                    remove.append((key, i))
        for (key, i) in remove:
            del Observer.moves_map[key][i]
            if len(Observer.moves_map[key]) == 0:
                del Observer.moves_map[key]
        Observer.step = step
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    # ----- Получить общую матрицу ходов роботов ----------------------------------------------------------------
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    def getMovesMatrix():
        result = np.ones(Observer.game_state.board.ice.shape, dtype=int)
        for maps in Observer.moves_map.values():
            for map in maps:
                result = np.where(map > 0, 0, result)
        return result
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    # ----- Проверить роботов и раздать задачи ------------------------------------------------------------------
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    def look(data:DataController, step:int, game_state:GameState, eyes:Eyes) -> list:
        ''' Проверить роботов и раздать задачи '''
        Observer.next_step(step)
        Observer.eyes = eyes
        Observer.game_state = game_state
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
            # --- если можем, то что-то делаем ---
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
                        task_changed = robot.setTask(ROBOT_TASK.ICE_MINER)
                    else:
                        task_changed = robot.setTask(ROBOT_TASK.ICE_MINER if step < 50 else ROBOT_TASK.CLEANER)
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
    def getLockMap(unit:Unit, task:int, map_type:int=MAP_TYPE.MOVE) -> np.ndarray:
        ''' Вернуть матрицу возможных ходов
            lock_map: 0 - lock, 1 - alloy '''
        eyes = Observer.eyes
        if map_type == MAP_TYPE.MOVE:
            if task == ROBOT_TASK.WARRION or task == ROBOT_TASK.LEAVER:
                return Observer.getWarriorLockMap(unit)
            #elif task == ROBOT_TASK.CLEANER:
            else:
                eyes.clear('u_move')
                eyes.update('u_move', unit.pos-1, getRad(unit.pos, as_matrix=True))
                return eyes.neg(eyes.sum([eyes.mul(['units', 'u_move']), 'factories']))
                #return eyes.neg(eyes.sum(['factories', 'units']))
        elif task == ROBOT_TASK.ICE_MINER or task == ROBOT_TASK.ORE_MINER:
            return Observer.findResource(RES.ice if task == ROBOT_TASK.ICE_MINER else RES.ore)
        elif task == ROBOT_TASK.CLEANER:
            return Observer.findRubble(unit)
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    # ----- Расчёт матрицы поиска ближайшего ресурса ------------------------------------------------------------
    # ------- lock_map: 0 - lock, 1 - alloy ---------------------------------------------------------------------
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    def findResource(res_type:int):
        eyes = Observer.eyes
        resource = Observer.game_state.board.ice if res_type == RES.ice else Observer.game_state.board.ore
        return eyes.neg(eyes.sum([eyes.getFree(1) - resource, 'units']))
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    # ----- Расчёт матрицы поиска ближайшего щебня --------------------------------------------------------------
    # ------- lock_map: 0 - lock, 1 - alloy ---------------------------------------------------------------------
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    def findRubble(unit:Unit):
        rubble_map = Observer.game_state.board.rubble
        ice_map = Observer.game_state.board.ice
        ore_map = Observer.game_state.board.ore
        eyes = Observer.eyes
        return eyes.update(eyes.neg('units'), unit.pos, 1)*rubble_map*eyes.neg(ore_map+ice_map)#*eyes.neg(Observer.getMovesMatrix())
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    # ----- Расчёт матрицы возможных ходов для столкновения с противником -------------------------------------------------
    # ------- lock_map: 0 - lock, 1 - alloy ---------------------------------------------------------------------
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    def getWarriorLockMap(unit:Unit) -> np.ndarray:
        eyes = Observer.eyes
        eyes.update('units', getNextMovePos(unit), -1, collision=lambda a,b: a+b)
        eyes.update('units', unit.pos, 1, collision=lambda a,b: a+b)
        eyes.clear(['u_move', 'u_energy'])
        eyes.update('u_move', unit.pos-1, getRad(unit.pos, as_matrix=True)*ROBOT_TYPE.getType(unit.unit_type))
        eyes.update('u_energy', unit.pos-1, getRad(unit.pos, as_matrix=True)*unit.power)
        move_map = eyes.diff(['e_move', 'u_move'])
        energy_map = eyes.diff(['e_energy', 'u_energy']) # 
        move_map = np.where(move_map == 0, energy_map, move_map)
        move_map = np.where(move_map > 0, 1, 0)
        # --- выясняем куда мы можем шагнуть ---
        locked_field = np.where(eyes.sum(['factories', 'units', move_map]) > 0, 0, 1)
        return locked_field
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
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    # ----- Добавить матрицы ходов всех роботов -----------------------------------------------------------------
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    def addMovesMap(unit:Unit, move_map:list):
        Observer.moves_map[unit.unit_id] = move_map
        Observer.eyes.update('units', unit.pos, -1, collision=lambda a,b: a+b)
        for map in move_map:
            poses = np.argwhere(map == 1)
            if len(poses) > 0:
                Observer.eyes.update('units', poses[0], 1, collision=lambda a,b: a+b)
# ===============================================================================================================
# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
# ===============================================================================================================