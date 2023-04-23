from collections import defaultdict
import numpy as np
from lux.unit import Unit
from strategy.kits.action_fabric import ActionsFabric

from strategy.kits.data_controller import DataController
from strategy.kits.observer import MAP_TYPE, Observer
from strategy.kits.robot_struct import ROBOT_TASK, ROBOT_TYPE
from strategy.kits.task_manager import TaskManager
from strategy.kits.utils import *

from strategy.kits.eyes import Eyes
from strategy.kits.robot import RobotData
from strategy.kits.factory import FactoryData

from lux.kit import GameState
from lux.kit import EnvConfig

# ===============================================================================================================
# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
# ===============================================================================================================
class RobotStrategy:
    ''' Стратегия с наблюдателем '''
    obs: Observer = None
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    def __init__(self) -> None:
        self.obs = Observer()
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    # ----- Получить действия (для стратегий) -------------------------------------------------------------------
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    def getActions(self, step:int, env_cfg:EnvConfig, game_state:GameState, data:DataController, **kwargs)->dict:
        ''' Получить список действий для роботов '''
        eyes = data.eyes
        robot, task = self.obs.look(data, step, game_state, eyes)
        return RobotStrategy.getRLActions(robot, task, env_cfg, game_state, eyes, self.obs)
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    # ----- Получить действия (для RL) --------------------------------------------------------------------------
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    def getRLActions(robots, tasks, env_cfg:EnvConfig, game_state:GameState, eyes:Eyes, obs:Observer=None):
        if obs is None: obs = Observer()
        obs.game_state = game_state
        obs.eyes = eyes
        result = {}
        f_energy = {}
        # --- перебираем всех роботов и их задачи ---
        for robot, task in zip(robots, tasks):
            robot: RobotData
            unit, item = robot.robot, robot.factory
            actions = ActionsFabric(game_state, robot)
            if f_energy.get(item.factory.unit_id) is None:
                f_energy[item.factory.unit_id] = item.getActionEnergyCost()
            if task == ROBOT_TASK.WALKER:
                task = ROBOT_TASK.RETURN if unit.unit_id in obs.return_robots else robot.robot_task
            # --- если робот находится на своей фабрике ---
            elif robot.on_position(item.factory.pos, size=3):
                # --- добавляем действия взятия энергии ---
                max_on_task = 750 if robot.isType(ROBOT_TYPE.HEAVY) else 100
                if robot.isTask(ROBOT_TASK.ENERGIZER):
                    max_on_task = 100 if robot.isType(ROBOT_TYPE.HEAVY) else 100
                #elif robot.isTask(ROBOT_TASK.CARRIER):
                #    max_on_task = 250 if robot.isType(ROBOT_TYPE.HEAVY) else 150
                #elif robot.isTask(ROBOT_TASK.CLEANER):
                #    max_on_task = 500 if robot.isType(ROBOT_TYPE.HEAVY) else 150
                take_energy = min(unit.unit_cfg.BATTERY_CAPACITY-unit.power, 
                                  min(item.factory.power-f_energy.get(item.factory.unit_id, 0), max_on_task))
                # --- устанавливаем базовую задачу робота ---
                task = robot.robot_task if task == ROBOT_TASK.RETURN else task
                # --- если робот вернулся от куда-то, то удаляем его из массива ---
                actions.buildResourceUnload(item.getNeareastPoint(unit.pos))
                if actions.buildTakeEnergy(take_energy):
                    f_energy[item.factory.unit_id] += take_energy
                obs.removeReturn(unit.unit_id)
            elif robot.on_position(item.factory.pos, size=5) and (task != ROBOT_TASK.LEAVER and task != ROBOT_TASK.WARRION):
                # --- выгружаем ресурс, если выгрузили, то удаляем из возвращающихся ---
                if actions.buildResourceUnload(item.getNeareastPoint(unit.pos, ignore=True)):
                    obs.removeReturn(unit.unit_id)

            # --- формируем действия робота на основе задачи ---
            actions:ActionsFabric = RobotStrategy.getActionsOnTask(robot, task, game_state, obs, actions)
            
            # --- если действий для робота нет - действия не изменяем ---
            if not actions.isFree() or len(unit.action_queue) > 0:
                result[unit.unit_id] = actions.getActions()
                obs.addMovesMap(unit, actions.getMoveMap())
        return result
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    # ----- Получить действия по задаче -------------------------------------------------------------------------
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    def getActionsOnTask(robot:RobotData, task:int, game_state:GameState, obs:Observer, actions:ActionsFabric=None) -> ActionsFabric:
        robot: RobotData
        unit, item = robot.robot, robot.factory
        eyes = obs.eyes
        lichen = eyes.get('e_lichen').copy()
        lock_map = obs.getLockMap(unit, task)
        ice_map, ore_map, rubble_map = game_state.board.ice.copy(), game_state.board.ore.copy(), game_state.board.rubble.copy()
        actions = ActionsFabric(game_state, robot) if actions is None else actions
        
        # --- если робот идёт на базу ---
        if task == ROBOT_TASK.RETURN:
            # --- находим ближайшую точку базы к роботу ---
            ct = item.getNeareastPoint(unit.pos, ignore=True)
            # --- если до базы нужно идти ---
            if getDistance(unit.pos, ct) > 1:
                # --- строим маршрут ---
                m_actions, move_cost, move_map = findPathActions(unit, game_state, to=ct, lock_map=lock_map, get_move_map=True)
                # --- если у робота есть ресурс и мы не стоим возле базы, то идём до базы, а не на базу ---
                if robot.getResCount() > 0 and move_map[ct[0], ct[1]] > 0:
                    m_actions[-1][-1] -= 1
                    if m_actions[-1][-1] == 0:
                        del m_actions[-1]
                        del move_cost[-1]
                    move_map[ct[0], ct[1]] = 0
                # --- идём ---
                actions.extend(m_actions, move_cost, move_map)
                obs.addReturn(unit.unit_id)
             # --- если мы стоим в притык ---
            elif getDistance(unit.pos, ct) == 1:
                # --- если роботов никаких нет в позиции, куда идём, то идём ---
                if not actions.buildMove(ct, lock_map=lock_map):
                    if robot.isTask(ROBOT_TASK.ICE_MINER) or robot.isTask(ROBOT_TASK.ORE_MINER):
                        r: RobotData = item.findRobotOnPos(ct)
                        # --- если это заряжатель, то выходим после того, как он отдаст энергию ---
                        if (r is not None) and r.isTask(ROBOT_TASK.ENERGIZER) and (len(r.robot.action_queue) > 0) and r.robot.action_queue[0][0] != 1:
                            actions = RobotStrategy.getActionsOnTask(robot, robot.robot_task, game_state, obs, actions)
                            obs.removeReturn(unit.unit_id)
                    else:
                        actions.buildMove(item.getNeareastPoint(unit.pos), lock_map=lock_map)
        # --- если робот заряжается ---
        elif task == ROBOT_TASK.RECHARGE:
            # --- заряжаемся, чтобы можно было сделать следующий шаг ---
            actions.buildReharge(getNextMoveEnergyCost(game_state, unit))
            # --- идём на базу ---
            if robot.isTask(ROBOT_TASK.ICE_MINER) or robot.isTask(ROBOT_TASK.ORE_MINER) or robot.isTask(ROBOT_TASK.CLEANER):
                obs.addReturn(unit.unit_id)
        # --- если робот не на фабрике и он - копатель ---
        elif task == ROBOT_TASK.ICE_MINER or task == ROBOT_TASK.ORE_MINER:
            # --- находим ближайший не занятый ресурс ---
            units = eyes.get('units')
            units[unit.pos[0], unit.pos[1]] -= 1
            resource = (ice_map if task == ROBOT_TASK.ICE_MINER else ore_map)*np.where(units > 0, 0, 1)
            units[unit.pos[0], unit.pos[1]] += 1
            # --- если робот на блоке с ресурсом ---
            if robot.onResourcePoint(resource) :
                space = unit.cargo.ice if task == ROBOT_TASK.ICE_MINER else unit.cargo.ore
                max_res = 1000 if task == ROBOT_TASK.ICE_MINER else 150
                # --- строим маршрут к фабрике ---
                __, move_cost, __ = findPathActions(unit, game_state, to=item.getNeareastPoint(unit.pos), lock_map=lock_map, get_move_map=True)
                # --- если не можем ничего выкопать - идём на фабрику ---
                if space >= max_res or not actions.buildDigResource(reserve=sum(move_cost)):
                    npt = item.getNeareastPoint(unit.pos, ignore=True)
                    if getDistance(unit.pos, npt) == 1:
                        actions.buildResourceUnload(npt)
                    else:
                        obs.addReturn(unit.unit_id)
            # --- если робот где-то гуляет ---
            else:
                # --- находим ближайший ресурс ---
                ct = findClosestTile(item.factory.pos, resource, lock_map=obs.getLockMap(unit, task, map_type=MAP_TYPE.FIND))
                # --- находим ближайшую точку фабрики к ресурсу ---
                pt = item.getNeareastPoint(ct)
                dec = unit.pos
                # --- если расстояние до ресурса < n_n*2, то строим маршрут ---
                if getDistance(pt, ct) < (TaskManager.i_n*2 if task == ROBOT_TASK.ICE_MINER else TaskManager.o_n*2):
                    # --- если расстояние от ближайшей свободной точки фабрики до ресурса меньше чем от позиции робота ---
                    if getDistance(unit.pos, pt) < getDistance(unit.pos, ct) and getDistance(pt, ct) < getDistance(unit.pos, ct):
                        # --- то идём от неё ---
                        if actions.buildMove(pt, lock_map=lock_map):
                            dec = pt
                    # --- строим маршрут к фабрике от ресурса ---
                    __, move_cost, __ = findPathActions(unit, game_state, to=item.getNeareastPoint(unit.pos), lock_map=lock_map, dec=ct, get_move_map=True)
                    if actions.buildMove(ct, dec=dec, border=20, lock_map=lock_map):
                        move_map = actions.getMoveMap()[-1]
                        if move_map[ct[0]][ct[1]] > 0:
                            actions.buildDigResource(reserve=sum(move_cost))
                    # --- иначе - идём на базу ---
                    else:
                        obs.addReturn(unit.unit_id)
                else:
                    obs.addReturn(unit.unit_id)
        # --- если робот не на фабрике и он - чистильщик ---
        elif task == ROBOT_TASK.CLEANER:
            # --- строим маршрут к фабрике ---
            target = rubble_map
            __, f_move_cost = findPathActions(unit, game_state, to=item.getNeareastPoint(unit.pos), lock_map=lock_map)
            lock_find_map = obs.getLockMap(unit, task, MAP_TYPE.FIND)
            to_factory_cost = sum(f_move_cost)
            start_pos = unit.pos
            base = len(actions.actions)
            while not actions.isFull():
                # --- находим ближайший щебень ---
                m_actions, move_cost, move_map = [], [], np.zeros((48, 48), dtype=int)
                ct = findClosestTile(start_pos, target, lock_map=lock_find_map)
                if getDistance(item.factory.pos, ct) > 25:
                    break
                # --- если мы стоим на щебне, то будем копать его ---
                if ct[0] == start_pos[0] and ct[1] == start_pos[1]:
                    move_map[ct[0], ct[1]] = 1
                else:
                    # --- строим маршрут к ресурсу ---
                    m_actions, move_cost, move_map = findPathActions(unit, game_state, dec=start_pos, to=ct, lock_map=lock_map, get_move_map=True, 
                                                                     reserve=actions.energy_cost+to_factory_cost)
                    to_factory_cost += sum(move_cost)
                
                dig_count, __, __ = calcDigCount(unit, count=target[ct[0]][ct[1]], reserve_energy=actions.energy_cost+to_factory_cost,
                                                 dig_type=DIG_TYPES.RUBBLE)
                # --- смотрим, можем ли мы копнуть хотябы раз ---
                if dig_count > 0:
                    # --- добавляем маршрут ---
                    actions.extend(m_actions, move_cost, move_map)
                    # --- если дошли до щебня, то копаем ---
                    if move_map[ct[0]][ct[1]] > 0:
                        if actions.buildDigRubble(target[ct[0]][ct[1]], reserve=to_factory_cost):
                            target[ct[0]][ct[1]] -= min(actions.rubble_gain.get('last', 0), target[ct[0]][ct[1]])
                        else: break
                    else: break
                    start_pos = ct.copy()
                # --- если не можем, то идём на базу ---
                else:
                    if len(actions.actions) == base:
                        obs.addReturn(unit.unit_id)
                    break
        # --- если робот не на фабрике и он - давитель ---
        elif task == ROBOT_TASK.WARRION:
            # --- строим маршрут к фабрике ---
            #m_actions, move_cost, move_map = findPathActions(unit, game_state, to=item.getNeareastPoint(unit.pos), lock_map=lock_map, get_move_map=True)
            # --- ищем доступный шаг на врага ---
            next_pos = findClosestTile(unit.pos, np.where(lock_map > 0, eyes.get('e_move'), 0), dec_is_none=False)
            if next_pos is None:
                # --- если не нашли, то пытаемся пойти хоть куда-то ---
                next_pos = findClosestTile(unit.pos, lock_map)
                # --- если не можем походить никуда рядом, то идём на фабрику напролом ---
                if getDistance(unit.pos, next_pos) > 1:
                    next_pos = item.getNeareastPoint(unit.pos)
                    lock_map = np.ones(lock_map.shape, dtype=int)
            # --- если можем шагнуть на врага - шагаем ---
            m_actions, move_cost, move_map = findPathActions(unit, game_state, to=next_pos, lock_map=lock_map, get_move_map=True)
            # --- если энергии хватит ещё и вернуться домой, то давим ---
            #if unit.power - (sum(move_cost) + sum(e_move_cost)) > 1:
            #    m_actions = e_actions
            #    move_cost = e_move_cost
            #    move_map  = e_move_map
            # --- делаем шаг, если можем сделать шаг ---
            if len(m_actions) > 0:
                actions.extend(m_actions, move_cost, move_map)
        # --- если робот не на фабрике и он - убегатель ---
        elif task == ROBOT_TASK.LEAVER:
            # --- выясняем куда мы можем шагнуть ---
            if not actions.buildMove(item.getNeareastPoint(unit.pos), True, 1, lock_map):
                if not actions.buildMove(findClosestTile(unit.pos, lock_map), True, 1, lock_map):
                    actions.buildMove(item.getNeareastPoint(unit.pos), True, 1, lock_map=np.where(eyes.get('factories')+eyes.get('units') > 0, 0, 1))
        # --- если робот не на фабрике и он - уничтожитель ---
        elif task == ROBOT_TASK.DESTROYER:
            # --- строим маршрут к фабрике ---
            target = lichen
            lock_find_map = obs.getLockMap(unit, task, MAP_TYPE.FIND)
            to_factory_cost = 0
            start_pos = unit.pos
            # --- находим ближайший лишайник ---
            m_actions, move_cost, move_map = [], [], np.zeros((48, 48), dtype=int)
            ct = findClosestTile(start_pos, target, lock_map=lock_find_map)
            # --- если мы стоим на лишайнике, то будем копать его ---
            if ct[0] == start_pos[0] and ct[1] == start_pos[1]:
                move_map[ct[0], ct[1]] = 1
            else:
                # --- строим маршрут к ресурсу ---
                m_actions, move_cost, move_map = findPathActions(unit, game_state, dec=start_pos, to=ct, lock_map=lock_map, get_move_map=True, 
                                                                 reserve=actions.energy_cost+to_factory_cost)
                to_factory_cost += sum(move_cost)
            # --- смотрим, можем ли мы копнуть хотябы пару раз ---
            dig_count, __, __ = calcDigCount(unit, count=target[ct[0]][ct[1]], reserve_energy=actions.energy_cost+to_factory_cost,
                                         dig_type=DIG_TYPES.LICHEN)
            if dig_count > 0:
                # --- добавляем маршрут ---
                actions.extend(m_actions, move_cost, move_map)
                # --- если дошли до щебня, то копаем ---
                if move_map[ct[0]][ct[1]] > 0:
                    if actions.buildDigLichen(target[ct[0]][ct[1]], reserve=to_factory_cost):
                        target[ct[0]][ct[1]] -= min(actions.lichen_gain.get('last', 0), target[ct[0]][ct[1]])
        # --- если робот заряжатель ---
        elif task == ROBOT_TASK.ENERGIZER:
            # --- если стоим на своей базе, то работаем ---
            if robot.on_position(item.factory.pos, size=3):
                units = np.zeros((48, 48), dtype=int)
                for t_robot in item.getRobots(task_is=ROBOT_TASK.ICE_MINER):
                    [x, y] = t_robot.robot.pos
                    units[x, y] = 2
                for t_robot in item.getRobots(task_is=ROBOT_TASK.ORE_MINER):
                    [x, y] = t_robot.robot.pos
                    units[x, y] = 1
                # --- убираем из поиска роботов, возле которых стоит ENERGIZER ---
                for t_robot in item.getRobots(task_is=ROBOT_TASK.ENERGIZER, ignore=[unit.unit_id]):
                    for [x, y] in getRad(t_robot.robot.pos):
                        units[x, y] = 0
                if np.max(units) == 2:
                    units = np.where(units == 1, 0, units)
                # --- находим ближайшего робота ---
                if np.max(units) > 0:
                    ct = findClosestTile(unit.pos, units, lock_map=np.where(eyes.get('u_factories') > 0, 0, 1))
                    if getDistance(unit.pos, ct) == 1:
                        if unit.power-actions.energy_cost > unit.unit_cfg.ACTION_QUEUE_POWER_COST*2:
                            r: RobotData = item.findRobotOnPos(ct)
                            if r is not None:
                                n = r.robot.unit_cfg.BATTERY_CAPACITY-r.robot.power
                                if n > unit.unit_cfg.ACTION_QUEUE_POWER_COST*2:
                                    actions.buildTransferResource(RES.energy, ct, min(n, unit.power-actions.energy_cost-unit.unit_cfg.ACTION_QUEUE_POWER_COST*2))
                    else:
                        # --- находим ближайшую точку фабрики к роботу ---
                        pt = item.getNeareastPoint(ct)
                        # --- идём на точку базы ---
                        actions.buildMove(pt, lock_map=lock_map)
            # --- иначе - идём на базу ---
            else:
                obs.addReturn(unit.unit_id)
        # --- если робот копатель траншей ---
        elif task == ROBOT_TASK.CARRIER:
            # --- находим ближайший ресурс ---
            ct = findClosestTile(item.factory.pos, ore_map)
            # --- находим ближайшую точку фабрики к ресурсу ---
            pt = item.getNeareastPoint(ct)
            # --- если расстояние от ближайшей свободной точки фабрики до ресурса меньше чем от позиции робота ---
            dec = unit.pos
            if getDistance(pt, ct) < getDistance(unit.pos, ct):
                # --- то идём от неё ---
                if actions.buildMove(pt, lock_map=lock_map):
                    dec = pt
            # --- строим маршрут к фабрике ---
            __, f_move_cost = findPathActions(unit, game_state, to=pt, lock_map=lock_map)
            # --- строим маршрут с копанием ---
            m_actions, move_cost, move_map = findPathAndDigActions(unit, game_state, rubble_map, dec=dec, to=ct, lock_map=lock_map, get_move_map=True, 
                                                                reserve=actions.energy_cost + sum(f_move_cost))
            # --- если можем что-то сделать, то делаем, иначе - идём на базу ---
            if len(m_actions) > 0:
                actions.extend(m_actions, move_cost, move_map)
            else:
                obs.addReturn(unit.unit_id)
        return actions
# ===============================================================================================================
# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
# ===============================================================================================================