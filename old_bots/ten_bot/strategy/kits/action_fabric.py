import numpy as np
from lux.unit import Unit

from strategy.kits.data_controller import DataController
from strategy.kits.decorators import time_wrapper
from strategy.kits.observer import Observer
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
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
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
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    # ----- Проверить, можно ли добавить ещё ходов --------------------------------------------------------------
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    def check(self) -> bool:
        ''' Проверить, можно ли добавить ещё ходов '''
        return self.unit.robot.power > self.action_cost \
            and len(self.actions) < self.max_actions
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    # ----- Обрезать действия по максимуму ----------------------------------------------------------------------
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    def trimActions(self) -> bool:
        ''' Обрезать действия по максимуму '''
        self.actions = self.actions[:self.max_actions]
        return True
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    # ----- Добавить действие выгрузки всех ресурсов ------------------------------------------------------------
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    def buildResourceUnload(self) -> bool:
        ''' Добавить действие выгрузки всех ресурсов '''
        if not self.check(): return False
        for res, count in zip(*self.unit.getResource()):
            self.actions.append(self.unit.robot.transfer(0, res, count))
        return self.trimActions()
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    # ----- Добавить действие "взять энергию" ----------------------------------------------------------------------------
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    def buildTakeEnergy(self, count:int) -> bool:
        ''' Добавить действие "взять энергию" '''
        if not self.check(): return False
        if count > self.action_cost:
            self.actions.append(self.unit.robot.pickup(RES.energy, count))
            self.energy_cost -= count
            return True
        return False
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    # ----- Добавить в действия маршрут -------------------------------------------------------------------------
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    def buildMove(self, to:np.ndarray, trim:bool=False, border:int=20, lock_map:np.ndarray=None, *, dec:np.ndarray = None) -> bool:
        ''' Добавить в действия маршрут '''
        if not self.check(): return False
        dec = self.unit.robot.pos if dec is None else dec
        if getDistance(dec, to) > border and not trim: return False
        m_actions, move_cost = findPathActions(self.unit.robot, self.game_state, to=to, steps=self.max_actions-len(self.actions)+3,
                                               dec=dec, lock_map=lock_map or Observer.getLockMap())
        if len(m_actions) > 0:
            self.actions.extend(m_actions[:self.max_actions-len(self.actions)])
            self.energy_cost += sum(move_cost[:self.max_actions-len(self.actions)])
            self.last_energy_cost = sum(move_cost[:self.max_actions-len(self.actions)])
            Observer.lock_map[self.unit.robot.pos[0], self.unit.robot.pos[1]] = 0
            Observer.lock_map[m_actions[0][0], m_actions[0][1]] = 1
            self.eyes.update('units', self.unit.robot.pos, 0)
            self.eyes.update('units', m_actions[0], 1)
            return self.trimActions()
        return False
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    # ----- Добавить действие "копать ресурс" -------------------------------------------------------------------
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    def buildDigResource(self, count:int=1000, reserve:int=0) -> bool:
        ''' Добавить действие "копать ресурс" '''
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
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    # ----- Добавить действие "копать щебень" -------------------------------------------------------------------
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    def buildDigRubble(self, count:int=100, reserve:int=0) -> bool:
        ''' Добавить действие "копать щебень" '''
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
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    # ----- Добавить действия из вне ----------------------------------------------------------------------------
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    def extend(self, actions:list, energy_cost:int=0) -> bool:
        ''' Добавить действия из вне '''
        if not self.check(): return False
        if type(energy_cost) is int: self.energy_cost += energy_cost
        elif type(energy_cost) is list: self.energy_cost += sum(energy_cost[:self.max_actions-len(self.actions)])
        self.actions.extend(actions[:self.max_actions-len(self.actions)])
        return self.trimActions()
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    # ----- Добавить действия "передать ресурсы" ----------------------------------------------------------------
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    def buildTransferResource(self, res_id:int, to:np.ndarray, count_min:int=-1, count_max:int=10000) -> bool:
        ''' Добавить действия "передать ресурсы" '''
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
        if count < count_min: 
            return False
        self.actions.append(self.unit.robot.transfer(direction_to(self.unit.robot.pos, to), res_id, count))
        return self.trimActions()
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    # ----- Вернуть действия в виде списка ----------------------------------------------------------------------
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    def getActions(self) -> list:
        ''' Вернуть действия в виде списка '''
        return self.actions
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    # ----- Проверит не полная ли очередь ----------------------------------------------------------------------------
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    def isFull(self) -> bool:
        ''' Проверит не полная ли очередь '''
        return len(self.actions) >= self.max_actions
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    # ----- Проверить есть ли действия ----------------------------------------------------------------------------
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    def isFree(self) -> bool:
        ''' Проверить есть ли действия '''
        return len(self.actions) * self.unit.robot.power == 0
# ===============================================================================================================
# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
# ===============================================================================================================