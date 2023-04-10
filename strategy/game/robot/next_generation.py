import numpy as np
from lux.unit import Unit
from strategy.kits.action_fabric import ActionsFabric

from strategy.kits.data_controller import DataController
from strategy.kits.observer import MAP_TYPE, Observer
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
        # --- перебираем всех роботов и их задачи ---
        for robot, task in zip(robots, tasks):
            robot: RobotData
            unit, item = robot.robot, robot.factory
            actions = ActionsFabric(game_state, robot)
           
            if task == ROBOT_TASK.WALKER:
                task = robot.robot_task
            # --- если робот находится на своей фабрике ---
            elif robot.on_position(item.factory.pos, size=3):
                # --- добавляем действия взятия энергии ---
                take_energy = min(unit.unit_cfg.BATTERY_CAPACITY - unit.power, item.factory.power)
                # --- устанавливаем базовую задачу робота ---
                task = robot.robot_task if task == ROBOT_TASK.RETURN else task
                # --- если робот вернулся от куда-то, то удаляем его из массива ---
                actions.buildResourceUnload(item.getNeareastPoint(unit.pos))
                actions.buildTakeEnergy(take_energy)
                obs.removeReturn(unit.unit_id)
            elif robot.on_position(item.factory.pos, size=5) and (task != ROBOT_TASK.LEAVER or task != ROBOT_TASK.WARRION):
                # --- выгружаем ресурс, если выгрузили, то удаляем из возвращающихся ---
                if actions.buildResourceUnload(item.getNeareastPoint(unit.pos)):
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
            ct = item.getNeareastPoint(unit.pos)
            m_actions, move_cost, move_map = findPathActions(unit, game_state, to=ct, lock_map=lock_map, get_move_map=True)
            if robot.getResCount() > 0 and move_map[ct[0], ct[1]] > 0 and getDistance(ct, unit.pos) > 1:
                m_actions[-1][-1] -= 1
                if m_actions[-1][-1] == 0:
                    del m_actions[-1]
                    del move_cost[-1]
                move_map[ct[0], ct[1]] = 0
            actions.extend(m_actions, move_cost, move_map)
            obs.addReturn(unit.unit_id)
        # --- если робот заряжается ---
        elif task == ROBOT_TASK.RECHARGE:
            actions.buildReharge(getNextMoveEnergyCost(game_state, unit))
        # --- если робот не на фабрике и он - копатель ---
        elif task == ROBOT_TASK.ICE_MINER or task == ROBOT_TASK.ORE_MINER:
            eyes.update('units', unit.pos, -1, collision=lambda a,b: a+b)
            resource = (ice_map if task == ROBOT_TASK.ICE_MINER else ore_map)*np.where(eyes.get('units') > 0, 0, 1)
            eyes.update('units', unit.pos, 1, collision=lambda a,b: a+b)
            # --- если робот на блоке с ресурсом ---
            if robot.onResourcePoint(resource) :
                space = unit.cargo.ice if task == ROBOT_TASK.ICE_MINER else unit.cargo.ore
                max_res = 1000 if task == ROBOT_TASK.ICE_MINER else 150
                # --- строим маршрут к фабрике ---
                m_actions, move_cost, move_map = findPathActions(unit, game_state, to=item.getNeareastPoint(unit.pos), lock_map=lock_map, get_move_map=True)
                # --- если не можем ничего выкопать - идём на фабрику ---
                if space >= max_res or not actions.buildDigResource(reserve=sum(move_cost)):
                    actions.extend(m_actions, move_cost, move_map=move_map)
                    obs.addReturn(unit.unit_id)
            # --- если робот где-то гуляет ---
            else:
                # --- находим ближайший ресурс ---
                ct = findClosestTile(item.factory.pos, resource, lock_map=obs.getLockMap(unit, task, map_type=MAP_TYPE.FIND))
                # --- находим ближайшую точку фабрики к ресурсу ---
                pt = item.getNeareastPoint(ct)
                # --- если расстояние от ближайшей свободной точки фабрики до ресурса меньше чем от позиции робота ---
                dec = unit.pos
                if getDistance(pt, ct) < getDistance(unit.pos, ct):
                    # --- то идём от неё ---
                    if actions.buildMove(pt, lock_map=lock_map):
                        dec = pt
                else:
                    # --- иначе идём от робота ---
                    pass
                # --- строим маршрут к фабрике ---
                __, move_cost, move_map = findPathActions(unit, game_state, to=item.getNeareastPoint(unit.pos), lock_map=lock_map, dec=ct, get_move_map=True)
                if actions.buildCarrierMove(ct, rubble_map, dec=dec, border=20, lock_map=lock_map):
                #if actions.buildMove(ct, dec=dec, border=20, lock_map=lock_map):
                    if move_map[ct[0]][ct[1]] > 0:
                        actions.buildDigResource(reserve=actions.last_energy_cost + sum(move_cost))
                # --- иначе - идём на базу ---
                else:
                    obs.addReturn(unit.unit_id)
        # --- если робот не на фабрике и он - чистильщик ---
        elif task == ROBOT_TASK.CLEANER:
            # --- строим маршрут к фабрике ---
            lock_find_map = obs.getLockMap(unit, task, MAP_TYPE.FIND)
            m_actions, move_cost = findPathActions(unit, game_state, to=item.getNeareastPoint(unit.pos), lock_map=lock_map)
            start_pos = unit.pos
            full_energy_cost = sum(move_cost)
            while not actions.isFull():
                # --- находим ближайший щебень ---
                ct = findClosestTile(start_pos, rubble_map, lock_map=lock_find_map)
                if getDistance(start_pos, ct) > 25:
                    robot.setTask(ROBOT_TASK.DESTROYER)
                    break
                # --- строим маршрут к ресурсу ---
                m_actions, move_cost, move_map = findPathActions(unit, game_state, dec=start_pos, to=ct, lock_map=lock_map, get_move_map=True)
                if len(m_actions) > 0:
                    full_energy_cost += sum(move_cost)
                    # --- смотрим, можем ли мы копнуть хотябы пару раз ---
                    dig_count, __, __ = calcDigCount(unit, count=rubble_map[ct[0]][ct[1]], reserve_energy=actions.energy_cost+full_energy_cost,
                                                 dig_type=DIG_TYPES.RUBBLE)
                    if dig_count > 0:
                        actions.extend(m_actions, move_cost, move_map)
                        if move_map[ct[0]][ct[1]] > 0:
                            # --- копаем ---
                            if actions.buildDigRubble(rubble_map[ct[0]][ct[1]], reserve=full_energy_cost):
                                rubble_map[ct[0]][ct[1]] -= min(actions.rubble_gain.get('last', 0), rubble_map[ct[0]][ct[1]])
                            else: break
                        else: break
                        start_pos = ct.copy()
                    # --- если не можем, то идём на базу ---
                    else:
                        actions.buildMove(item.getNeareastPoint(unit.pos), True, lock_map=lock_map)
                        break
                else: break
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
            # --- выясняем куда мы можем шагнуть ---
            if not actions.buildMove(item.getNeareastPoint(unit.pos), True, 1, lock_map):
                actions.buildMove(item.getNeareastPoint(unit.pos), True, 1)
        # --- если робот не на фабрике и он - уничтожитель ---
        elif task == ROBOT_TASK.DESTROYER:
            # --- строим маршрут к фабрике ---
            lock_find_map = obs.getLockMap(unit, task, MAP_TYPE.FIND)
            m_actions, move_cost = findPathActions(unit, game_state, to=item.getNeareastPoint(unit.pos), lock_map=lock_map)
            start_pos = unit.pos
            full_energy_cost = sum(move_cost)
            while not actions.isFull():
                # --- находим ближайший лишайник ---
                m_actions, move_cost = [], []
                move_map = np.zeros((48, 48), dtype=int)
                ct = findClosestTile(start_pos, lichen, lock_map=lock_find_map)
                if ct[0] != start_pos[0] or ct[1] != start_pos[1]:
                    # --- строим маршрут к ресурсу ---
                    m_actions, move_cost, move_map = findPathActions(unit, game_state, dec=start_pos, to=ct, lock_map=lock_map, get_move_map=True)
                    full_energy_cost += sum(move_cost)
                else:
                    move_map[ct[0], ct[1]] = 1
                # --- смотрим, можем ли мы копнуть хотябы пару раз ---
                dig_count, __, __ = calcDigCount(unit, count=lichen[ct[0]][ct[1]], reserve_energy=actions.energy_cost+full_energy_cost,
                                             dig_type=DIG_TYPES.LICHEN)
                if dig_count > 0:
                    actions.extend(m_actions, move_cost, move_map)
                    if move_map[ct[0]][ct[1]] > 0:
                        # --- копаем ---
                        if actions.buildDigLichen(lichen[ct[0]][ct[1]], reserve=full_energy_cost):
                            lichen[ct[0]][ct[1]] -= min(actions.lichen_gain.get('last', 0), lichen[ct[0]][ct[1]])
                        else: break
                    else: break
                    start_pos = ct.copy()
                # --- если не можем, то идём на базу ---
                else:
                    actions.buildMove(item.getNeareastPoint(unit.pos), True, lock_map=lock_map)
                    break
        # --- если робот заряжатель ---
        elif task == ROBOT_TASK.ENERGIZER:
            # --- выясняем куда мы можем шагнуть ---
            #if not actions.buildMove(item.getNeareastPoint(unit.pos), True, 1, lock_map):
            #    actions.buildMove(item.getNeareastPoint(unit.pos), True, 1)
            pass
        return actions
# ===============================================================================================================
# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
# ===============================================================================================================