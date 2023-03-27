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
    def getActions(self, step:int, env_cfg:EnvConfig, game_state:GameState, data:DataController, **kwargs)->dict:
        ''' Получить список действий для роботов '''
        eyes:Eyes = kwargs.get('eyes')
        if eyes is None: raise Exception('eyes not found in args')
        result, ice_map, ore_map, rubble_map = {}, game_state.board.ice, game_state.board.ore, game_state.board.rubble
        for robot, task in zip(*Observer.look(data, step, game_state, eyes)):
            robot: RobotData
            unit, item = robot.robot, robot.factory
            actions = ActionsFabric(game_state, robot)
           
            # --- если робот находится на своей фабрике ---
            if robot.on_position(item.factory.pos, size=3):
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
                actions.buildMove(item.getNeareastPoint(unit.pos), True, lock_map=Observer.getLockMap(unit, task))
                Observer.addReturn(unit.unit_id)

            # --- если робот не на фабрике и он - копатель ---
            elif task == ROBOT_TASK.ICE_MINER or task == ROBOT_TASK.ORE_MINER:
                resource = ice_map if task == ROBOT_TASK.ICE_MINER else ore_map
                # --- если робот на блоке с ресурсом ---
                if robot.onResourcePoint(resource):
                    # --- строим маршрут к фабрике ---
                    m_actions, move_cost, move_map = findPathActions(unit, game_state, to=item.getNeareastPoint(unit.pos), lock_map=Observer.getLockMap(unit, task), get_move_map=True)
                    # --- если не можем ничего выкопать - идём на фабрику ---
                    if not actions.buildDigResource(reserve=sum(move_cost)):
                        actions.extend(m_actions, move_cost, move_map=move_map)
                        Observer.addReturn(unit.unit_id)
                # --- если робот где-то гуляет ---
                else:
                    # --- находим ближайший ресурс ---
                    ct = findClosestTile(unit.pos, resource, lock_map=Observer.getLockMap(unit, task, map_type=MAP_TYPE.FIND))
                    if actions.buildMove(ct, border=20, lock_map=Observer.getLockMap(unit, task)):
                        actions.buildDigResource(reserve=actions.last_energy_cost)
                    # --- иначе - идём на базу ---
                    else:
                        Observer.addReturn(unit.unit_id)
            # --- если робот не на фабрике и он - чистильщик ---
            elif task == ROBOT_TASK.CLEANER:
                # --- строим маршрут к фабрике ---
                m_actions, move_cost = findPathActions(unit, game_state, to=item.getNeareastPoint(unit.pos), lock_map=Observer.getLockMap(unit, task))
                start_pos = unit.pos
                full_energy_cost = sum(move_cost)
                while not actions.isFull():
                    # --- находим ближайший щебень ---
                    ct = findClosestTile(start_pos, rubble_map, lock_map=Observer.getLockMap(unit, task, MAP_TYPE.FIND))
                    # --- смотрим, можем ли мы копнуть хотябы пару раз ---
                    dig_count, __, __ = calcDigCount(unit, count=rubble_map[ct[0]][ct[1]], reserve_energy=actions.energy_cost+full_energy_cost,
                                                     dig_type=DIG_TYPES.RUBBLE)
                    if dig_count > 0:
                        # --- строим маршрут ---
                        if actions.buildMove(ct, border=20, dec=start_pos, lock_map=Observer.getLockMap(unit, task)):
                            full_energy_cost += actions.last_energy_cost 
                        if actions.buildDigRubble(rubble_map[ct[0]][ct[1]], reserve=full_energy_cost):
                            rubble_map[ct[0]][ct[1]] -= min(actions.rubble_gain.get('last', 0), rubble_map[ct[0]][ct[1]])
                        else: break
                        start_pos = ct
                    # --- если не можем, то идём на базу ---
                    else:
                        actions.buildMove(item.getNeareastPoint(unit.pos), True, lock_map=Observer.getLockMap(unit, task))
                        Observer.addReturn(unit.unit_id)
                        break
            # --- если робот не на фабрике и он - курьер ---
            #elif task == ROBOT_TASK.COURIER:
            #    # --- находим ближайшего робота на ресурсе ---
            #    ct = findClosestTile(unit.pos, eyes.get('units')*ice_map)
            #    ct_robot = data.getRobotOnPos(ct)
            #    if ct_robot is not None:
            #        # --- если робот на блоке с ресурсом ---
            #        if robot.onResourcePoint(ice_map):
            #            # --- передаём соседу ресурсы ---
            #            if actions.buildTransferResource(RES.ice, to=ct, count_max=ct_robot.getFree(RES.ice)):
            #                # --- продолжаем делать, что делали ---
            #                actions.extend(unit.action_queue)
            #        else:
            #            # --- строим маршрут к фабрике ---
            #            m_actions, move_cost = findPathActions(unit, game_state, to=item.getNeareastPoint(unit.pos), lock_map=Observer.getLockMap(unit, task))
            #            # --- передаём копателю энергию и едем на базу ---
            #            actions.buildTransferResource(RES.energy, to=ct, count_max=min(unit.power-sum(move_cost), ct_robot.getFree(RES.energy)))
            #            actions.extend(m_actions, move_cost)
            #            Observer.addReturn(unit.unit_id)
            # --- если робот не на фабрике и он - давитель ---
            elif task == ROBOT_TASK.WARRION:
                # --- выясняем куда мы можем шагнуть ---
                locked_field = Observer.getLockMap(unit, task)
                # --- ищем ближайшего врага ---
                next_pos = findClosestTile(unit.pos, eyes.get('e_move')*locked_field, dec_is_none=False)
                if next_pos is None:
                    # --- если не нашли, то пытаемся пойти хоть куда-то ---
                    next_pos = findClosestTile(unit.pos, locked_field)
                # --- если можем шагнуть на врага - шагаем ---
                m_actions, move_cost, move_map = findPathActions(unit, game_state, to=next_pos, lock_map=locked_field, get_move_map=True)
                # --- делаем один шаг, если можем сделать шаг ---
                if len(m_actions) > 0:
                    actions.extend(m_actions, move_cost, move_map)
            # --- если робот не на фабрике и он - убегатель ---
            elif task == ROBOT_TASK.LEAVER:
                # --- выясняем куда мы можем шагнуть ---
                locked_field = Observer.getLockMap(unit, task)
                # --- смотрим куда можем пойти ---
                next_pos = findClosestTile(unit.pos, locked_field)
                # --- строим маршрут побега в сторону базы ---
                m_actions, move_cost, move_map = findPathActions(unit, game_state, to=item.getNeareastPoint(unit.pos), lock_map=locked_field, get_move_map=True)
                # --- делаем один шаг, если можем сделать шаг ---
                if len(m_actions) > 0:
                    actions.extend(m_actions[:1], move_cost[:1], move_map=np.where(move_map==1, 1, 0))
            # если действий для робота нет - действия не изменяем
            if not actions.isFree():
                result[unit.unit_id] = actions.getActions()
                Observer.addMovesMap(unit, actions.getMoveMap())
        return result