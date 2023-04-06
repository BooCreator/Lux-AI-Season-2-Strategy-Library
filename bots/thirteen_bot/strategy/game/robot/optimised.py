import numpy as np
from lux.unit import Unit
from strategy.kits.action_fabric import ActionsFabric

from strategy.kits.data_controller import DataController
from strategy.kits.decorators import time_wrapper
from strategy.kits.observer import MAP_TYPE, Observer
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
class RobotStrategy:
    ''' Стратегия с наблюдателем '''

    #@time_wrapper('last_getRobotActions', 5)
    def getActions(self, step:int, env_cfg:EnvConfig, game_state:GameState, data:DataController, **kwargs)->dict:
        ''' Получить список действий для роботов '''
        eyes = data.eyes
        robot, task = Observer.look(data, step, game_state, eyes)
        return RobotStrategy.getRLActions(robot, task, env_cfg, game_state, eyes)
    
    #@time_wrapper('getRLActions', 5)
    def getRLActions(robots, tasks, env_cfg:EnvConfig, game_state:GameState, eyes:Eyes):
        Observer.eyes = eyes
        result, ice_map, ore_map, rubble_map = {}, game_state.board.ice, game_state.board.ore, game_state.board.rubble
        for robot, task in zip(robots, tasks):
            robot: RobotData
            unit, item = robot.robot, robot.factory
            actions = ActionsFabric(game_state, robot)
            lock_map = Observer.getLockMap(unit, task)

            if task == ROBOT_TASK.WALKER:
                task = robot.robot_task
            # --- если робот находится на своей фабрике ---
            elif robot.on_position(item.factory.pos, size=3):
                # --- если робот вернулся от куда-то, то удаляем его из массива ---
                Observer.removeReturn(unit.unit_id)
                # --- устанавливаем базовую задачу робота ---
                task = robot.robot_task if task == ROBOT_TASK.RETURN else task
                # --- добавляем действия по выгрузке и взятии энергии ---
                take_energy = min(unit.unit_cfg.BATTERY_CAPACITY - unit.power, item.factory.power)
                actions.buildResourceUnload()
                actions.buildTakeEnergy(take_energy)
            
            # --- если робот идёт на базу ---
            if task == ROBOT_TASK.RETURN:
                actions.buildMove(item.getNeareastPoint(unit.pos), True, lock_map=lock_map)
                Observer.addReturn(unit.unit_id)
            elif task == ROBOT_TASK.RECHARGE:
                actions.buildReharge(getNextMoveEnergyCost(game_state, unit))
            # --- если робот не на фабрике и он - копатель ---
            elif task == ROBOT_TASK.ICE_MINER or task == ROBOT_TASK.ORE_MINER:
                eyes.update('units', unit.pos, -1, collision=lambda a,b: a+b)
                resource = (ice_map if task == ROBOT_TASK.ICE_MINER else ore_map)*np.where(eyes.get('units') > 0, 0, 1)
                eyes.update('units', unit.pos, 1, collision=lambda a,b: a+b)
                # --- если робот на блоке с ресурсом ---
                if robot.onResourcePoint(resource):
                    # --- строим маршрут к фабрике ---
                    m_actions, move_cost, move_map = findPathActions(unit, game_state, to=item.getNeareastPoint(unit.pos), lock_map=lock_map, get_move_map=True)
                    # --- если не можем ничего выкопать - идём на фабрику ---
                    if not actions.buildDigResource(reserve=sum(move_cost)):
                        actions.extend(m_actions, move_cost, move_map=move_map)
                        Observer.addReturn(unit.unit_id)
                # --- если робот где-то гуляет ---
                else:
                    # --- находим ближайший ресурс ---
                    ct = findClosestTile(unit.pos, resource, lock_map=Observer.getLockMap(unit, task, map_type=MAP_TYPE.FIND))
                    if actions.buildMove(ct, border=20, lock_map=lock_map):
                        actions.buildDigResource(reserve=actions.last_energy_cost)
                    # --- иначе - идём на базу ---
                    else:
                        Observer.addReturn(unit.unit_id)
            # --- если робот не на фабрике и он - чистильщик ---
            elif task == ROBOT_TASK.CLEANER:
                # --- строим маршрут к фабрике ---
                m_actions, move_cost = findPathActions(unit, game_state, to=item.getNeareastPoint(unit.pos), lock_map=lock_map)
                start_pos = unit.pos
                lock_find_map = Observer.getLockMap(unit, task, MAP_TYPE.FIND)
                full_energy_cost = sum(move_cost)
                while not actions.isFull():
                    # --- находим ближайший щебень ---
                    ct = findClosestTile(start_pos, rubble_map, lock_map=lock_find_map)
                    # --- смотрим, можем ли мы копнуть хотябы пару раз ---
                    dig_count, __, __ = calcDigCount(unit, count=rubble_map[ct[0]][ct[1]], reserve_energy=actions.energy_cost+full_energy_cost,
                                                     dig_type=DIG_TYPES.RUBBLE)
                    if dig_count > 0:
                        # --- строим маршрут ---
                        if actions.buildMove(ct, border=20, dec=start_pos, lock_map=lock_map):
                            full_energy_cost += actions.last_energy_cost 
                        if actions.buildDigRubble(rubble_map[ct[0]][ct[1]], reserve=full_energy_cost):
                            rubble_map[ct[0]][ct[1]] -= min(actions.rubble_gain.get('last', 0), rubble_map[ct[0]][ct[1]])
                        else: break
                        start_pos = ct
                    # --- если не можем, то идём на базу ---
                    else:
                        actions.buildMove(item.getNeareastPoint(unit.pos), True, lock_map=lock_map)
                        break
            # --- если робот не на фабрике и он - давитель ---
            elif task == ROBOT_TASK.WARRION:
                # --- строим маршрут к фабрике ---
                m_actions, move_cost, move_map = findPathActions(unit, game_state, to=item.getNeareastPoint(unit.pos), lock_map=lock_map, get_move_map=True)
                # --- ищем ближайшего врага ---
                next_pos = findClosestTile(unit.pos, eyes.get('e_move')*lock_map, dec_is_none=False)
                if next_pos is None:
                    # --- если не нашли, то пытаемся пойти хоть куда-то ---
                    next_pos = findClosestTile(unit.pos, lock_map)
                    # --- если не можем походить никуда рядом, то идём на фабрику напролом ---
                    if getDistance(unit.pos, next_pos) > 1:
                        next_pos = item.getNeareastPoint(unit.pos)
                        lock_map = np.ones(lock_map.shape, dtype=int)
                # --- если можем шагнуть на врага - шагаем ---
                e_actions, e_move_cost, e_move_map = findPathActions(unit, game_state, to=next_pos, lock_map=lock_map, get_move_map=True)
                # --- если энергии хватит ещё и вернуться домой, то давим ---
                if unit.power - (sum(move_cost) + sum(e_move_cost)) > 1:
                    m_actions = e_actions
                    move_cost = e_move_cost
                    move_map  = e_move_map
                # --- делаем один шаг, если можем сделать шаг ---
                if len(m_actions) > 0:
                    actions.extend(m_actions, move_cost, move_map)
            # --- если робот не на фабрике и он - убегатель ---
            elif task == ROBOT_TASK.LEAVER:
                # --- строим маршрут побега в сторону базы ---
                m_actions, move_cost, move_map = findPathActions(unit, game_state, to=item.getNeareastPoint(unit.pos), lock_map=lock_map, get_move_map=True)
                # --- делаем один шаг, если можем сделать шаг ---
                if len(m_actions) > 0:
                    actions.extend(m_actions[:1], move_cost[:1], move_map=np.where(move_map==1, 1, 0))
            # если действий для робота нет - действия не изменяем
            if not actions.isFree() or len(unit.action_queue) > 0:
                result[unit.unit_id] = actions.getActions()
                Observer.addMovesMap(unit, actions.getMoveMap())
        return result