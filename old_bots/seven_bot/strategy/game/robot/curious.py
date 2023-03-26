import numpy as np
from strategy.kits.utils import *

from strategy.kits.eyes import Eyes
from strategy.kits.robot import RobotData
from strategy.kits.factory import FactoryData

class RobotStrategy:
    ''' Убегающая стратегия для роботов '''
    def getLockMap(self, unit, eyes:Eyes, log:bool=False) -> np.ndarray:
        eyes.clear(['u_move', 'u_energy'])
        eyes.update('u_move', unit.pos-1, getRad(unit.pos, as_matrix=True)*RobotData.TYPE.getType(unit.unit_type))
        eyes.update('u_energy', unit.pos-1, getRad(unit.pos, as_matrix=True)*unit.power)
        move_map = eyes.diff(['e_move', 'u_move'])
        energy_map = eyes.diff(['e_energy', 'u_energy'])
        move_map = np.where(move_map == 0, energy_map, move_map)
        move_map = np.where(move_map > 0, 1, 0)
        # --- выясняем куда мы можем шагнуть ---
        locked_field = np.where(eyes.sum(['factories', 'units', move_map]) > 0, 0, 1)
        if log: eyes.log(['factories','units', 'enemy', 'e_move', 'e_energy', 'u_move', 'u_energy', move_map, locked_field])
        return locked_field

    return_robots = []
    def getActions(self, step:int, env, game_state, **kwargs):
        ''' Получить список действий для роботов '''
        f_data = kwargs.get('f_data')
        eyes:Eyes = kwargs.get('eyes')
        if f_data is None or eyes is None:
            raise Exception('f_data or eyes not found in args')
        actions = {}
        ice_map = game_state.board.ice
        rubble_map = game_state.board.rubble
        for __, item in f_data.items():
            for robot in item.robots.values():
                unit = robot.robot
                # по умолчанию берём макс энергии
                take_energy = min(unit.unit_cfg.BATTERY_CAPACITY - unit.power, item.factory.power)
                actions[unit.unit_id] = []
                # --- определяем цену одной смены задачи ---
                action_cost = unit.action_queue_cost(game_state)
                # если у робота пустая очередь
                if len(unit.action_queue) == 0:
                    # --- если робот - копатель ---
                    if robot.robot_task == RobotData.TASK.MINER:
                        # --- находим ближайший ресурс ---
                        ct = findClosestTile(unit.pos, ice_map, lock_map=eyes.neg(eyes.sum([eyes.getFree(1)-ice_map, 'units'])))
                        # --- если робот находится на блоке с фабрикой ---
                        if robot.on_position(item.factory.pos, size=3):
                            # --- если есть ресурсы, то выгружаем ресурсы ---
                            if unit.cargo.ice > 0:
                                actions[unit.unit_id].append(unit.transfer(0, RES.ice, unit.cargo.ice))
                            if unit.cargo.ore > 0:
                                actions[unit.unit_id].append(unit.transfer(0, RES.ore, unit.cargo.ore))
                            if unit.cargo.metal > 0:
                                actions[unit.unit_id].append(unit.transfer(0, RES.metal, unit.cargo.metal))
                            if unit.cargo.water > 0:
                                actions[unit.unit_id].append(unit.transfer(0, RES.water, unit.cargo.water))
                            # --- если у фабрики нет 2 роботов чистильщиков, а уже пора высаживать лишайник - идём чистить ---
                            if robot.robot_type != RobotData.TYPE.HEAVY and \
                                (item.getCount(task_is=RobotData.TASK.CLEANER) == 0 or \
                                step > 700 and item.getCount(task_is=RobotData.TASK.CLEANER) < 2):
                                robot.robot_task = RobotData.TASK.CLEANER
                            else:
                                # --- строим маршрут к ресурсу ---
                                m_actions, move_cost = getMoveActions(game_state, unit, to=ct)
                                # --- если до ресурса <20 ходов, то идём ---
                                if len(m_actions) <= 20:
                                    # --- определяем сколько будем копать ---
                                    __, dig_cost, __ = calcDigCount(unit, reserve_energy=(move_cost + action_cost)*2)
                                    # --- указываем сколько брать энергии ---
                                    need_energy = min((move_cost + action_cost)*2 + dig_cost - unit.power, item.factory.power)
                                    # --- если при взятии энергии нам хватит её чтобы добыть ресурс, то берём по макс ---
                                    if need_energy <= take_energy:
                                        actions[unit.unit_id].append(unit.pickup(RES.energy, take_energy))
                                    # --- если энергии нам не хватит - идём чистить ---
                                    elif robot.robot_type != RobotData.TYPE.HEAVY:
                                        robot.robot_task = RobotData.TASK.CLEANER
                                    robot.min_task = 0
                                # --- Если ближайших ресурсов нет, то идём чистить ---
                                elif robot.robot_type != RobotData.TYPE.HEAVY:
                                    robot.robot_task = RobotData.TASK.CLEANER
                                # --- если робот вернулся от куда-то - убираем из массива ---
                                if unit.unit_id in self.return_robots: 
                                    self.return_robots.remove(unit.unit_id)
                        # --- выясняем может ли на нас шагнуть противник ---
                        locked_field = eyes.get('e_move')
                        # --- если нас не задавят, то ---
                        if locked_field[unit.pos[0], unit.pos[1]] < RobotData.TYPE.getType(unit.unit_type):
                            # --- ищем ближайшего противника ---
                            enemy_pos = findClosestTile(unit.pos, eyes.get('enemy'))
                            # --- считаем за сколько он до нас дойдёт ---
                            e_actions, __ = getMoveActions(game_state, unit, to=enemy_pos)
                            # --- если робот находится на блоке с ресурсом ---
                            if onResourcePoint(unit.pos, ice_map) and unit.unit_id not in self.return_robots:
                                # --- строим маршрут к фабрике ---
                                m_actions, move_cost = getMoveActions(game_state, unit, to=item.factory.pos)
                                # --- определяем сколько будем копать ---
                                dig_count, __, __ = calcDigCount(unit, has_energy=unit.power, reserve_energy=move_cost+action_cost)
                                # --- копаем столько, чтобы успеть докопать, если робот идёт к нам ---
                                dig_count = min(dig_count, len(e_actions)-1)
                                # --- если накопали сколько нужно или макс, то идём на базу ---
                                if robot.min_task <= 0 or unit.cargo.ice == unit.unit_cfg.CARGO_SPACE:
                                    self.return_robots.append(unit.unit_id)
                                # --- если ещё не накопали и можем капнуть больше чем 0 ---
                                elif dig_count > 0:
                                    # --- добавляем действие "копать" ---
                                    actions[unit.unit_id].append(unit.dig(n=dig_count))
                                    robot.min_task -= dig_count
                                else:
                                    # --- иначе, идём на базу ---
                                    self.return_robots.append(unit.unit_id)
                            # --- если робот где-то гуляет ---
                            else:
                                points = []
                                robot.persecution = 0
                                # --- выясняем куда мы можем шагнуть ---
                                locked_field = self.getLockMap(unit, eyes)
                                # --- если робот - идёт на базу ---
                                if unit.unit_id in self.return_robots:
                                    m_actions, move_cost, points = getMoveActions(game_state, unit, to=item.getNeareastPoint(unit.pos), locked_field=locked_field, has_points=True, steps=10)
                                else:
                                    # --- иначе - идём к ресурсу ---
                                    m_actions, move_cost, points = getMoveActions(game_state, unit, to=ct, locked_field=locked_field, has_points=True)
                                    # --- если идти больше чем 20 ходов или нет энергии, чтобы дойти до ресурса, то идём на базу ---
                                    if len(m_actions) >= 20 or unit.power < move_cost + action_cost:
                                        m_actions, move_cost, points = getMoveActions(game_state, unit, to=item.getNeareastPoint(unit.pos), locked_field=locked_field, has_points=True, steps=10)
                                # --- делаем один шаг, если можем сделать шаг ---
                                if len(points) > 0:
                                    if unit.power > move_cost + action_cost:
                                        actions[unit.unit_id].extend(m_actions[:1])
                                        eyes.update('units', getNextMovePos(unit), 0)
                                        eyes.update('units', points[0], 1)
                                        robot.min_task += 1
                        # --- если могут задавить ---
                        else:
                            points = []
                            # --- выясняем куда мы можем шагнуть ---
                            locked_field = self.getLockMap(unit, eyes)
                            # --- ищем ближайшего врага ---
                            e_pos = findClosestTile(unit.pos, eyes.get('e_move')*locked_field)
                            # --- если можем шагнуть на врага - шагаем ---
                            if locked_field[e_pos[0], e_pos[1]] == 1 and robot.getHasPerpecution():
                                m_actions, move_cost, points = getMoveActions(game_state, unit, to=e_pos, locked_field=locked_field, has_points=True)
                                robot.persecution += 1
                            # --- иначе - пытаемся убежать ---
                            else:
                                # --- на врага не ходим ---
                                locked_field[e_pos[0], e_pos[1]] = 0
                                # --- строим маршрут побега ---
                                run_pos = findClosestTile(unit.pos, locked_field)
                                m_actions, move_cost, points = getMoveActions(game_state, unit, to=run_pos, locked_field=locked_field, has_points=True)
                            # --- делаем один шаг, если можем сделать шаг ---
                            if len(points) > 0:
                                if unit.power > move_cost + action_cost:
                                    actions[unit.unit_id].extend(m_actions[:1])
                                    eyes.update('units', getNextMovePos(unit), 0)
                                    eyes.update('units', points[0], 1)
                                    robot.min_task += 1
                    # --- если робот - чистильщик ---
                    elif robot.robot_task == RobotData.TASK.CLEANER:
                        # --- находим ближайший щебень ---
                        ct = findClosestTile(item.factory.pos, rubble_map, lock_map=eyes.update(eyes.neg('units'), unit.pos, 1)*rubble_map)
                        # --- если робот находится на блоке с фабрикой ---
                        if robot.on_position(item.factory.pos, size=3):
                            # --- если у фабрики нет роботов копателей, а высаживать лишайник ещё рано - идём копать ---
                            if step < 500 and item.getCount(task_is=RobotData.TASK.MINER) == 0:
                                robot.robot_task = RobotData.TASK.MINER
                            else:
                                # --- строим маршрут к щебню ---
                                m_actions, move_cost = getMoveActions(game_state, unit, to=ct)
                                # --- определяем сколько будем копать ---
                                dig_count, dig_cost, __ = calcDigCount(unit, count=rubble_map[ct[0]][ct[1]], 
                                                                        reserve_energy=(move_cost*2)*action_cost, dig_type=DIG_TYPES.RUBBLE)
                                # --- указываем сколько брать энергии ---
                                take_energy = min((move_cost + action_cost)*2 + dig_cost - unit.power, item.factory.power)
                                # --- добавляем действие "взять энергию" ---
                                if take_energy > action_cost:
                                    actions[unit.unit_id].append(unit.pickup(RES.energy, take_energy))
                            if unit.unit_id in self.return_robots: 
                                self.return_robots.remove(unit.unit_id)
                        # --- выясняем может ли на нас шагнуть противник ---
                        locked_field = eyes.get('e_move')
                        # --- если нас не задавят, то ---
                        if locked_field[unit.pos[0], unit.pos[1]] < RobotData.TYPE.getType(unit.unit_type):
                            # --- ищем ближайшего противника ---
                            enemy_pos = findClosestTile(unit.pos, eyes.get('enemy'))
                            # --- считаем за сколько он до нас дойдёт ---
                            e_actions, __ = getMoveActions(game_state, unit, to=enemy_pos)
                            # --- если робот находится на блоке с ресурсом ---
                            if robot.on_position(ct, size=1) and unit.unit_id not in self.return_robots:
                                # --- определяем сколько энергии нужно для того, чтобы вернуться ---
                                __, move_cost = getMoveActions(game_state, unit, to=item.getNeareastPoint(unit.pos))
                                # --- определяем сколько будем копать ---
                                dig_count, dig_cost, __ = calcDigCount(unit, count=rubble_map[ct[0]][ct[1]], 
                                                                    has_energy=unit.power, reserve_energy=move_cost+action_cost, dig_type=DIG_TYPES.RUBBLE)
                                # --- копаем столько, чтобы успеть докопать, если робот идёт к нам ---
                                dig_count = min(dig_count, len(e_actions)-1)
                                # --- если можем капнуть хотябы раз ---
                                if dig_count > 0:
                                    # --- добавляем действие "копать" ---
                                    actions[unit.unit_id].append(unit.dig(n=dig_count))
                                    robot.min_task -= dig_count
                                    rubble_map[ct[0]][ct[1]] = 0
                                # --- если нет, то идём на базу ---
                                else:
                                    self.return_robots.append(unit.unit_id)
                            # --- если робот где-то гуляет ---
                            else:
                                points = []
                                robot.persecution = 0
                                # --- выясняем куда мы можем шагнуть ---
                                locked_field = self.getLockMap(unit, eyes)
                                # --- если робот - идёт на базу ---
                                if unit.unit_id in self.return_robots:
                                    m_actions, move_cost, points = getMoveActions(game_state, unit, to=item.getNeareastPoint(unit.pos), locked_field=locked_field, has_points=True, steps=10)
                                else:
                                    # --- иначе - идём к ресурсу ---
                                    m_actions, move_cost, points = getMoveActions(game_state, unit, to=ct, locked_field=locked_field, has_points=True)
                                    # --- если идти больше чем 20 ходов или нет энергии, чтобы дойти до ресурса, то идём на базу ---
                                    if len(m_actions) >= 20 or unit.power < move_cost + action_cost:
                                        m_actions, move_cost, points = getMoveActions(game_state, unit, to=item.getNeareastPoint(unit.pos), locked_field=locked_field, has_points=True, steps=10)
                                # --- делаем один шаг, если можем сделать шаг ---
                                if len(points) > 0:
                                    if unit.power > move_cost + action_cost:
                                        actions[unit.unit_id].extend(m_actions[:1])
                                        eyes.update('units', getNextMovePos(unit), 0)
                                        eyes.update('units', points[0], 1)
                                        robot.min_task += 1
                        # --- если могут задавить ---
                        else:
                            points = []
                            # --- выясняем куда мы можем шагнуть ---
                            locked_field = self.getLockMap(unit, eyes)
                            # --- ищем ближайшего врага ---
                            e_pos = findClosestTile(unit.pos, eyes.get('e_move')*locked_field)
                            # --- если можем шагнуть на врага - шагаем ---
                            if locked_field[e_pos[0], e_pos[1]] == 1 and robot.getHasPerpecution():
                                m_actions, move_cost, points = getMoveActions(game_state, unit, to=e_pos, locked_field=locked_field, has_points=True)
                                robot.persecution += 1
                            # --- иначе - пытаемся убежать ---
                            else:
                                # --- на врага не ходим ---
                                locked_field[e_pos[0], e_pos[1]] = 0
                                # --- строим маршрут побега ---
                                run_pos = findClosestTile(unit.pos, locked_field)
                                m_actions, move_cost, points = getMoveActions(game_state, unit, to=run_pos, locked_field=locked_field, has_points=True)
                            # --- делаем один шаг, если можем сделать шаг ---
                            if len(points) > 0:
                                if unit.power > move_cost + action_cost:
                                    actions[unit.unit_id].extend(m_actions[:1])
                                    eyes.update('units', getNextMovePos(unit), 0)
                                    eyes.update('units', points[0], 1)
                                    robot.min_task += 1
                    # --- если у робота нет задачи, то назначаем её ---
                    elif robot.robot_type == RobotData.TYPE.HEAVY:
                        robot.robot_task = RobotData.TASK.MINER
                    else:
                        robot.robot_task = RobotData.TASK.MINER if step < 500 else RobotData.TASK.CLEANER
                # если действий для робота нет - удаляем массив действий, чтобы не тратить энергию
                # или если не хватает энергии чтобы задать действия
                if (unit.unit_id in actions.keys() and len(actions[unit.unit_id]) == 0) or (unit.power < action_cost): 
                    if unit.unit_id in actions.keys(): del actions[unit.unit_id]
        return actions