import numpy as np
from strategy.kits.robot_struct import ROBOT_TYPE


from strategy.kits.utils import *
from strategy.kits.decorators import time_wrapper

from strategy.kits.robot import RobotData

from lux.kit import GameState

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
    lichen_gain = {'full': 0, 'last': 0}
    action_cost = 1
    move_map = []
    steps = 0
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    def __init__(self, game_state:GameState, unit:RobotData, max_actions:int=20) -> None:
        self.action_cost = unit.robot.action_queue_cost(game_state)
        self.resource_gain = {'full': 0, 'last': 0}
        self.rubble_gain = {'full': 0, 'last': 0}
        self.lichen_gain = {'full': 0, 'last': 0}
        self.energy_cost = self.action_cost
        self.max_actions = max_actions
        self.game_state = game_state
        self.free_len = max_actions
        self.last_energy_cost = 0
        self.move_map = []
        self.actions = []
        self.unit = unit
        self.steps = 0
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
    #@time_wrapper('af_buildResourceUnload', 6)
    def buildResourceUnload(self, to:np.ndarray=None) -> bool:
        ''' Добавить действие выгрузки всех ресурсов '''
        if not self.check(): return False
        if to is None: to = self.unit.robot.pos
        for res, count in zip(*self.unit.getResource()):
            d = direction_to(self.unit.robot.pos, to)
            if d < 5 and d >= 0:
                self.actions.append(self.unit.robot.transfer(d, res, count))
                self.steps += 1
            else:
                return False
        return self.trimActions()
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    # ----- Добавить действие "взять энергию" -------------------------------------------------------------------
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    #@time_wrapper('af_buildTakeEnergy', 6)
    def buildTakeEnergy(self, count:int) -> bool:
        ''' Добавить действие "взять энергию" '''
        if not self.check(): return False
        if count > self.action_cost:
            self.actions.append(self.unit.robot.pickup(RES.energy, count))
            self.energy_cost -= count
            self.steps += 1
            return True
        return False
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    # ----- Добавить действие "копить энергию" ------------------------------------------------------------------
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    #@time_wrapper('af_buildReharge', 6)
    def buildReharge(self, count:int) -> bool:
        ''' Добавить действие "копить энергию" '''
        if not self.check(): return False
        if count > self.action_cost:
            self.actions.append(self.unit.robot.recharge(count))
            self.energy_cost -= count
            self.steps += count if self.unit.isType(ROBOT_TYPE.LIGHT) else ceil(count/10)
            return True
        return False
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    # ----- Добавить в действия маршрут -------------------------------------------------------------------------
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    #@time_wrapper('af_buildMove', 6)
    def buildMove(self, to:np.ndarray, trim:bool=False, border:int=20, lock_map:np.ndarray=None, *, dec:np.ndarray = None) -> bool:
        ''' Добавить в действия маршрут '''
        if not self.check(): return False
        dec = self.unit.robot.pos if dec is None else dec
        if getDistance(dec, to) > border and not trim: return False
        m_actions, move_cost, move_map = findPathActions(self.unit.robot, self.game_state, to=to, steps=self.max_actions-len(self.actions)+3,
                                               dec=dec, lock_map=lock_map, get_move_map=True)
        if len(m_actions) > 0:
            self.move_map.append(np.where(move_map > 0, move_map + self.steps, 0))
            self.actions.extend(m_actions[:min(border, self.max_actions-len(self.actions))])
            self.energy_cost += sum(move_cost[:min(border, self.max_actions-len(self.actions))])
            self.last_energy_cost = sum(move_cost[:min(border, self.max_actions-len(self.actions))])
            self.steps += np.max(move_map)
            return self.trimActions()
        return False
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    # ----- Добавить в действия маршрут с копанием щебня --------------------------------------------------------
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    #@time_wrapper('af_buildMove', 6)
    def buildCarrierMove(self, to:np.ndarray, rubble:np.ndarray, trim:bool=False, border:int=20, lock_map:np.ndarray=None, *, dec:np.ndarray = None) -> bool:
        ''' Добавить в действия маршрут '''
        if not self.check(): return False
        dec = self.unit.robot.pos if dec is None else dec
        if getDistance(dec, to) > border and not trim: return False
        m_actions, move_cost, move_map = findPathAndDigActions(self.unit.robot, self.game_state, rubble, to=to, steps=self.max_actions-len(self.actions)+3,
                                               dec=dec, lock_map=lock_map, get_move_map=True, reserve=self.energy_cost)
        if len(m_actions) > 0:
            self.move_map.append(np.where(move_map > 0, move_map + self.steps, 0))
            self.actions.extend(m_actions[:min(border, self.max_actions-len(self.actions))])
            self.energy_cost += sum(move_cost[:min(border, self.max_actions-len(self.actions))])
            self.last_energy_cost = sum(move_cost[:min(border, self.max_actions-len(self.actions))])
            self.steps += np.max(move_map)
            return self.trimActions()
        return False
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    # ----- Добавить действие "копать ресурс" -------------------------------------------------------------------
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    #@time_wrapper('af_buildDigResource', 6)
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
            self.steps += dig_count
            return True
        return False
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    # ----- Добавить действие "копать щебень" -------------------------------------------------------------------
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    #@time_wrapper('af_buildDigRubble', 6)
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
            self.steps += dig_count
            return True
        return False
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    # ----- Добавить действие "копать лишайник" -------------------------------------------------------------------
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    #@time_wrapper('af_buildDigRubble', 6)
    def buildDigLichen(self, count:int=100, reserve:int=0) -> bool:
        ''' Добавить действие "копать щебень" '''
        if not self.check(): return False
        dig_count, dig_cost, dig_gain = calcDigCount(self.unit.robot, count=count, reserve_energy=self.energy_cost+reserve,
                                                      dig_type=DIG_TYPES.LICHEN)
        if dig_count > 0:
            self.actions.append(self.unit.robot.dig(n=dig_count))
            self.lichen_gain['full'] += dig_gain
            self.lichen_gain['last'] = dig_gain
            self.energy_cost += dig_cost
            self.last_energy_cost = dig_cost
            self.steps += dig_count
            return True
        return False
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    # ----- Добавить действия из вне ----------------------------------------------------------------------------
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    #@time_wrapper('af_extend', 6)
    def extend(self, actions:list, energy_cost:int=0, move_map:np.ndarray=None) -> bool:
        ''' Добавить действия из вне '''
        if not self.check(): return False
        if type(energy_cost) is int: self.energy_cost += energy_cost
        elif type(energy_cost) is list: self.energy_cost += sum(energy_cost[:self.max_actions-len(self.actions)])
        self.actions.extend(actions[:self.max_actions-len(self.actions)])
        if move_map is not None:
            self.move_map.append(np.where(move_map > 0, move_map + self.steps, 0))
            self.steps += np.max(move_map)
        return self.trimActions()
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    # ----- Добавить действия "передать ресурсы" ----------------------------------------------------------------
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    #@time_wrapper('af_buildTransferResource', 6)
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
        self.steps += 1
        return self.trimActions()
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    # ----- Вернуть действия в виде списка ----------------------------------------------------------------------
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    def getActions(self) -> list:
        ''' Вернуть действия в виде списка '''
        return self.actions
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    # ----- Вернуть матрицу ходов -------------------------------------------------------------------------------
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    def getMoveMap(self) -> list:
        ''' Вернуть матрицу ходов '''
        return self.move_map
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