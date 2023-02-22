import numpy as np
from utils_func import *
from math import ceil, floor

# ===============================================================================================================
# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
# ===============================================================================================================
class EarlyStrategy:
    ''' Класс стратегии ранней игры '''
    spreadRubble = 3  # распространение уровня щебня для повышения важности
    spreadResource = 3
    factory_size = (3,3)
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    def __init__(self, spreadResource=6, spreadRubble=3) -> None:
        self.spreadResource = spreadResource
        self.spreadRubble = spreadRubble
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    # ----- Ставка для выбора позиции ---------------------------------------------------------------------------
    # ------- Если ставка == 0, то очередь по умолчанию. Ресурсы не тратятся ------------------------------------
    # ------- Если ставка > 0, то ставим на первый ход. Ресурсы тратятся ----------------------------------------
    # ------- Если ставка < 0, то ставим на второй ход. Ресурсы тратятся ----------------------------------------
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    def getBid(self) -> int:
        ''' Ставка для выбора позиции '''
        return 0
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    # ----- Получить позицию расположения фабрики ---------------------------------------------------------------
    # ------- Возвращаем массив из двух значений ----------------------------------------------------------------
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    def getSpawnPos(self, game_state, step:int) -> np.ndarray:
        ''' Получить позицию расположения фабрики '''
        ice, ore, rubble, valid = getResFromState(game_state)
        resource = spreadCell(ice if step > 2 else ore, self.spreadResource, max=self.spreadResource*2)
        rubble = normalize(rubble, np.max(resource)/self.spreadRubble)
        rubble = spreadCell(rubble, self.spreadRubble, find=0, val=-1)
        res = resource - rubble if step > 2 else resource
        res = res * valid + valid
        res = conv(res, self.factory_size)
        potential_spawns = np.array(list(zip(*np.where(res==np.max(res)))))
        spawn_loc = potential_spawns[np.random.randint(0, len(potential_spawns))]
        return spawn_loc
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    # ----- Получить ресурсы для каждой фабрики -----------------------------------------------------------------
    # ------- Если мы сделали ставку и выиграли, то ресурсов будет меньше чем 150 для фабрики -------------------
    # ------- Суть функции для указания количества ресурсов для фабрик - 150, 150, 50 или 117, 117, 116 ---------
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    def getResourcesForFactory(self, game_state, player:str, n_factories:int) -> tuple[int, int]:
        ''' Получить ресурсы для каждой фабрики '''
        metal_left:int = ceil(game_state.teams[player].metal / n_factories)
        water_left:int = ceil(game_state.teams[player].water / n_factories)
        return metal_left, water_left
# ===============================================================================================================
# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
# ===============================================================================================================


class RobotData:
    robot = None

    def __init__(self, robot) -> None:
        self.robot = robot

    def on_position(self, pos: np.ndarray, size=1) -> bool:
        size = floor(size/2) + 1
        loc = self.robot.pos - pos
        return True if loc[0] > -size and loc[1] > -size and loc[0] < size and loc[1] < size else False

class FactoryData:
    factory = None
    robots: list[RobotData] = []
    alive = False

    def __init__(self, factory) -> None:
        self.factory = factory
        self.robots = list[RobotData]()
        self.alive = True

    def free_loc(self, units=None):
        robots = units if units is not None else self.robots
        matrix = np.ones((3,3), dtype=int)
        for unit in robots:
            loc = unit.robot.pos - self.factory.pos
            if loc[0] > -2 and loc[1] > -2 and loc[0] < 2 and loc[1] < 2:
                matrix[loc[0]+1, loc[1]+1] = 0
        return matrix

