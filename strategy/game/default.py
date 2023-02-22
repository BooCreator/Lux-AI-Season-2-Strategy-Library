import numpy as np
from strategy.utils_func import *
from math import ceil, floor

class Eyes:
    ''' Класс "глазок", т.е. работа с информацией на карте. Сбор, преобразование и т.д.
        * Матрицы: 1 - что-то есть, 0 - ничего нет'''
    map_size: list[int] = [48, 48]
    data: dict[str, np.ndarray] = None

    def __init__(self, map_size:list[int]=None) -> None:
        self.map_size = map_size if map_size is not None else [48, 48]
        self.data = {}
    
    def update(self, name:str, index:list[int], value:int=1, *, check_keys:bool=True):
        if name not in self.data.keys(): 
            if check_keys: raise Exception(f'Field {name} not found!')
            self.clear(name)
        self.data[name][index[0], index[1]] = value

    def clear(self, name:str, *, value:int=0, names:list[str]=None): # ['fields', 'fields'] or [{'fields': 1, 'fields': 0}]
        shape = (self.map_size, self.map_size)
        if names is not None:
            for name in names:
                if type(name) is str:
                    self.data[name] = np.ones(shape, dtype=int) * value
                elif type(name) is dict and len(name) > 0:
                    self.data[name.keys()[0]] = np.ones(shape, dtype=int) * name.values()[0]
        else:
            self.data[name] = np.ones(shape, dtype=int) * value

    def sum(self, names:list[str]) -> np.ndarray: # ['fields', 'fields', np.ndarray[48, 48]]
        result = np.zeros((self.map_size, self.map_size))
        for name in names:
            if type(name) is str:
                result = result + self.data.get(name) or np.zeros((self.map_size, self.map_size))
            elif type(name) is np.ndarray:
                result = result + name
        return result
    
    def diff(self, names:list[str]) -> np.ndarray: # ['fields', 'fields', np.ndarray[48, 48]]
        result = np.zeros((self.map_size, self.map_size))
        for name in names:
            if type(name) is str:
                result = result - self.data.get(name) or np.zeros((self.map_size, self.map_size))
            elif type(name) is np.ndarray:
                result = result - name
        return result

    def get(self, name:str) -> np.ndarray:
        return self.data.get(name)

    def getLocketField(self, names:list[str]) -> np.ndarray:
        ''' Получить матрицу запрещённых ходов
            0 - блокирован проход, 1 - проход возможен '''
        locked_field = np.ones((self.map_size, self.map_size), dtype=int)
        energy = self.eyes['e_energy'] - self.eyes['u_energy']
        energy = np.where(energy > 0, energy, 0)
        if np.max(energy) > 0: energy /= np.max(energy)
        locked_field = np.where(self.eyes['factories'] + self.eyes['units'] + energy > 0, locked_field, 1)
        return locked_field





class RobotData:
    ''' Класс данных робота '''

    class TYPE:
        ''' Тип робота LIGHT - 0, HEAVY - 1 '''
        LIGHT = 0
        HEAVY = 1

        def getType(type_name:str) -> int:
            return 0 if type_name == 'LIGHT' else 1

    class TASK:
        ''' Тип работы робота: MINER - 0, CLEANER - 1'''
        MINER = 0
        CLEANER = 1
        # COURIER = 2
        # WARRION = 3

        def getTask(task_name:str) -> int:
            return 0 if task_name == 'MINER' else 1

    robot = None
    robot_type: TYPE = 0 
    robot_task: TASK = 1
    min_task: int = 0 # сколько раз, минимально, нужно выполнить task
    
    def __init__(self, robot) -> None:
        self.robot = robot
        self.robot_type = RobotData.TYPE.getType(robot.unit_type)

    def on_position(self, pos:np.ndarray,*, size:int=1) -> bool:
        size = floor(size/2) + 1
        loc = self.robot.pos - pos
        return True if loc[0] > -size and loc[1] > -size and loc[0] < size and loc[1] < size else False

