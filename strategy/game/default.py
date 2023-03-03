import numpy as np
from strategy.kits.utils import *

from strategy.kits.eyes import Eyes
from strategy.kits.robot import RobotData
from strategy.kits.factory import FactoryData

from strategy.game.factory.default import FactoryStrategy
from strategy.game.robot.default import RobotStrategy

# ===============================================================================================================
# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
# ===============================================================================================================
class GameStrategy:
    ''' Класс стратегии игры '''
    f_data = {}
    free_robots = []
    eyes: Eyes = None
    game_state = None
    player = None
    env = None
    step = 0
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    def __init__(self, env, factoryStrategy=None, robotStrategy=None) -> None:
        self.f_data = {}
        self.free_robots = []
        self.eyes = Eyes(env.map_size)
        self.factoryStrategy = FactoryStrategy() if factoryStrategy is None else (factoryStrategy() if type(factoryStrategy) is type else factoryStrategy)
        self.robotStrategy = RobotStrategy() if robotStrategy is None else (robotStrategy() if type(robotStrategy) is type else robotStrategy)
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
                self.f_data[unit_id].water.append(factory.cargo.water - self.f_data[unit_id].factory.cargo.water)
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
    def checkRobots(self, robots:dict):
        ''' Проверить роботов в данных стратегии '''

        # убираем удалённых роботов
        for item in self.f_data.values():
            has_robots = {}
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
    def getFactoryInfo(self):
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
        self.eyes.clear(['factories', 'units', 'enemy', 'e_energy', 'u_energy', 'u_move', 'e_move'])
        for pl in game_state.factories:
            if pl != player:
                for factory in game_state.factories.get(pl).values():
                    self.eyes.update('factories', factory.pos-1, np.ones((3,3), dtype=int))
        for pl in game_state.units:
            for unit in game_state.units.get(pl).values():
                px, py = getRad(unit.pos[0], unit.pos[1])
                unit_type = RobotData.TYPE.getType(unit.unit_type)
                if pl == player:
                    self.eyes.update('units', getNextMovePos(unit), unit_type)
                    for x, y in zip(px, py):
                        self.eyes.update('u_move', [x, y], unit_type)
                        self.eyes.update('u_energy', [x, y], unit.power)
                else:
                    self.eyes.update('enemy', getNextMovePos(unit), unit_type)
                    for x, y in zip(px, py):
                        self.eyes.update('e_move', [x, y], unit_type)
                        self.eyes.update('e_energy', [x, y], unit.power)
        
        # лишайник
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    # ----- Получить массив действий для фабрик -----------------------------------------------------------------
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    def getFactoryActions(self, step:int) -> dict:
        actions = self.factoryStrategy.getActions(step, self.env, self.game_state, f_data=self.f_data)
        return actions
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    # ----- Получить массив действий для роботов ----------------------------------------------------------------
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    return_robots = []
    clean_robots = []
    def getRobotActions(self, step:int) -> dict:
        actions = self.robotStrategy.getActions(step, self.env, self.game_state, f_data=self.f_data, 
                                                eyes=self.eyes, return_robots=self.return_robots)
        return actions
# ===============================================================================================================
# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
# ===============================================================================================================
