import numpy as np
from strategy.kits.utils import *

from strategy.kits.eyes import Eyes
from strategy.kits.robot import RobotData
from strategy.kits.factory import FactoryData

class RobotStrategy:
    ''' Класс для стратегии роботов на стадии игры '''

    def getActions(self, step:int, env, game_state, **kwargs):
        ''' Получить список действий для роботов '''
        actions = {}
        f_data = kwargs.get('f_data')
        eyes = kwargs.get('eyes')
        return_robots = kwargs.get('return_robots')
        if f_data is None or eyes is None or return_robots is None:
            raise Exception('f_data, eyes or return_robots not found in args')
        ice_map = game_state.board.ice
        rubble_map = game_state.board.rubble
        for __, item in f_data.items():
            for robot in item.robots.values():
                # по умолчанию не берём энергии
                take_energy = 0 # unit.unit_cfg.BATTERY_CAPACITY - unit.power
                unit = robot.robot
                actions[unit.unit_id] = []
                # --- определяем цену одной смены задачи ---
                action_cost = unit.action_queue_cost(game_state)
                # если у робота пустая очередь
                if len(unit.action_queue) == 0:
                    # --- если робот - копатель ---
                    if robot.robot_task == RobotData.TASK.MINER:
                        # --- находим ближайший ресурс ---
                        ct = findClosestTile(unit.pos, ice_map, lock_map=eyes.neg(eyes.sum([eyes.getFree(1) - ice_map, 'units'])))
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
                            # --- строим маршрут к ресурсу ---
                            m_actions, move_cost = getMoveActions(game_state, unit, to=ct, steps=1000)
                            if len(m_actions) <= 20:
                                # --- определяем сколько будем копать ---
                                __, dig_cost, __ = calcDigCount(unit, reserve_energy=(move_cost + action_cost)*2)
                                # --- указываем сколько брать энергии ---
                                take_energy = min((move_cost + action_cost)*2 + dig_cost - unit.power, item.factory.power)
                                # --- добавляем действие "взять энергию" ---
                                if take_energy > action_cost:
                                    actions[unit.unit_id].append(unit.pickup(RES.energy, take_energy))
                                if unit.unit_id in return_robots: 
                                    return_robots.remove(unit.unit_id)
                                robot.min_task = 0
                            # --- Если ближайших ресурсов нет, то идём чистить ---
                            elif robot.robot_type != RobotData.TYPE.HEAVY:
                                robot.robot_task = RobotData.TASK.CLEANER
                        # --- если робот находится на блоке с ресурсом ---
                        if onResourcePoint(robot.robot.pos, ice_map) and unit.unit_id not in return_robots:
                            # --- строим маршрут к фабрике ---
                            m_actions, move_cost = getMoveActions(game_state, unit, to=item.factory.pos)
                            # --- определяем сколько будем копать ---
                            dig_count, __, __ = calcDigCount(unit, has_energy=unit.power, reserve_energy=move_cost+action_cost)
                            # --- если накопали сколько нужно или макс, то идём на базу ---
                            if robot.min_task <= 0 or unit.cargo.ice == unit.unit_cfg.CARGO_SPACE:
                                return_robots.append(unit.unit_id)
                            # --- если ещё не накопали, но можем капнуть больше чем 0 ---
                            elif dig_count > 0:
                                # --- добавляем действие "копать" ---
                                actions[unit.unit_id].append(unit.dig(n=dig_count))
                                robot.min_task -= dig_count
                            else:
                                # --- иначе, копим энергию ---
                                how_energy = max(robot.min_task - unit.cargo.ice + action_cost, 20)
                                actions[unit.unit_id].append(unit.recharge(x=how_energy))
                        # --- если робот где-то гуляет ---
                        else:
                            # --- выясняем куда мы можем шагнуть ---
                            locked_field = np.zeros(eyes.map_size, dtype=int)
                            locked_field = np.where(eyes.sum(['factories', 'units', eyes.norm(eyes.diff(['e_energy', 'u_energy']))]) > 0, locked_field, 1)
                            #eyes.log(['factories', 'units', 'e_energy', 'u_energy', locked_field],f'log/step/{player}')
                            points = []
                            # --- если робот - идёт на базу ---
                            if unit.unit_id in return_robots:
                                m_actions, move_cost, points = getMoveActions(game_state, unit, to=item.getNeareastPoint(unit.pos), locked_field=locked_field, has_points=True)
                            # --- иначе - идём к ресурсу ---
                            else:
                                m_actions, move_cost, points = getMoveActions(game_state, unit, to=ct, locked_field=locked_field, has_points=True)
                                # --- если идти больше чем 20 ходов, то идём на базу ---
                                if len(m_actions) >= 20:
                                    m_actions, move_cost, points = getMoveActions(game_state, unit, to=item.getNeareastPoint(unit.pos), locked_field=locked_field, has_points=True)
                            # --- делаем один шаг, если можем сделать шаг ---
                            if len(points) > 0:
                                if unit.power > move_cost + action_cost:
                                    actions[unit.unit_id].extend(m_actions[:1])
                                    eyes.update('units', unit.pos, 0)
                                    eyes.update('units', points[0], 1)
                                    robot.min_task += 1
                                else:
                                    # --- иначе, копим энергию ---
                                    how_energy = move_cost + action_cost
                                    actions[unit.unit_id].append(unit.recharge(x=how_energy))
                    # --- если робот - чистильщик ---
                    elif robot.robot_task == RobotData.TASK.CLEANER:
                        # --- находим ближайший щебень ---
                        ct = findClosestTile(item.factory.pos, rubble_map, lock_map=eyes.update(eyes.neg('units'), unit.pos, 1)*rubble_map)
                        # --- если робот находится на блоке с фабрикой ---
                        if robot.on_position(item.factory.pos, size=3):
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
                            if unit.unit_id in return_robots: 
                                return_robots.remove(unit.unit_id)
                        # --- если робот находится на блоке с щебнем ---
                        if robot.on_position(ct, size=1) and unit.unit_id not in return_robots:
                            # --- определяем сколько энергии нужно для того, чтобы вернуться ---
                            __, move_cost = getMoveActions(game_state, unit, to=item.getNeareastPoint(unit.pos))
                            # --- определяем сколько будем копать ---
                            dig_count, dig_cost, __ = calcDigCount(unit, count=rubble_map[ct[0]][ct[1]], 
                                                                    has_energy=unit.power, reserve_energy=move_cost+action_cost, dig_type=DIG_TYPES.RUBBLE)
                            # --- если можем капнуть хотябы раз ---
                            if dig_count > 0:
                                # --- добавляем действие "копать" ---
                                actions[unit.unit_id].append(unit.dig(n=dig_count))
                                robot.min_task -= dig_count
                                rubble_map[ct[0]][ct[1]] = 0
                            # --- если нет, то идём на базу ---
                            else:
                                return_robots.append(unit.unit_id)
                        # --- если робот где-то гуляет ---
                        else:
                            # --- выясняем куда мы можем шагнуть ---
                            locked_field = np.zeros(eyes.map_size, dtype=int)
                            locked_field = np.where(eyes.sum(['factories', 'units', eyes.norm(eyes.diff([eyes.get('e_energy'), 'u_energy']))]) > 0, locked_field, 1)
                            points = []
                            # --- если робот - идёт на базу ---
                            if unit.unit_id in return_robots:
                                m_actions, move_cost, points = getMoveActions(game_state, unit, to=item.getNeareastPoint(unit.pos), locked_field=locked_field, has_points=True)
                            # --- иначе - идём к щебню ---
                            else:
                                m_actions, move_cost, points = getMoveActions(game_state, unit, to=ct, locked_field=locked_field, has_points=True)
                            # --- делаем один шаг, если можем сделать шаг ---
                            if len(points) > 0:
                                if unit.power >= move_cost + action_cost:
                                    actions[unit.unit_id].extend(m_actions[:1])
                                    eyes.update('units', unit.pos, 0)
                                    eyes.update('units', points[0], 1)
                                else:
                                    # --- иначе, копим энергию ---
                                    how_energy = move_cost + action_cost
                                    actions[unit.unit_id].append(unit.recharge(x=how_energy))
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