class FactoryData:
    ''' Класс данных фабрики '''
    factory = None
    robots: dict[str, RobotData] = []
    alive = False

    def __init__(self, factory) -> None:
        self.factory = factory
        self.robots = dict[str, RobotData]()
        self.alive = True

    def getRobotsOnType(self, robot_type: int = 0) -> int:
        result = []
        if type(robot_type) is str: robot_type = RobotData.TYPE.getType(robot_type)
        for unit in self.robots.values():
            if unit.robot_type == robot_type: result.append(unit)
        return result

    def getRobotstOnTask(self, robot_task: int = 0) -> int:
        result = []
        if type(robot_task) is str: robot_task = RobotData.TASK.getTask(robot_task)
        for unit in self.robots.values():
            if unit.robot_task == robot_task: result.append(unit)
        return result

    def getCountOnType(self, robot_type: int = 0) -> int:
        n = 0
        if type(robot_type) is str: robot_type = RobotData.TYPE.getType(robot_type)
        for unit in self.robots.values():
            if unit.robot_type == robot_type: n += 1
        return n

    def getCountOnTask(self, robot_task: int = 0) -> int:
        n = 0
        if type(robot_task) is str: robot_task = RobotData.TASK.getTask(robot_task)
        for unit in self.robots.values():
            if unit.robot_task == robot_task: n += 1
        return n

    def getFreeLocation(self):
        matrix = np.ones((3,3), dtype=int)
        for unit in self.robots.values():
            loc = unit.robot.pos - self.factory.pos
            if loc[0] > -2 and loc[1] > -2 and loc[0] < 2 and loc[1] < 2:
                matrix[loc[0]+1, loc[1]+1] = 0
        return matrix
    
    def getNeareastPoint(self, point: np.ndarray) -> np.ndarray:
        minX, minY = self.factory.pos[0], self.factory.pos[1]
        min = abs(point[0]-minX) + abs(point[1]-minY)
        x, y = getRect(minX, minY, 1)
        for x, y in zip(x, y):
            if abs(point[0]-x) + abs(point[1]-y) < min:
                minX, minY = x, y
        return np.array([minX, minY])

