import numpy as np
from strategy.kits.data_controller import DataController
from strategy.kits.utils import *

from strategy.game.factory.default import FactoryStrategy
from strategy.game.robot.default import RobotStrategy

from lux.kit import GameState
from lux.kit import EnvConfig

# ===============================================================================================================
# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
# ===============================================================================================================
class GameStrategy:
    ''' Класс стратегии игры '''
    data: DataController = None
    game_state: GameState = None
    player = None
    env_cfg = None
    step = 0
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    def __init__(self, env_cfg:EnvConfig, factoryStrategy=None, robotStrategy=None) -> None:
        self.env_cfg = env_cfg
        self.data = DataController(env_cfg)
        self.game_state:GameState = None
        self.factoryStrategy = FactoryStrategy() if factoryStrategy is None else (factoryStrategy() if type(factoryStrategy) is type else factoryStrategy)
        self.robotStrategy = RobotStrategy() if robotStrategy is None else (robotStrategy() if type(robotStrategy) is type else robotStrategy)
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    # ----- Обновить состояние стратегии (фабрики, роботы) ------------------------------------------------------
    # ------- Инициализация происходит только при первом запуск -------------------------------------------------
    # ------- Сама функция вызывается на каждом ходу ------------------------------------------------------------
    # ------- В случае смены стратегии инициализация должна происходить -----------------------------------------
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    #@time_wrapper('game_update', 4)
    def update(self, game_state:GameState, step:int):
        ''' Обновить состояние стратегии (фабрики, роботы) '''
        self.step = step
        self.game_state = game_state
        self.data.update(game_state)
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    # ----- Получить массив действий для фабрик -----------------------------------------------------------------
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    #@time_wrapper('game_getFactoryActions', 4)
    def getFactoryActions(self, f_max:int = 0) -> dict:
        actions = self.factoryStrategy.getActions(self.step, self.env_cfg, self.game_state, data=self.data, f_max=f_max)
        return actions
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    # ----- Получить массив действий для роботов ----------------------------------------------------------------
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    #@time_wrapper('game_getRobotActions', 4)
    def getRobotActions(self) -> dict:
        actions = self.robotStrategy.getActions(self.step, self.env_cfg, self.game_state, data=self.data)
        return actions
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    # ----- Обновить игрока для стратегии -----------------------------------------------------------------------
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    def setPlayer(self, player:str):
        self.data.setPlayer(player)
        self.player = player
        return self
# ===============================================================================================================
# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
# ===============================================================================================================
