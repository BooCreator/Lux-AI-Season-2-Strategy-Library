import numpy as np
from lux.unit import Unit

from strategy.kits.data_controller import DataController
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
    energy_cost = 0
    resource_gain =  {'full': 0, 'last': 0}
    rubble_gain = {'full': 0, 'last': 0}
    action_cost = 1

    def __init__(self, game_state:GameState, unit:RobotData, max_actions:int=20) -> None:
        self.action_cost = unit.robot.action_queue_cost(game_state)
        self.max_actions = max_actions
        self.game_state = game_state
        self.resource_gain = {'full': 0, 'last': 0}
        self.rubble_gain = {'full': 0, 'last': 0}
        self.energy_cost = 0
        self.actions = []
        self.unit = unit

    def buildResourceUnload(self) -> bool:
        for res, count in zip(self.unit.getResource()):
            self.actions.append(self.unit.robot.transfer(0, res, count))
        self.actions = self.actions[:self.max_actions]
        return True

    def buildTakeEnergy(self, count:int) -> bool:
        if count > self.action_cost and len(self.actions) < self.max_actions:
            self.actions.append(self.unit.robot.pickup(RES.energy, count))
            return True
        return False

    def buildMove(self, to:np.ndarray, lock_map:np.ndarray, trim_border:int=20, trim:bool=False) -> bool:
        m_actions, move_cost = getMoveActions(self.game_state, self.unit.robot, to=to, steps=self.max_actions+5, locked_field=lock_map)
        if trim or len(m_actions) < trim_border:
            self.actions.extend(m_actions)
            self.actions = self.actions[:self.max_actions]
            self.energy_cost += move_cost
            return True
        return False

    def buildDigResource(self, count:int=1000, reserve:int=0) -> bool:
        dig_count, dig_cost, dig_gain = calcDigCount(self.unit.robot, count=count, reserve_energy=self.energy_cost+self.action_cost+reserve, 
                                                     dig_type=DIG_TYPES.RESOURCE)
        if dig_count > 0:
            self.actions.append(self.unit.robot.dig(n=dig_count-len(self.actions)))
            self.resource_gain['full'] += dig_gain
            self.resource_gain['last'] = dig_gain
            self.energy_cost += dig_cost
            return True
        return False
    
    def buildDigRubble(self, count:int=100, reserve:int=0) -> bool:
        dig_count, dig_cost, dig_gain = calcDigCount(self.unit.robot, count=count, reserve_energy=self.energy_cost+self.action_cost+reserve,
                                                      dig_type=DIG_TYPES.RUBBLE)
        if dig_count > 0:
            self.actions.append(self.unit.robot.dig(n=dig_count-len(self.actions)))
            self.rubble_gain['full'] += dig_gain
            self.rubble_gain['last'] = dig_gain
            self.energy_cost += dig_cost
            return True
        return False
    
    def extend(self, actions:list, energy_cost:int=0) -> bool:
        self.energy_cost += energy_cost
        self.actions.extend(actions)
        return True

    def getActions(self) -> list:
        return self.actions

    def isFull(self) -> bool:
        return len(self.actions) >= self.max_actions

    def isFree(self) -> bool:
        return len(self.actions) == 0 or self.unit.robot.power <= self.action_cost

# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
# ----- Номера ресурсов для удобства (в Lux не указаны)
# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
class Observer:
    ''' Класс-обозреватель состояния игры '''

    lock_map = np.ones((48, 48), dtype=int)

    def look(f_data:dict, game_state:GameState, eyes:Eyes) -> list:
        robots = []
        for __, item in f_data.items():
            item: FactoryData
            for robot in item.robots.values():
                robot: RobotData
                if len(robot.robot.action_queue) == 0:
                    robots.append(robot)
        return robots
    
    def getLockMap()-> np.ndarray:
        return Observer.lock_map
# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
# ----- Номера ресурсов для удобства (в Lux не указаны)
# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
class RobotStrategy:
    ''' Стратегия с наблюдателем '''
    return_robots = []
    def getActions(self, step:int, env_cfg:EnvConfig, game_state:GameState, data:DataController, **kwargs)->dict:
        ''' Получить список действий для роботов '''
        eyes:Eyes = kwargs.get('eyes')
        if eyes is None: raise Exception('eyes not found in args')
        f_data:dict = data.getFactoryData()
        result, ice_map, rubble_map = {}, game_state.board.ice, game_state.board.rubble
        for robot, task in zip(Observer.look(f_data, game_state, eyes)):
            robot: RobotData
            unit, item = robot.robot, robot.factory
            take_energy = min(unit.unit_cfg.BATTERY_CAPACITY - unit.power, item.factory.power)
            actions = ActionsFabric(game_state, robot)
            # --- если робот находится на своей фабрике ---
            if robot.on_position(item.factory.pos, size=3):
                # --- если робот вернулся от куда-то, то удаляем его из массива ---
                if unit.unit_id in self.return_robots: 
                    self.return_robots.remove(unit.unit_id)
                actions.buildResourceUnload()
                actions.buildTakeEnergy(take_energy)
                # --- определяем что будем делать ---
                if robot.isType(ROBOT_TASK.MINER):
                    # --- находим ближайший ресурс ---
                    ct = findClosestTile(unit.pos, ice_map, lock_map=eyes.neg(eyes.sum([eyes.getFree(1) - ice_map, 'units'])))
                    if actions.buildMove(ct, Observer.getLockMap(), 20, False):
                        actions.buildDigResource()
                    # --- Если ближайших ресурсов нет, то идём чистить ---
                    elif not robot.isType(ROBOT_TYPE.HEAVY):
                        robot.setTask(ROBOT_TASK.CLEANER)
                elif robot.isTask(ROBOT_TASK.CLEANER):
                    start_pos = item.factory.pos
                    while not actions.isFull():
                        # --- находим ближайший щебень ---
                        ct = findClosestTile(start_pos, rubble_map, lock_map=eyes.update(eyes.neg('units'), unit.pos, 1)*rubble_map)
                        # --- строим маршрут ---
                        if actions.buildMove(ct, Observer.getLockMap(), 20, False):
                            actions.buildDigRubble(rubble_map[ct[0]][ct[1]])
                            rubble_map[ct[0]][ct[1]] -= actions.rubble_gain.get('last', 0)
                        start_pos = ct
                elif robot.isTask(ROBOT_TASK.COURIER):
                    pass
            # --- если робот не на фабрике и он - копатель ---
            elif robot.isTask(RobotData.TASK.MINER):
                # --- если робот на блоке с ресурсом ---
                if robot.onResourcePoint(ice_map) and unit.unit_id not in self.return_robots:
                    # --- строим маршрут к фабрике ---
                    m_actions, move_cost = getMoveActions(game_state, unit, to=item.factory.pos)
                    # --- если не можем ничего выкопать - идём на фабрику ---
                    if not actions.buildDigResource(reserve=move_cost):
                        self.return_robots.append(unit.unit_id)
                        actions.extend(m_actions, move_cost)
                # --- если робот где-то гуляет ---
                else:
                    # --- если робот идёт к ресурсу ---
                    if unit.unit_id not in self.return_robots:
                        # --- находим ближайший ресурс ---
                        ct = findClosestTile(unit.pos, ice_map, lock_map=eyes.neg(eyes.sum([eyes.getFree(1) - ice_map, 'units'])))
                        if actions.buildMove(ct, Observer.getLockMap(), 20, False):
                            actions.buildDigResource()
                        # --- иначе - идём на базу ---
                        else:
                            self.return_robots.append(unit.unit_id)
                    # --- если робот - идёт на базу ---
                    if unit.unit_id in self.return_robots:
                        actions.buildMove(item.getNeareastPoint(unit.pos), Observer.getLockMap())
            # --- если робот не на фабрике и он - чистильщик ---
            elif robot.isTask(RobotData.TASK.CLEANER):
                # --- если робот находится на блоке с щебнем ---
                if robot.on_position(ct, size=1) and unit.unit_id not in self.return_robots:
                    # --- определяем сколько энергии нужно для того, чтобы вернуться ---
                    m_actions, move_cost = getMoveActions(game_state, unit, to=item.getNeareastPoint(unit.pos))
                    # --- если не можем ничего выкопать - идём на фабрику ---
                    if not actions.buildDigRubble(rubble_map[ct[0]][ct[1]], reserve=move_cost):
                        self.return_robots.append(unit.unit_id)
                        actions.extend(m_actions, move_cost)
                        rubble_map[ct[0]][ct[1]] -= actions.rubble_gain.get('last', 0)
                # --- если робот где-то гуляет ---
                else:
                    # --- если робот идёт к щебню ---
                    if unit.unit_id not in self.return_robots:
                        start_pos = item.factory.pos
                        while not actions.isFull():
                            # --- находим ближайший щебень ---
                            ct = findClosestTile(start_pos, rubble_map, lock_map=eyes.update(eyes.neg('units'), unit.pos, 1)*rubble_map)
                            # --- строим маршрут ---
                            if actions.buildMove(ct, Observer.getLockMap(), 20, False):
                                actions.buildDigRubble(rubble_map[ct[0]][ct[1]])
                                rubble_map[ct[0]][ct[1]] -= actions.rubble_gain.get('last', 0)
                            start_pos = ct
            # --- если робот не на фабрике и он - курьер ---
            elif robot.isTask(RobotData.TASK.COURIER):
                pass
            # --- если у робота нет задачи, то назначаем её ---
            else:
                if robot.isType(RobotData.TYPE.HEAVY):
                    robot.setTask(RobotData.TASK.MINER)
                else:
                    robot.setTask(RobotData.TASK.MINER if step < 500 else RobotData.TASK.CLEANER)
            # если действий для робота нет - действия не изменяем
            if not actions.isFree():
                result[unit.unit_id] = actions.getActions()
        return result