# ===============================================================================================================
# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
# ===============================================================================================================
class GameStrategy:
    ''' Класс стратегии игры '''
    f_data:dict[str,FactoryData] = {}
    free_robots: list[str] = []
    eyes: Eyes = None
    game_state = None
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
    def update(self, game_state, player, step):
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
        self.eyes.clear(names=['factories', 'units', 'enemy', 'e_energy', 'u_energy', 'resources'])
        for pl in game_state.factories:
            for factory in game_state.factories.get(pl).values():
                for i in range(3):
                    for j in range(3):
                        self.eyes.update('factories', [i+factory.pos[0]-1, j+factory.pos[1]-1], 0 if pl == player else 1)
        for pl in game_state.units:
            for unit in game_state.units.get(pl).values():
                x, y = getRad(unit.pos[0], unit.pos[1])
                for x, y in zip(x, y):
                    self.eyes.update('u_energy' if pl == player else 'e_energy', [x, y], unit.power)
                self.eyes.update('units' if pl == player else 'enemy', [unit.pos[0], unit.pos[1]], 1)
                self.eyes.update('resources', [unit.pos[0], unit.pos[1]], 1)
        
        # лишайник
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    # -----
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    def getFactoryActions(self, step:int) -> dict:
        actions = {}
        for unit_id, item in self.f_data.items():
            fact_free_loc = item.getFreeLocation()
            if self.step < 500 and fact_free_loc[1][1] == 1:
                if item.factory.power >= self.env.ROBOTS["LIGHT"].POWER_COST and \
                    item.factory.cargo.metal >= self.env.ROBOTS["LIGHT"].METAL_COST and item.getCountOnType('LIGHT') < 5:
                    actions[unit_id] = item.factory.build_light()
                if item.factory.power >= self.env.ROBOTS["HEAVY"].BATTERY_CAPACITY and \
                    item.factory.cargo.metal >= self.env.ROBOTS["HEAVY"].METAL_COST and item.getCountOnType('HEAVY') < 0:
                    actions[unit_id] = item.factory.build_heavy()
            elif self.step > 500 and item.factory.water_cost(self.game_state) <= item.factory.cargo.water / 5 - 200:
                actions[unit_id] = item.factory.water()
        return actions
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    # -----
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
                # если у робота пустая очередь
                if len(unit.action_queue) == 0:
                    actions[unit.unit_id] = []
                    # --- определяем цену одной смены задачи ---
                    action_cost = unit.action_queue_cost(self.game_state) 
                    # по умолчанию не берём энергии
                    take_energy = 0 # unit.unit_cfg.BATTERY_CAPACITY - unit.power
                    # --- если робот - копатель ---
                    if robot.robot_task == RobotData.TASK.MINER:
                        # --- находим ближайший ресурс ---
                        ct = findClosestTile(unit.pos, ice_map, free_resources=self.eyes['free_resources']) 
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
                            m_actions, move_cost = getMoveActions(self.game_state, unit, to=ct)
                            # --- определяем сколько будем копать ---
                            __, dig_cost, __ = calcDigCount(unit, reserve_energy=(move_cost + action_cost)*2)
                            # --- указываем сколько брать энергии ---
                            take_energy = min((move_cost + action_cost)*2 + dig_cost - unit.power, item.factory.power)
                            # --- добавляем действие "взять энергию" ---
                            if take_energy > action_cost:
                                actions[unit.unit_id].append(unit.pickup(RES.energy, take_energy))
                            if unit.unit_id in self.return_robots: 
                                self.return_robots.remove(unit.unit_id)
                            robot.min_task = 0
                        # --- если робот находится на блоке с ресурсом ---
                        if onResourcePoint(robot.robot.pos, ice_map) and unit.unit_id not in self.return_robots:
                            # --- строим маршрут к фабрике ---
                            m_actions, move_cost = getMoveActions(self.game_state, unit, to=item.factory.pos)
                            # --- определяем сколько будем копать ---
                            dig_count, __, __ = calcDigCount(unit)
                            # --- если накопали сколько нужно или макс, то идём на базу ---
                            if unit.cargo.ice >= robot.min_task or unit.cargo.ice == unit.unit_cfg.CARGO_SPACE:
                                self.return_robots.append(unit.unit_id)
                            # --- если ещё не накопали, но можем капнуть больше чем 0 ---
                            elif dig_count > 0:
                                # --- добавляем действие "копать" ---
                                actions[unit.unit_id].append(unit.dig(n=dig_count))
                            else:
                                # --- иначе, копим энергию ---
                                how_energy = robot.min_task - unit.cargo.ice + action_cost
                                actions[unit.unit_id].append(unit.recharge(x=how_energy))
                        # --- если робот где-то гуляет ---
                        else:
                            # --- выясняем куда мы можем шагнуть ---
                            locked_field = np.zeros((self.env.map_size, self.env.map_size), dtype=int)
                            energy = self.eyes['e_energy'] - self.eyes['u_energy']
                            energy = np.where(energy > 0, energy, 0)
                            if np.max(energy) > 0: energy /= np.max(energy)
                            locked_field = np.where(self.eyes['factories'] + self.eyes['units'] + energy > 0, locked_field, 1)
                            points = []
                            # --- если робот - идёт на базу ---
                            if unit.unit_id in self.return_robots:
                                m_actions, move_cost, points = getMoveActions(self.game_state, unit, to=item.getNeareastPoint(unit.pos), locked_field=locked_field, has_points=True)
                            # --- иначе - идём к ресурсу ---
                            else:
                                m_actions, move_cost, points = getMoveActions(self.game_state, unit, to=ct, locked_field=locked_field, has_points=True)
                            # --- делаем один шаг, если можем сделать шаг ---
                            if len(points) > 0:
                                if unit.power > move_cost + action_cost:
                                    actions[unit.unit_id].extend(m_actions[:1])
                                    self.eyes.update('units', [unit.pos[0], unit.pos[1]], 0)
                                    self.eyes.update('units', [points[0][0], points[0][1]], 1)
                                    robot.min_task += 1
                                else:
                                    # --- иначе, копим энергию ---
                                    how_energy = move_cost + action_cost
                                    actions[unit.unit_id].append(unit.recharge(x=how_energy))
                    # --- если робот - чистильщик ---
                    elif robot.robot_task == RobotData.TASK.CLEANER:
                        # --- находим ближайший щебень ---
                        ct = findClosestTile(item.factory.pos, rubble_map, free_resources=rubble_map)
                        # --- если робот находится на блоке с фабрикой ---
                        if robot.on_position(item.factory.pos, size=3):
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
                            dig_count, dig_cost, gain = calcDigCount(unit, count=rubble_map[ct[0]][ct[1]], 
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
                            locked_field = np.zeros((self.env.map_size, self.env.map_size), dtype=int)
                            energy = self.eyes['e_energy'] - self.eyes['u_energy']
                            energy = np.where(energy > 0, energy, 0) / np.max(energy)
                            locked_field = np.where(self.eyes['factories'] + self.eyes['units'] + energy > 0, locked_field, 1)
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
                                    self.eyes.update('units', [unit.pos[0], unit.pos[1]], 0)
                                    self.eyes.update('units', [points[0][0], points[0][1]], 1)
                                else:
                                    # --- иначе, копим энергию ---
                                    how_energy = move_cost + action_cost
                                    actions[unit.unit_id].append(unit.recharge(x=how_energy))
                        rubble_map[ct[0], ct[1]] = 0
                    # --- если у робота нет задачи, то назначаем её ---
                    else:
                        robot.robot_task = RobotData.TASK.MINER if step < 500 else RobotData.TASK.CLEANER
                # если действий для робота нет - удаляем массив действий, чтобы не тратить энергию
                if unit.unit_id in actions.keys() and len(actions[unit.unit_id]) == 0: 
                    del actions[unit.unit_id]
        return actions
# ===============================================================================================================
# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
# ===============================================================================================================
