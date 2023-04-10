from strategy.kits.eyes import Eyes
from strategy.kits.utils import *

from strategy.kits.robot import RobotData
from strategy.kits.factory import FactoryData

from lux.kit import GameState

# ===============================================================================================================
# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
# ===============================================================================================================
class DataController:
    ''' Класс для контроля данных фабрик и роботов '''
    free_robots = []
    factories = {}
    e_factories = {}
    e_lichens = []
    robots = {}
    player = ''
    eyes: Eyes = None
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    def __init__(self, env_cfg:EnvConfig) -> None:
        self.free_robots = []
        self.e_factories = {}
        self.factories = {}
        self.robots = {}
        self.player = ''
        self.eyes = Eyes(env_cfg.map_size)
        self.e_lichens = []
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    # ----- Обновить состояние стратегии (фабрики, роботы) ------------------------------------------------------
    # ------- Инициализация происходит только при первом запуск -------------------------------------------------
    # ------- Сама функция вызывается на каждом ходу ------------------------------------------------------------
    # ------- В случае смены стратегии инициализация должна происходить -----------------------------------------
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    def update(self, game_state:GameState):
        self.checkFactories(game_state)
        self.checkRobots(game_state)
        # назначаем свободных роботов фабрикам
        ft, fu = self.getFactoryInfo()
        for unit_id in self.free_robots:
            robot:RobotData = self.robots.get(unit_id)
            factory = findClosestFactory(robot.robot.pos, ft, fu)
            self.factories[factory.unit_id].robots[unit_id] = robot
            robot.factory = self.factories.get(factory.unit_id)
        self.free_robots.clear()
        self.look(game_state, self.player)
        return self.eyes
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    # ----- Обновить карты фабрик, юнитов, лишайника TODO -------------------------------------------------------
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    #@time_wrapper('game_look', 4)
    def look(self, game_state:GameState, player: str):
        ''' Обновить карту юнитов '''
        self.eyes.clear(['units', 'e_energy', 'e_move'])
        for pl in game_state.units:
            for unit in game_state.units.get(pl).values():
                unit_type = RobotData.TYPE.getType(unit.unit_type)
                if pl == player:
                    self.eyes.update('units', getNextMovePos(unit), 1, collision=lambda a,b: a+b)
                else:
                    self.eyes.update('e_energy', unit.pos, -unit.power, collision=lambda a,b: a+b)
                    xy = getRad(unit.pos)
                    for [x, y] in xy:
                        self.eyes.update('e_move', [x, y], unit_type, collision=lambda a,b: max(a,b))
                        self.eyes.update('e_energy', [x, y], unit.power, collision=lambda a,b: a+b)
        # лишайник
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    # ----- Проверить фабрики в данных стратегии ----------------------------------------------------------------
    # ------- Удаляем фабрики, если какая-то была уничтожена ----------------------------------------------------
    # ------- Если фабрик нет - заполняем массив ----------------------------------------------------------------
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    def checkFactories(self, game_state:GameState):
        ''' Проверить фабрики в данных стратегии '''
        self.eyes.clear(['e_lichen'])
        
        # обновляем словарь с фабриками
        for pl in game_state.factories:
            if pl == self.player:
                for unit_id, factory in game_state.factories[pl].items():
                    if unit_id not in self.factories.keys():
                        self.factories[unit_id] = FactoryData(factory)
                    else:
                        self.factories[unit_id].water.append(factory.cargo.water - self.factories[unit_id].factory.cargo.water)
                        self.factories[unit_id].factory = factory
                # удаляем уничтоженные фабрики
                for unit_id in self.factories.copy().keys():
                    if unit_id not in game_state.factories[self.player].keys():
                        del self.factories[unit_id]
            else:
                if len(self.e_factories) != len(game_state.factories[pl].keys()):
                    for unit_id, factory in game_state.factories[pl].items():
                        if unit_id not in self.e_factories.keys():
                            self.e_factories[unit_id] = factory.pos
                            self.eyes.update('factories', factory.pos-1, np.ones((3,3), dtype=int), check_keys=False)
                            self.e_lichens.append(factory.strain_id)
                    for unit_id in self.e_factories.copy().keys():
                        if unit_id not in game_state.factories[pl].keys():
                            self.eyes.update('factories', self.e_factories.get(unit_id)-1, np.zeros((3,3), dtype=int))
                            del self.e_factories[unit_id]
        lichen = np.zeros((48, 48), dtype=int)
        for id in self.e_lichens:
            lichen = np.where(game_state.board.lichen_strains == id, game_state.board.lichen, lichen)
        self.eyes.update('e_lichen', [0, 0], lichen)
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    # ----- Проверить роботов в данных стратегии ----------------------------------------------------------------
    # ------- Удаляем робота, если он не существует -------------------------------------------------------------
    # ------- Если фабрик нет - заполняем массив ----------------------------------------------------------------
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    def checkRobots(self, game_state:GameState):
        ''' Проверить роботов в данных стратегии '''
        # обновляем словарь с роботами
        for unit_id, unit in game_state.units[self.player].items():
            if unit_id not in self.robots.keys():
                self.robots[unit_id] = RobotData(unit)
            else:
                self.robots[unit_id].robot = unit
        # удаляем уничтоженные роботы
        for unit_id in self.robots.copy().keys():
            if unit_id not in game_state.units[self.player].keys():
                del self.robots[unit_id]

        # обновляем связи роботов с фабриками
        for fabric in self.factories.values():
            fabric:FactoryData
            for robot_id in fabric.robots.copy().keys():
                if robot_id not in self.robots.keys():
                    del fabric.robots[robot_id]
        for robot_id, robot in self.robots.items():
            robot: RobotData
            if robot.factory is None or robot.factory.factory.unit_id not in self.factories.keys():
                self.free_robots.append(robot_id)
                robot.factory = None
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    # ----- Получить информацию о фабриках (factory_tiles, factory_units) ---------------------------------------
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    def getFactoryInfo(self):
        ''' Получить информацию о фабриках '''
        tiles, units = [], []
        for fabric in self.factories.values():
            fabric: FactoryData
            tiles.append(fabric.factory.pos)
            units.append(fabric.factory)
        return tiles, units
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    # ----- Вернуть список FactoryData --------------------------------------------------------------------------
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    def getFactoryData(self) -> dict:
        return self.factories
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    # ----- Обновить игрока для стратегии -----------------------------------------------------------------------
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    def setPlayer(self, player:str):
        self.player = player
        return self

    def getRobotOnPos(self, pos:np.ndarray) -> RobotData:
        for robot in self.robots.values():
            robot: RobotData
            if robot.robot.pos[0] == pos[0] and robot.robot.pos[1] == pos[1]: return robot
        return None
# ===============================================================================================================
# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
# ===============================================================================================================