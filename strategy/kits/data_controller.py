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
    robots = {}
    player = ''
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    def __init__(self) -> None:
        self.free_robots = []
        self.factories = {}
        self.robots = {}
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
            factory, __ = findClosestFactory(robot.robot.pos, factory_tiles=ft, factory_units=fu)
            self.factories[factory.unit_id].robots[unit_id] = robot
            robot.factory = self.factories.get(factory.unit_id)
        self.free_robots.clear()
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    # ----- Проверить фабрики в данных стратегии ----------------------------------------------------------------
    # ------- Удаляем фабрики, если какая-то была уничтожена ----------------------------------------------------
    # ------- Если фабрик нет - заполняем массив ----------------------------------------------------------------
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    def checkFactories(self, game_state:GameState):
        ''' Проверить фабрики в данных стратегии '''
        # обновляем словарь с фабриками
        for unit_id, factory in game_state.factories[self.player].items():
            if unit_id not in self.factories.keys():
                self.factories[unit_id] = FactoryData(factory)
            else:
                self.factories[unit_id].water.append(factory.cargo.water - self.factories[unit_id].factory.cargo.water)
                self.factories[unit_id].factory = factory
        # удаляем уничтоженные фабрики
        for unit_id in self.factories.copy().keys():
            if unit_id not in game_state.factories[self.player].keys():
                del self.factories[unit_id]
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
            if robot.robot.pos == pos: return robot
        return None
# ===============================================================================================================
# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
# ===============================================================================================================