# ===============================================================================================================
# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
# ===============================================================================================================
class GameStrategy:
    ''' Класс стратегии игры '''
    f_data:dict[str,FactoryData] = {}
    free_robots: list[str] = []
    eyes: dict[str, np.ndarray] = {}
    game_state = None
    env = None
    step = 0
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    def __init__(self, env) -> None:
        self.f_data = dict[str,FactoryData]()
        self.free_robots = list[str]()
        self.eyes = dict[str, np.ndarray]()
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
        for item in self.free_robots:
            unit = game_state.units[player].get(item.robot.unit_id)
            if unit is not None:
                cf, __ = findClosestFactory(unit.pos, factory_tiles=ft, factory_units=fu)
                self.f_data[cf.unit_id].robots.append(RobotData(unit))
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
                self.free_robots.extend(item.robots)
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
            new_robots = []
            for unit in robots.values():
                if unit.unit_id in item.robots:
                    new_robots.append(unit)
            item.robots = new_robots
        
        # ищем свободных роботов
        for unit in robots.values():
            has_factory = False
            for item in self.f_data.values():
                if unit in item.robots:
                    has_factory = True
                    break
            if not has_factory and unit not in self.free_robots:
                self.free_robots.append(RobotData(unit))
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
    # ------- Если стоит юнит соперника, то 1, иначе -1 ------------------------------------------------------------
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    def look(self, game_state, player: str):
        ''' Обновить карту юнитов '''
        self.eyes = dict[str, np.ndarray]()
        
        self.eyes['factories'] = np.zeros((self.env.map_size, self.env.map_size), dtype=int)
        for pl in game_state.factories:
            for factory in game_state.factories.get(pl).values():
                for i in range(3):
                    for j in range(3):
                        self.eyes['factories'][i+factory.pos[0]-1, j+factory.pos[1]-1] = -1 if pl == player else 1
        
        self.eyes['units'] = np.zeros((self.env.map_size, self.env.map_size), dtype=int)
        for pl in game_state.units:
            for unit in game_state.units.get(pl).values():
                self.eyes['units'][unit.pos[0], unit.pos[1]] = -1 if pl == player else 1
        
        # лишайник
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    # -----
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    def getFactoryActions(self) -> dict:
        actions = {}
        for unit_id, item in self.f_data.items():
            fact_free_loc = item.free_loc()
            if np.sum(fact_free_loc) > 0 and fact_free_loc[1][1] == 1 and \
                item.factory.power >= self.env.ROBOTS["LIGHT"].POWER_COST and \
                item.factory.cargo.metal >= self.env.ROBOTS["LIGHT"].METAL_COST and len(item.robots) < 1:
                actions[unit_id] = item.factory.build_light()
            elif self.step > 500 and item.factory.water_cost(self.game_state) <= item.factory.cargo.water / 5 - 200:
                actions[unit_id] = item.factory.water()
        return actions
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    # -----
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    miner_robots = []
    return_robots = []
    def getRobotActions(self) -> dict:
        actions = {}
        ice_map = self.game_state.board.ice
        for __, item in self.f_data.items():
            for robot in item.robots:
                unit = robot.robot
                # если у робота пустая очередь
                if len(unit.action_queue) == 0:
                    actions[unit.unit_id] = []
                    # --- находим ближайший ресурс ---
                    ct = findClosestTile(unit.pos, ice_map) 
                    # --- определяем цену одной смены задачи ---
                    action_cost = unit.action_queue_cost(self.game_state)        
                    # --- если робот находится на блоке с фабрикой ---
                    if robot.on_position(item.factory.pos, size=3):
                        # --- строим маршрут к ресурсу ---
                        m_actions, move_cost = getMoveActions(self.game_state, unit, to=ct) 
                        # --- определяем сколько будем копать ---
                        __, dig_cost = calcDigCount(unit, on_factory=item.factory, reserve_cost=(move_cost + action_cost*len(m_actions))*2)
                        # --- если есть, то выгружаем ресурсы ---
                        if unit.cargo.ice > 0:
                            actions[unit.unit_id].append(unit.transfer(0, RES.ice, unit.cargo.ice))
                        if unit.cargo.ore > 0:
                            actions[unit.unit_id].append(unit.transfer(0, RES.ore, unit.cargo.ore))
                        if unit.cargo.metal > 0:
                            actions[unit.unit_id].append(unit.transfer(0, RES.metal, unit.cargo.metal))
                        if unit.cargo.water > 0:
                            actions[unit.unit_id].append(unit.transfer(0, RES.water, unit.cargo.water))
                        # --- добавляем действие "взять энергию" ---
                        actions[unit.unit_id].append(unit.pickup(RES.energy, (move_cost + action_cost)*2 + dig_cost - unit.power))
                        # --- добавляем действия для выхода с базы ---
                        actions[unit.unit_id].extend(m_actions[:4])
                        # --- добавляем в список роботов копателей ---
                        if unit.unit_id in self.return_robots: self.return_robots.remove(unit.unit_id)
                        self.miner_robots.append(unit.unit_id)
                    # --- если робот находится на блоке с ресурсом ---
                    elif robot.on_position(ct) and unit.unit_id in self.miner_robots:
                        # --- строим маршрут к фабрике ---
                        m_actions, move_cost = getMoveActions(self.game_state, unit, to=item.factory.pos)
                        # --- определяем сколько будем копать ---
                        dig_count, __ = calcDigCount(unit, reserve_cost=(move_cost + action_cost*len(m_actions)))
                        if dig_count > 0:
                            # --- добавляем действие "копать" ---
                            actions[unit.unit_id].append(unit.dig(n=dig_count))
                        else:
                            # --- если копать больше не можем, то возвращаем на базу ---
                            self.miner_robots.remove(unit.unit_id)
                            self.return_robots.append(unit.unit_id)
                    # --- если робот где-то гуляет ---
                    else:
                        # --- выясняем куда мы можем шагнуть ---
                        locked_field = np.zeros((self.env.map_size, self.env.map_size), dtype=int)
                        locked_field = np.where(self.eyes['factories'] + self.eyes['units']*-1 > 0, locked_field, 1)
                        # --- если робот - копатель ---
                        if unit.unit_id in self.miner_robots:
                            # --- строим маршрут к ресурсу (1 шаг) ---
                            m_actions, move_cost = getMoveActions(self.game_state, unit, to=ct, locked_field=locked_field)
                            # --- делаем один шаг ---
                            actions[unit.unit_id].extend(m_actions[:1])
                        # --- если робот - идёт на базу ---
                        elif unit.unit_id in self.return_robots:
                            # --- строим маршрут к базе (1 шаг) ---
                            m_actions, move_cost = getMoveActions(self.game_state, unit, to=item.factory.pos, locked_field=locked_field)
                            # --- делаем один шаг ---
                            actions[unit.unit_id].extend(m_actions[:1])
                # если действий для робота нет - удаляем массив действий, чтобы не тратить энергию
                if unit.unit_id in actions.keys() and len(actions[unit.unit_id]) == 0: 
                    del actions[unit.unit_id]
        return actions
# ===============================================================================================================
# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
# ===============================================================================================================


# ===============================================================================================================
# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
# ===============================================================================================================
class Strategy:
    ''' Общий класс стратегии '''
    early: EarlyStrategy = None
    game: GameStrategy = None
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    def __init__(self, env_cfg, early:EarlyStrategy=None, game:GameStrategy=None) -> None:
        self.early = early or EarlyStrategy()
        self.game  = game  or GameStrategy(env=env_cfg)
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    # ----- Обновить состояние стратегии ------------------------------------------------------------------------
    # ------- Можно изменять стратегии в процессе игры ----------------------------------------------------------
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    def update(self, game_state, player, step):
        ''' Обновить состояние стратегии '''
        self.game.update(game_state, player, step)
# ===============================================================================================================
# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
# ===============================================================================================================