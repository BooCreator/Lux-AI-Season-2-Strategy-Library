import numpy as np
from strategy.kits.utils import *

from strategy.kits.eyes import Eyes
from strategy.kits.robot import RobotData
from strategy.kits.factory import FactoryData

# ===============================================================================================================
# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
# ===============================================================================================================
class GameStrategy:
    ''' Класс стратегии игры '''
    f_data:dict[str,FactoryData] = {}
    free_robots: list[str] = []
    eyes: Eyes = None
    game_state = None
    player = None
    env = None
    step = 0
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    def __init__(self, env) -> None:
        self.f_data = dict[str,FactoryData]()
        self.free_robots = list[str]()
        self.eyes = Eyes(env.map_size)
        self.game_state = None
        self.env = env
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    # ----- Обновить состояние стратегии (фабрики, роботы) ------------------------------------------------------
    # ------- Инициализация происходит только при первом запуск -------------------------------------------------
    # ------- Сама функция вызывается на каждом ходу ------------------------------------------------------------
    # ------- В случае смены стратегии инициализация должна происходить -----------------------------------------
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    def update(self, game_state, player:str, step:int):
        ''' Обновить состояние стратегии (фабрики, роботы) '''
        self.checkFactories(game_state.factories[player])
        self.checkRobots(game_state.units[player])
        ft, fu = self.getFactoryInfo()
        for unit_id in self.free_robots:
            unit = game_state.units[player].get(unit_id)
            if unit is not None:
                cf, __ = findClosestFactory(unit.pos, factory_tiles=ft, factory_units=fu)
                self.f_data[cf.unit_id].robots[unit_id] = RobotData(unit)
        self.free_robots.clear()
        self.look(game_state, player)
        self.game_state = game_state
        self.player = player
        self.step = step
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    # ----- Проверить фабрики в данных стратегии ----------------------------------------------------------------
    # ------- Удаляем фабрики, если какая-то была уничтожена ----------------------------------------------------
    # ------- Если фабрик нет - заполняем массив ----------------------------------------------------------------
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    def checkFactories(self, factories):
        ''' Проверить фабрики в данных стратегии '''
        for unit_id, factory in factories.items():
            if unit_id in self.f_data.keys():
                self.f_data[unit_id].alive = True
                self.f_data[unit_id].factory = factory
            else:
                self.f_data[unit_id] = FactoryData(factory)
        to_remove = []
        for unit_id, item in self.f_data.items():
            if not item.alive: 
                for uid in item.robots.keys():
                    self.free_robots.append(uid)
                to_remove.append(unit_id)
            else:
                item.alive = False
        for unit_id in to_remove:
            del self.f_data[unit_id]
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    # ----- Проверить роботов в данных стратегии ----------------------------------------------------------------
    # ------- Удаляем робота, если он не существует -------------------------------------------------------------
    # ------- Если фабрик нет - заполняем массив ----------------------------------------------------------------
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    def checkRobots(self, robots:dict[str]):
        ''' Проверить роботов в данных стратегии '''
        # убираем удалённых роботов
        for item in self.f_data.values():
            has_robots = dict[str, RobotData]()
            for unit in robots.values():
                if unit.unit_id in item.robots.keys():
                    has_robots[unit.unit_id] = item.robots.get(unit.unit_id)
                    has_robots[unit.unit_id].robot = unit
            item.robots = has_robots
        
        # ищем свободных роботов
        for unit in robots.values():
            has_factory = False
            for item in self.f_data.values():
                if unit.unit_id in item.robots.keys():
                    has_factory = True
                    break
            if not has_factory and unit.unit_id not in self.free_robots:
                self.free_robots.append(unit.unit_id)
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    # ----- Получить информацию о фабриках (factory_tiles, factory_units) ---------------------------------------
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    def getFactoryInfo(self) -> tuple[list[list],list]:
        ''' Получить информацию о фабриках '''
        factory_tiles = []
        factory_units = []
        for item in self.f_data.values():
            factory_tiles.append(item.factory.pos)
            factory_units.append(item.factory)
        return factory_tiles, factory_units
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    # ----- Обновить карты фабрик, юнитов, лишайника TODO -------------------------------------------------------
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    def look(self, game_state, player: str):
        ''' Обновить карту юнитов '''
        self.eyes.clear(['factories', 'units', 'enemy', 'e_energy', 'u_energy'])
        for pl in game_state.factories:
            if pl != player:
                for factory in game_state.factories.get(pl).values():
                    self.eyes.update('factories', factory.pos-1, np.ones((3,3), dtype=int))
        for pl in game_state.units:
            for unit in game_state.units.get(pl).values():
                x, y = getRad(unit.pos[0], unit.pos[1])
                for x, y in zip(x, y):
                    self.eyes.update('u_energy' if pl == player else 'e_energy', [x, y], unit.power)
                self.eyes.update('units' if pl == player else 'enemy', getNextMovePos(unit), 1)
        # лишайник
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    # ----- Получить массив действий для фабрик -----------------------------------------------------------------
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    def getFactoryActions(self, step:int) -> dict:
        actions = {}
        for unit_id, item in self.f_data.items():
            fact_free_loc = item.getFreeLocation()
            if step < 500 and fact_free_loc[1][1] == 1:
                if item.factory.power >= self.env.ROBOTS["HEAVY"].BATTERY_CAPACITY and \
                    item.factory.cargo.metal >= self.env.ROBOTS["HEAVY"].METAL_COST and item.getCount(type_is='HEAVY') < 1:
                    actions[unit_id] = item.factory.build_heavy()
                elif item.factory.power >= self.env.ROBOTS["LIGHT"].POWER_COST and \
                    item.factory.cargo.metal >= self.env.ROBOTS["LIGHT"].METAL_COST and item.getCount(type_is='LIGHT') < 4:
                    actions[unit_id] = item.factory.build_light()
            elif step > 500:
                if item.factory.water_cost(self.game_state) <= item.factory.cargo.water / 5 - 200:
                    actions[unit_id] = item.factory.water()
        return actions
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    # ----- Получить массив действий для роботов ----------------------------------------------------------------
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    return_robots = []
    clean_robots = []
    def getRobotActions(self, step:int) -> dict:
        actions = {}
        ice_map = self.game_state.board.ice
        rubble_map = self.game_state.board.rubble
        for __, item in self.f_data.items():
            for robot in item.robots.values():
                unit = robot.robot
                # по умолчанию берём макс энергии
                take_energy = min(unit.unit_cfg.BATTERY_CAPACITY - unit.power, item.factory.power)
                actions[unit.unit_id] = []
                # --- определяем цену одной смены задачи ---
                action_cost = unit.action_queue_cost(self.game_state)
                # если у робота пустая очередь
                if len(unit.action_queue) == 0:
                    # --- если робот - копатель ---
                    if robot.robot_task == RobotData.TASK.MINER:
                        # --- находим ближайший ресурс ---
                        ct = findClosestTile(unit.pos, ice_map, lock_map=self.eyes.neg(self.eyes.sum([self.eyes.getFree(1) - ice_map, 'units'])))
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
                            if item.getCount(task_is=RobotData.TASK.CLEANER) == 0 or \
                                step > 700 and item.getCount(task_is=RobotData.TASK.CLEANER) < 2:
                                robot.robot_task = RobotData.TASK.CLEANER
                            else:
                                # --- строим маршрут к ресурсу ---
                                m_actions, move_cost = getMoveActions(self.game_state, unit, to=ct, steps=25)
                                if len(m_actions) <= 20:
                                    # --- определяем сколько будем копать ---
                                    __, dig_cost, __ = calcDigCount(unit, reserve_energy=(move_cost + action_cost)*2)
                                    # --- указываем сколько брать энергии ---
                                    need_energy = min((move_cost + action_cost)*2 + dig_cost - unit.power, item.factory.power)
                                    # --- если при взятии энергии нам хватит её чтобы добыть ресурс, то берём по макс ---
                                    if need_energy <= take_energy:
                                        actions[unit.unit_id].append(unit.pickup(RES.energy, take_energy))
                                    # --- если энергии нам не хватит - идём чистить ---
                                    else:
                                        robot.robot_task = RobotData.TASK.CLEANER
                                    # --- убираем ---
                                    robot.min_task = 0
                                # --- Если ближайших ресурсов нет, то идём чистить ---
                                else:
                                    robot.robot_task = RobotData.TASK.CLEANER
                            # --- если робот вернулся от куда-то - убираем из массива ---
                            if unit.unit_id in self.return_robots: 
                                self.return_robots.remove(unit.unit_id)
                        # --- если робот находится на блоке с ресурсом ---
                        if onResourcePoint(unit.pos, ice_map) and unit.unit_id not in self.return_robots:
                            # --- выясняем куда может ли на нас шагнуть противник ---
                            locked_field = self.eyes.diff(['e_energy', 'u_energy'])
                            # --- ищем ближайшего противника ---
                            enemy_pos = findClosestTile(unit.pos, self.eyes.get('enemy'))
                            # --- считаем за сколько он до нас дойдёт ---
                            e_actions, __ = getMoveActions(self.game_state, unit, to=enemy_pos)
                            # --- если нас не задавят, то копаем ---
                            if locked_field[unit.pos[0], unit.pos[1]] <= 0:
                                # --- строим маршрут к фабрике ---
                                m_actions, move_cost = getMoveActions(self.game_state, unit, to=item.factory.pos)
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
                            # --- если могут задавить - отходим ---
                            else:
                                # --- выясняем куда мы можем шагнуть ---
                                locked_field = np.zeros(self.eyes.map_size, dtype=int)
                                locked_field = np.where(self.eyes.sum(['factories', 'units', self.eyes.norm(self.eyes.diff(['e_energy', 'u_energy']))]) > 0, locked_field, 1)
                                points = []
                                # строим маршрут побега
                                run_pos = findClosestTile(unit.pos, locked_field)
                                m_actions, move_cost, points = getMoveActions(self.game_state, unit, to=run_pos, locked_field=locked_field, has_points=True)
                                # --- делаем один шаг, если можем сделать шаг ---
                                if len(points) > 0:
                                    if unit.power > move_cost + action_cost:
                                        actions[unit.unit_id].extend(m_actions[:1])
                                        self.eyes.update('units', unit.pos, 0)
                                        self.eyes.update('units', points[0], 1)
                                        robot.min_task += 1
                                    else:
                                        # --- иначе, копим энергию ---
                                        how_energy = move_cost + action_cost
                                        actions[unit.unit_id].append(unit.recharge(x=how_energy))
                        # --- если робот где-то гуляет ---
                        else:
                            # --- выясняем куда мы можем шагнуть ---
                            norm = self.eyes.norm(self.eyes.diff(['e_energy', 'u_energy']))
                            norm = np.where(norm < 0, 0, norm)
                            locked_field = np.where(self.eyes.sum(['factories', 'units', norm]) > 0, 0, 1)
                            #self.eyes.log(['factories', 'units', 'e_energy', 'u_energy', locked_field],f'log/step/{self.player}')
                            points = []
                            # --- если робот - идёт на базу ---
                            if unit.unit_id in self.return_robots:
                                m_actions, move_cost, points = getMoveActions(self.game_state, unit, to=item.getNeareastPoint(unit.pos), locked_field=locked_field, has_points=True)
                            # --- иначе - идём к ресурсу ---
                            else:
                                m_actions, move_cost, points = getMoveActions(self.game_state, unit, to=ct, locked_field=locked_field, has_points=True)
                                # --- если идти больше чем 20 ходов, то идём на базу ---
                                if len(m_actions) >= 20:
                                    m_actions, move_cost, points = getMoveActions(self.game_state, unit, to=item.getNeareastPoint(unit.pos), locked_field=locked_field, has_points=True)
                            # --- делаем один шаг, если можем сделать шаг ---
                            if len(points) > 0:
                                if unit.power > move_cost + action_cost:
                                    actions[unit.unit_id].extend(m_actions[:1])
                                    self.eyes.update('units', unit.pos, 0)
                                    self.eyes.update('units', points[0], 1)
                                    robot.min_task += 1
                                else:
                                    # --- иначе, копим энергию ---
                                    how_energy = move_cost + action_cost
                                    actions[unit.unit_id].append(unit.recharge(x=how_energy))
                    # --- если робот - чистильщик ---
                    elif robot.robot_task == RobotData.TASK.CLEANER:
                        # --- находим ближайший щебень ---
                        ct = findClosestTile(item.factory.pos, rubble_map, lock_map=self.eyes.update(self.eyes.neg('units'), unit.pos, 1)*rubble_map)
                        # --- если робот находится на блоке с фабрикой ---
                        if robot.on_position(item.factory.pos, size=3):
                            # --- если у фабрики нет роботов копателей, а высаживать лишайник ещё рано - идём копать ---
                            if step < 500 and item.getCount(task_is=RobotData.TASK.MINER) == 0:
                                robot.robot_task = RobotData.TASK.MINER
                            else:
                                # --- строим маршрут к щебню ---
                                m_actions, move_cost = getMoveActions(self.game_state, unit, to=ct)
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
                        # --- если робот находится на блоке с щебнем ---
                        if robot.on_position(ct, size=1) and unit.unit_id not in self.return_robots:
                            # --- определяем сколько энергии нужно для того, чтобы вернуться ---
                            __, move_cost = getMoveActions(self.game_state, unit, to=item.getNeareastPoint(unit.pos))
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
                                self.return_robots.append(unit.unit_id)
                        # --- если робот где-то гуляет ---
                        else:
                            # --- выясняем куда мы можем шагнуть ---
                            locked_field = np.zeros(self.eyes.map_size, dtype=int)
                            norm = self.eyes.norm(self.eyes.diff(['e_energy', 'u_energy']))
                            norm = np.where(norm < 0, 0, norm)
                            locked_field = np.where(self.eyes.sum(['factories', 'units', norm]) > 0, locked_field, 1)
                            points = []
                            # --- если робот - идёт на базу ---
                            if unit.unit_id in self.return_robots:
                                m_actions, move_cost, points = getMoveActions(self.game_state, unit, to=item.getNeareastPoint(unit.pos), locked_field=locked_field, has_points=True)
                            # --- иначе - идём к щебню ---
                            else:
                                m_actions, move_cost, points = getMoveActions(self.game_state, unit, to=ct, locked_field=locked_field, has_points=True)
                            # --- делаем один шаг, если можем сделать шаг ---
                            if len(points) > 0:
                                if unit.power >= move_cost + action_cost:
                                    actions[unit.unit_id].extend(m_actions[:1])
                                    self.eyes.update('units', unit.pos, 0)
                                    self.eyes.update('units', points[0], 1)
                                else:
                                    # --- иначе, копим энергию ---
                                    how_energy = move_cost + action_cost
                                    actions[unit.unit_id].append(unit.recharge(x=how_energy))
                    # --- если у робота нет задачи, то назначаем её ---
                    else:
                        robot.robot_task = RobotData.TASK.MINER if step < 500 else RobotData.TASK.CLEANER
                # если действий для робота нет - удаляем массив действий, чтобы не тратить энергию
                # или если не хватает энергии чтобы задать действия
                if (unit.unit_id in actions.keys() and len(actions[unit.unit_id]) == 0) or (unit.power < action_cost): 
                    if unit.unit_id in actions.keys(): del actions[unit.unit_id]
        return actions
# ===============================================================================================================
# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
# ===============================================================================================================
