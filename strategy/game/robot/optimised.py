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
# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
# ----- Номера ресурсов для удобства (в Lux не указаны)
# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
class ActionsFabric:
    ''' Фабрика действий '''
    game_state: GameState = None
    unit: RobotData = None
    max_actions = 20
    free_len = 0
    energy_cost = 0
    last_energy_cost = 0
    resource_gain =  {'full': 0, 'last': 0}
    rubble_gain = {'full': 0, 'last': 0}
    action_cost = 1
    eyes: Eyes

    def __init__(self, game_state:GameState, unit:RobotData, eyes:Eyes, max_actions:int=20) -> None:
        self.action_cost = unit.robot.action_queue_cost(game_state)
        self.last_energy_cost = 0
        self.max_actions = max_actions
        self.free_len = max_actions
        self.game_state = game_state
        self.resource_gain = {'full': 0, 'last': 0}
        self.rubble_gain = {'full': 0, 'last': 0}
        self.energy_cost = self.action_cost
        self.actions = []
        self.unit = unit
        self.eyes = eyes

    def check(self):
        if self.unit.robot.power > self.action_cost \
            or len(self.actions) < self.max_actions: return True
        return False

    def buildResourceUnload(self) -> bool:
        if not self.check(): return False
        for res, count in zip(*self.unit.getResource()):
            self.actions.append(self.unit.robot.transfer(0, res, count))
        self.actions = self.actions[:self.max_actions]
        return True

    def buildTakeEnergy(self, count:int) -> bool:
        if not self.check(): return False
        if count > self.action_cost:
            self.actions.append(self.unit.robot.pickup(RES.energy, count))
            self.energy_cost -= count
            return True
        return False

    def buildMove(self, to:np.ndarray, lock_map:np.ndarray, trim_border:int=20, trim:bool=False, *, dec:np.ndarray = None) -> bool:
        if not self.check(): return False
        m_actions, move_cost = findPathActions(self.unit.robot, self.game_state, to=to, steps=self.max_actions+5,
                                               dec=self.unit.robot.pos if dec is None else dec, lock_map=Observer.getLockMap())
        if len(m_actions) > 0 and (trim or len(m_actions) < trim_border):
            self.actions.extend(m_actions[:self.max_actions-len(self.actions)])
            self.energy_cost += sum(move_cost[:self.max_actions-len(self.actions)])
            Observer.lock_map[self.unit.robot.pos[0], self.unit.robot.pos[1]] = 0
            Observer.lock_map[self.unit.robot.pos[0], self.unit.robot.pos[1]] = 0
            self.eyes.update('units', self.unit.robot.pos, 0)
            self.eyes.update('units', m_actions[0], 1)
            self.last_energy_cost = sum(move_cost[:self.max_actions-len(self.actions)])
            return True
        return False

    def buildDigResource(self, count:int=1000, reserve:int=0) -> bool:
        if not self.check(): return False
        dig_count, dig_cost, dig_gain = calcDigCount(self.unit.robot, count=count, reserve_energy=self.energy_cost+reserve, 
                                                     dig_type=DIG_TYPES.RESOURCE)
        if dig_count > 0:
            self.actions.append(self.unit.robot.dig(n=dig_count))
            self.resource_gain['full'] += dig_gain
            self.resource_gain['last'] = dig_gain
            self.energy_cost += dig_cost
            self.last_energy_cost = dig_cost
            return True
        return False
    
    def checkDigRubble(self, count:int=100, reserve:int=0) -> bool:
        dig_count, __, __ = calcDigCount(self.unit.robot, count=count, reserve_energy=self.energy_cost+reserve,
                                                      dig_type=DIG_TYPES.RUBBLE)
        return dig_count > 0

    def buildDigRubble(self, count:int=100, reserve:int=0) -> bool:
        if not self.check(): return False
        dig_count, dig_cost, dig_gain = calcDigCount(self.unit.robot, count=count, reserve_energy=self.energy_cost+reserve,
                                                      dig_type=DIG_TYPES.RUBBLE)
        if dig_count > 0:
            self.actions.append(self.unit.robot.dig(n=dig_count))
            self.rubble_gain['full'] += dig_gain
            self.rubble_gain['last'] = dig_gain
            self.energy_cost += dig_cost
            self.last_energy_cost = dig_cost
            return True
        return False
    
    def extend(self, actions:list, energy_cost:int=0) -> bool:
        if not self.check(): return False
        if type(energy_cost) is int: self.energy_cost += energy_cost
        elif type(energy_cost) is list: self.energy_cost += sum(energy_cost[:self.max_actions-len(self.actions)])
        self.actions.extend(actions[:self.max_actions-len(self.actions)])
        return True

    def buildTransferResource(self, res_id:int, to:np.ndarray, count_min:int=-1, count_max:int=10000) -> bool:
        if not self.check(): return False
        count, count_min = 0, max(count_min, self.unit.robot.unit_cfg.DIG_RESOURCE_GAIN)
        if res_id == RES.ice:
            count = min(self.unit.robot.cargo.ice, count_max)
        elif res_id == RES.ore:
            count = min(self.unit.robot.cargo.ore, count_max)
        elif res_id == RES.water:
            count = min(self.unit.robot.cargo.water, count_max)
        elif res_id == RES.metal:
            count = min(self.unit.robot.cargo.metal, count_max)
        elif res_id == RES.energy:
            count = min(self.unit.robot.power, count_max)
        if count < count_min: return False
        self.actions.append(self.unit.robot.transfer(direction_to(self.unit.robot.pos, to), res_id, count))
        self.actions = self.actions[:self.max_actions]
        return True


    def getActions(self) -> list:
        return self.actions

    def isFull(self) -> bool:
        return len(self.actions) >= self.max_actions

    def isFree(self) -> bool:
        return len(self.actions) * self.unit.robot.power == 0

# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
# ----- Номера ресурсов для удобства (в Lux не указаны)
# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
class Observer:
    ''' Класс-обозреватель состояния игры '''
    return_robots = []
    lock_map = np.ones((48, 48), dtype=int)

    def calcLockMap(eyes:Eyes):
        Observer.lock_map = eyes.neg(eyes.sum(['factories', 'units']))

    def look(data:DataController, step:int, game_state:GameState, eyes:Eyes) -> list:
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
    
    def getLockMap() -> np.ndarray:
        ''' lock_map: 0 - lock, 1 - alloy '''
        return Observer.lock_map
    
    def addReturn(unit_id:str) -> bool:
        Observer.return_robots.append(unit_id)
        return True

    def removeReturn(unit_id:str) -> bool:
        if unit_id in Observer.return_robots:
            Observer.return_robots.remove(unit_id)
        return True
# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
# ----- Номера ресурсов для удобства (в Lux не указаны)
# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
class RobotStrategy:
    ''' Стратегия с наблюдателем '''  
    def getLockMap(self, unit:Unit, eyes:Eyes) -> np.ndarray:
        eyes.clear(['u_move', 'u_energy'])
        eyes.update('u_move', unit.pos-1, getRad(unit.pos, as_matrix=True)*RobotData.TYPE.getType(unit.unit_type))
        eyes.update('u_energy', unit.pos-1, getRad(unit.pos, as_matrix=True)*unit.power)
        move_map = eyes.diff(['e_move', 'u_move'])
        energy_map = eyes.diff(['e_energy', 'u_energy'])
        move_map = np.where(move_map == 0, energy_map, move_map)
        move_map = np.where(move_map > 0, 1, 0)
        # --- выясняем куда мы можем шагнуть ---
        locked_field = np.where(eyes.sum(['factories', 'units', move_map]) > 0, 0, 1)
        return locked_field
      
    #@time_wrapper('getRobotActions')
    def getActions(self, step:int, env_cfg:EnvConfig, game_state:GameState, data:DataController, **kwargs)->dict:
        ''' Получить список действий для роботов '''
        eyes:Eyes = kwargs.get('eyes')
        if eyes is None: raise Exception('eyes not found in args')
        result, ice_map, ore_map, rubble_map = {}, game_state.board.ice, game_state.board.ore, game_state.board.rubble
        for robot, task in zip(*Observer.look(data, step, game_state, eyes)):
            robot: RobotData
            unit, item = robot.robot, robot.factory
            actions = ActionsFabric(game_state, robot, eyes)
           
            # --- если робот находится на своей фабрике ---
            if robot.on_position(item.factory.pos, size=3):
                # --- если робот вернулся от куда-то, то удаляем его из массива ---
                Observer.removeReturn(unit.unit_id)
                task = robot.robot_task
                # --- добавляем действия по выгрузке и взятии энергии ---
                take_energy = min(unit.unit_cfg.BATTERY_CAPACITY - unit.power, item.factory.power)
                actions.buildResourceUnload()
                actions.buildTakeEnergy(take_energy)
            
            # --- если робот идёт на базу ---
            if task == ROBOT_TASK.RETURN:
                actions.buildMove(item.getNeareastPoint(unit.pos), Observer.getLockMap(), trim=True)
                Observer.addReturn(unit.unit_id)

            # --- если робот не на фабрике и он - копатель ---
            elif task == ROBOT_TASK.MINER:
                # --- если робот на блоке с ресурсом ---
                if robot.onResourcePoint(ice_map):
                    # --- строим маршрут к фабрике ---
                    m_actions, move_cost = findPathActions(unit, game_state, to=item.getNeareastPoint(unit.pos), lock_map=Observer.getLockMap())
                    # --- если не можем ничего выкопать - идём на фабрику ---
                    # --- или у фабрики закончится скоро вода - идём на фабрику ---
                    if not actions.buildDigResource(reserve=sum(move_cost)):
                        actions.extend(m_actions, move_cost)
                        Observer.addReturn(unit.unit_id)
                # --- если робот где-то гуляет ---
                else:
                    # --- находим ближайший ресурс ---
                    ct = findClosestTile(unit.pos, ice_map, lock_map=eyes.neg(eyes.sum([eyes.getFree(1) - ice_map, 'units'])))
                    if actions.buildMove(ct, Observer.getLockMap(), 20, False):
                        actions.buildDigResource(reserve=actions.last_energy_cost)
                    # --- иначе - идём на базу ---
                    else:
                        Observer.addReturn(unit.unit_id)
            # --- если робот не на фабрике и он - чистильщик ---
            elif task == ROBOT_TASK.CLEANER:
                # --- строим маршрут к фабрике ---
                m_actions, move_cost = findPathActions(unit, game_state, to=item.getNeareastPoint(unit.pos), lock_map=Observer.getLockMap())
                start_pos = unit.pos
                full_energy_cost = sum(move_cost)
                while not actions.isFull():
                    # --- находим ближайший щебень ---
                    ct = findClosestTile(start_pos, rubble_map, lock_map=eyes.update(eyes.neg('units'), unit.pos, 1)*rubble_map*eyes.neg(ore_map+ice_map))
                    # --- смотрим, можем ли мы копнуть хотябы пару раз ---
                    dig_count, __, __ = calcDigCount(unit, count=rubble_map[ct[0]][ct[1]], reserve_energy=actions.energy_cost+full_energy_cost,
                                                     dig_type=DIG_TYPES.RUBBLE)
                    if dig_count > 0:
                        # --- строим маршрут ---
                        if actions.buildMove(ct, Observer.getLockMap(), 20, False, dec=start_pos):
                            full_energy_cost += actions.last_energy_cost 
                        if actions.buildDigRubble(rubble_map[ct[0]][ct[1]], reserve=full_energy_cost):
                            rubble_map[ct[0]][ct[1]] -= min(actions.rubble_gain.get('last', 0), rubble_map[ct[0]][ct[1]])
                        else: break
                        start_pos = ct
                    # --- если не можем, то идём на базу ---
                    else:
                        actions.buildMove(item.getNeareastPoint(unit.pos), Observer.getLockMap(), trim=True)
                        Observer.addReturn(unit.unit_id)
                        break
            # --- если робот не на фабрике и он - курьер ---
            elif task == ROBOT_TASK.COURIER:
                # --- находим ближайшего робота на ресурсе ---
                ct = findClosestTile(unit.pos, eyes.get('units')*ice_map)
                ct_robot = data.getRobotOnPos(ct)
                if ct_robot is not None:
                    # --- если робот на блоке с ресурсом ---
                    if robot.onResourcePoint(ice_map):
                        # --- передаём соседу ресурсы ---
                        if actions.buildTransferResource(RES.ice, to=ct, count_max=ct_robot.getFree(RES.ice)):
                            # --- продолжаем делать, что делали ---
                            actions.extend(unit.action_queue)
                    else:
                        # --- строим маршрут к фабрике ---
                        m_actions, move_cost = findPathActions(unit, game_state, to=item.getNeareastPoint(unit.pos), lock_map=Observer.getLockMap())
                        # --- передаём копателю энергию и едем на базу ---
                        actions.buildTransferResource(RES.energy, to=ct, count_max=min(unit.power-sum(move_cost), ct_robot.getFree(RES.energy)))
                        actions.extend(m_actions, move_cost)
                        Observer.addReturn(unit.unit_id)
            # --- если робот не на фабрике и он - давитель ---
            elif task == ROBOT_TASK.WARRION:
                # --- выясняем куда мы можем шагнуть ---
                locked_field = self.getLockMap(unit, eyes)
                # --- ищем ближайшего врага ---
                next_pos = findClosestTile(unit.pos, eyes.get('e_move')*locked_field)
                # --- если можем шагнуть на врага - шагаем ---
                if locked_field[next_pos[0], next_pos[1]] == 1 and robot.getHasPerpecution():
                    m_actions, move_cost = findPathActions(unit, game_state, to=next_pos, lock_map=locked_field)
                    robot.persecution += 1
                # --- иначе - пытаемся убежать ---
                else:
                    # --- на врага не ходим ---
                    locked_field[next_pos[0], next_pos[1]] = 0
                    # --- строим маршрут побега ---
                    next_pos = findClosestTile(unit.pos, locked_field)
                    m_actions, move_cost = findPathActions(unit, game_state, to=next_pos, lock_map=locked_field)
                # --- делаем один шаг, если можем сделать шаг ---
                if len(m_actions) > 0:
                    actions.extend(m_actions, move_cost)
                    eyes.update('units', getNextMovePos(unit), 0)
                    eyes.update('units', next_pos, 1)
            # --- если робот не на фабрике и он - убегатель ---
            elif task == ROBOT_TASK.LEAVER:
                # --- выясняем куда мы можем шагнуть ---
                locked_field = self.getLockMap(unit, eyes)
                # --- ищем ближайшего врага ---
                next_pos = findClosestTile(unit.pos, eyes.get('e_move')*locked_field)
                # --- на врага не ходим ---
                locked_field[next_pos[0], next_pos[1]] = 0
                # --- строим маршрут побега ---
                next_pos = findClosestTile(unit.pos, locked_field)
                m_actions, move_cost = findPathActions(unit, game_state, to=next_pos, lock_map=locked_field)
                # --- делаем один шаг, если можем сделать шаг ---
                if len(m_actions) > 0:
                    actions.extend(m_actions, move_cost)
                    eyes.update('units', getNextMovePos(unit), 0)
                    eyes.update('units', next_pos, 1)
            # если действий для робота нет - действия не изменяем
            if not actions.isFree():
                result[unit.unit_id] = actions.getActions()
        return result