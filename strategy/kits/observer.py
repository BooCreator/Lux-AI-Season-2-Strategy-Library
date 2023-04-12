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
    #@time_wrapper('obs_next_step', 6)
    def next_step(self, step:int):
        r = step - self.step
        remove = []
        for key, maps in self.moves_map.items():
            for i, map in enumerate(maps):
                map = np.where((map-r) < 0, 0, map)
                if np.max(map) <= 0:
                    remove.append((key, i))
        for (key, i) in remove:
            del self.moves_map[key][i]
            if len(self.moves_map[key]) == 0:
                del self.moves_map[key]
        self.step = step
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    # ----- Получить общую матрицу ходов роботов ----------------------------------------------------------------
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    #@time_wrapper('obs_getMovesMatrix', 6)
    def getMovesMatrix(self):
        result = np.ones(self.game_state.board.ice.shape, dtype=int)
        for maps in self.moves_map.values():
            for map in maps:
                result = np.where(map > 0, 0, result)
        return result
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    # ----- Проверить и изменить задачу для роботов -------------------------------------------------------------
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    def setRobotNewTask(self, robot:RobotData, step:int) -> list:
        task_changed = False
        if robot.isTask(ROBOT_TASK.JOBLESS) or step > 150:
            if not robot.isTask(ROBOT_TASK.DESTROYER):
                task_changed = False
                if robot.isType(ROBOT_TYPE.HEAVY):
                    if robot.factory.getCount(unit=robot, type_is=ROBOT_TYPE.HEAVY, task_is=ROBOT_TASK.ICE_MINER) == 0:
                        task_changed = robot.setTask(ROBOT_TASK.ICE_MINER)
                    elif robot.factory.getCount(unit=robot, type_is=ROBOT_TYPE.HEAVY, task_is=ROBOT_TASK.ORE_MINER) == 0:
                        task_changed = robot.setTask(ROBOT_TASK.ORE_MINER)
                    else:
                        task_changed = robot.setTask(ROBOT_TASK.CLEANER)
                else:
                    if robot.factory.getCount(unit=robot, task_is=ROBOT_TASK.ICE_MINER) == 0:
                        task_changed = robot.setTask(ROBOT_TASK.ICE_MINER)
                    elif robot.factory.getCount(unit=robot, task_is=ROBOT_TASK.ORE_MINER) == 0:
                        task_changed = robot.setTask(ROBOT_TASK.ORE_MINER)
                    else:
                        task_changed = robot.setTask(ROBOT_TASK.CLEANER)
                # --- если базовая задача была изменена - сначала возвращаемся на базу ---
                
        return task_changed
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    # ----- Проверить роботов и раздать задачи ------------------------------------------------------------------
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    #@time_wrapper('obs_look', 6)
    def look(self, data:DataController, step:int, game_state:GameState, eyes:Eyes) -> list:
        ''' Проверить роботов и раздать задачи '''
        self.next_step(step)
        self.eyes = eyes
        self.game_state = game_state
        robots, tasks, has_robots = [], [], []
        # --- проверяем действия роботов без энергии ---
        for unit_id, robot in data.robots.items():
            robot: RobotData
            unit = robot.robot
            # --- если у робота нет энергии чтобы сделать шаг - устанавливаем задачу - заряжатся ---
            if getNextMoveEnergyCost(game_state, unit) >= unit.power:
                eyes.update('units', getNextMovePos(unit), -1, collision=lambda a,b: a+b)
                eyes.update('units', unit.pos, 1, collision=lambda a,b: a+b)
                tasks.append(ROBOT_TASK.RECHARGE)
                has_robots.append(unit_id)
                robots.append(robot)

        # --- обрабатываем случаи наезда на противников ---
        for unit_id, robot in data.robots.items():
            if unit_id in has_robots: continue
            robot: RobotData
            unit = robot.robot
            item = robot.factory.factory
            # --- задавит ли нас противник ---
            pos = getNextMovePos(unit)
            e_move = eyes.get('e_move')
            # --- если робот может на нас наехать, то что-то делаем ---
            if e_move[pos[0], pos[1]] >= ROBOT_TYPE.getType(unit.unit_type):
                # --- если робот тяжелее нас или у нас нет шагов преследования - убегаем ---
                if e_move[unit.pos[0], unit.pos[1]] > ROBOT_TYPE.getType(unit.unit_type) \
                    or not robot.getHasPerpecution():
                    tasks.append(ROBOT_TASK.LEAVER)
                    has_robots.append(unit_id)
                    robot.persecution = 0
                    robots.append(robot)
                # --- если вес равный, то пытаемся задавить ---
                else:
                    tasks.append(ROBOT_TASK.WARRION)
                    has_robots.append(unit_id)
                    robot.persecution += 1
                    robots.append(robot)
            # --- если вражеский робот не может нас задавить ---
            else:
                # --- проверяем задачу робота ---
                if  self.setRobotNewTask(robot, step):
                    tasks.append(ROBOT_TASK.RETURN)
                    has_robots.append(unit_id)
                    robots.append(robot)
                    continue
                robot_task = ROBOT_TASK.RETURN if unit_id in self.return_robots else robot.robot_task
                # --- считаем сколько шагов до связанной фабрики --- 
                moves = getDistance(unit.pos, robot.factory.factory.pos)
                # --- считаем через сколько фабрика уничтожится --- 
                steps = robot.factory.waterToSteps(game_state)
                # --- если у нас есть лёд и фабрика скоро уничтожится - везём домой лёд ---
                if unit.cargo.ice >= item.env_cfg.ICE_WATER_RATIO and (steps <= moves+3 or step >= 990 - moves) \
                    and robot_task != ROBOT_TASK.RETURN:
                    tasks.append(ROBOT_TASK.RETURN)
                    has_robots.append(unit_id)
                    robots.append(robot)
                # --- если с фабрикой всё ок ---
                else:
                    # --- если робот стоит на месте ---
                    if unit.pos[0] == pos[0] and unit.pos[1] == pos[1]:
                        # --- проверяем, есть ли действия у робота, если нет - задаём ---
                        if len(robot.robot.action_queue) == 0:
                            has_robots.append(unit_id)
                            tasks.append(robot_task)
                            robots.append(robot)
                    else:
                        # --- выясняем, не шагаем ли мы на союзника ---
                        if eyes.get('units')[pos[0], pos[1]] -1 > 0:
                            # --- если да, то пересчитываем маршрут ---
                            tasks.append(ROBOT_TASK.WALKER)
                            has_robots.append(unit_id)
                            robots.append(robot)
            # --- если мы меняем робту задача, то пересчитываем ему units ---
            if unit_id in has_robots:
                eyes.update('units', pos, -1, collision=lambda a,b: a+b)
                eyes.update('units', unit.pos, 1, collision=lambda a,b: a+b)
        
        return robots, tasks
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    # ----- Вернуть матрицу возможных ходов ---------------------------------------------------------------------
    # ------- lock_map: 0 - lock, 1 - alloy ---------------------------------------------------------------------
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    #@time_wrapper('obs_getLockMap', 6)
    def getLockMap(self, unit:Unit, task:int, map_type:int=MAP_TYPE.MOVE) -> np.ndarray:
        ''' Вернуть матрицу возможных ходов
            lock_map: 0 - lock, 1 - alloy '''
        eyes = self.eyes
        if map_type == MAP_TYPE.MOVE:
            eyes.clear(['u_move', 'u_energy'])
            eyes.update('u_move', unit.pos-1, getRad(unit.pos, as_matrix=True)*ROBOT_TYPE.getType(unit.unit_type))
            eyes.update('u_energy', unit.pos-1, getRad(unit.pos, as_matrix=True)*unit.power)
            move_map = eyes.diff(['e_move', 'u_move'])
            energy_map = eyes.diff(['e_energy', 'u_energy']) # 
            move_map = np.where(move_map == 0, energy_map, move_map)
            move_map = np.where(move_map > 0, 1, 0)
            if task == ROBOT_TASK.WARRION or task == ROBOT_TASK.LEAVER:
                return self.getWarriorLockMap(unit, move_map)
            else:
                eyes.clear('u_move')
                eyes.update('u_move', unit.pos-1, getRad(unit.pos, as_matrix=True))
                return np.where(eyes.sum([eyes.mul(['units', 'u_move']), 'factories', move_map]) > 0, 0, 1)
        elif task == ROBOT_TASK.ICE_MINER or task == ROBOT_TASK.ORE_MINER:
            return self.findResource(RES.ice if task == ROBOT_TASK.ICE_MINER else RES.ore)
        elif task == ROBOT_TASK.CLEANER:
            return self.findRubble(unit)
        elif task == ROBOT_TASK.DESTROYER:
            return self.findLichen(unit)
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    # ----- Расчёт матрицы поиска ближайшего ресурса ------------------------------------------------------------
    # ------- lock_map: 0 - lock, 1 - alloy ---------------------------------------------------------------------
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    #@time_wrapper('obs_findResource', 7)
    def findResource(self, res_type:int):
        eyes = self.eyes
        resource = self.game_state.board.ice if res_type == RES.ice else self.game_state.board.ore
        return np.where(eyes.sum([eyes.getFree(1) - resource, 'units']) > 0, 0, 1)
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    # ----- Расчёт матрицы поиска ближайшего щебня --------------------------------------------------------------
    # ------- lock_map: 0 - lock, 1 - alloy ---------------------------------------------------------------------
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    #@time_wrapper('obs_findRubble', 7)
    def findRubble(self, unit:Unit):
        rubble_map = self.game_state.board.rubble
        ice_map = self.game_state.board.ice
        ore_map = self.game_state.board.ore
        eyes = self.eyes
        return rubble_map*np.where(eyes.sum(['units', ore_map, ice_map]) > 0, 0, 1)
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    # ----- Расчёт матрицы поиска ближайшего лишайника ----------------------------------------------------------
    # ------- lock_map: 0 - lock, 1 - alloy ---------------------------------------------------------------------
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    #@time_wrapper('obs_findLichen', 7)
    def findLichen(self, unit:Unit):
        eyes = self.eyes
        lichen = eyes.get('e_lichen').copy()
        if  ROBOT_TYPE.getType(unit.unit_type) == ROBOT_TYPE.LIGHT:
            return np.where(lichen < max(np.min(lichen) * 1.25, 5), 1, 0)
        else:
            return np.where(lichen > np.max(lichen) * 0.75, 1, 0)
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    # ----- Расчёт матрицы возможных ходов для столкновения с противником ---------------------------------------
    # ------- lock_map: 0 - lock, 1 - alloy ---------------------------------------------------------------------
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    #@time_wrapper('obs_getWarriorLockMap', 7)
    def getWarriorLockMap(self, unit:Unit, move_map:np.ndarray=None) -> np.ndarray:
        eyes = self.eyes
        return np.where(eyes.sum(['factories', 'units', move_map]) > 0, 0, 1)
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    # ----- Добавить робота в список возвращающихся роботов -----------------------------------------------------
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    def addReturn(self, unit_id:str) -> bool:
        ''' Добавить робота в список возвращающихся роботов '''
        if unit_id not in self.return_robots:
            self.return_robots.append(unit_id)
        return True
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    # ----- Удалить робота в список возвращающихся роботов ------------------------------------------------------
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    def removeReturn(self, unit_id:str) -> bool:
        ''' Удалить робота в список возвращающихся роботов '''
        if unit_id in self.return_robots:
            self.return_robots.remove(unit_id)
        return True
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    # ----- Добавить матрицы ходов всех роботов -----------------------------------------------------------------
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    #@time_wrapper('obs_addMovesMap', 6)
    def addMovesMap(self, unit:Unit, move_map:list):
        self.moves_map[unit.unit_id] = move_map
        self.eyes.update('units', unit.pos, -1, collision=lambda a,b: a+b)
        find = False
        for map in move_map:
            poses = np.argwhere(map == 1)
            if len(poses) > 0:
                self.eyes.update('units', poses[0], 1, collision=lambda a,b: a+b)
                find = True
        if not find:
            self.eyes.update('units', unit.pos, 1, collision=lambda a,b: a+b)
# ===============================================================================================================
# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
# ===============================================================================================================