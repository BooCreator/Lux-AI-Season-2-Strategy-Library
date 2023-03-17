import numpy as np
from strategy.kits.data_controller import DataController
from strategy.kits.utils import *

from strategy.kits.eyes import Eyes
from strategy.kits.robot import RobotData
from strategy.kits.factory import FactoryData

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
    eyes: Eyes = None
    game_state: GameState = None
    player = None
    env_cfg = None
    step = 0
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    def __init__(self, env_cfg:EnvConfig, factoryStrategy=None, robotStrategy=None) -> None:
        self.env_cfg = env_cfg
        self.data = DataController()
        self.game_state:GameState = None
        self.eyes = Eyes(env_cfg.map_size)
        self.factoryStrategy = FactoryStrategy() if factoryStrategy is None else (factoryStrategy() if type(factoryStrategy) is type else factoryStrategy)
        self.robotStrategy = RobotStrategy() if robotStrategy is None else (robotStrategy() if type(robotStrategy) is type else robotStrategy)
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    # ----- Обновить состояние стратегии (фабрики, роботы) ------------------------------------------------------
    # ------- Инициализация происходит только при первом запуск -------------------------------------------------
    # ------- Сама функция вызывается на каждом ходу ------------------------------------------------------------
    # ------- В случае смены стратегии инициализация должна происходить -----------------------------------------
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    def update(self, game_state:GameState, step:int):
        ''' Обновить состояние стратегии (фабрики, роботы) '''
        self.step = step
        self.game_state = game_state
        self.data.update(game_state)
        self.look(game_state, self.player)
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    # ----- Обновить карты фабрик, юнитов, лишайника TODO -------------------------------------------------------
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    def look(self, game_state:GameState, player: str):
        ''' Обновить карту юнитов '''
        self.eyes.clear(['factories', 'units', 'enemy', 'e_energy', 'e_move'])
        for pl in game_state.factories:
            if pl != player:
                for factory in game_state.factories.get(pl).values():
                    self.eyes.update('factories', factory.pos-1, np.ones((3,3), dtype=int))
        for pl in game_state.units:
            for unit in game_state.units.get(pl).values():
                unit_type = RobotData.TYPE.getType(unit.unit_type)
                if pl == player:
                    self.eyes.update('units', getNextMovePos(unit), unit_type)
                else:
                    self.eyes.update('enemy', getNextMovePos(unit), unit_type)
                    px, py = getRad(unit.pos[0], unit.pos[1])
                    for x, y in zip(px, py):
                        self.eyes.update('e_move', [x, y], unit_type, collision=lambda a,b: max(a,b))
                        self.eyes.update('e_energy', [x, y], unit.power, collision=lambda a,b: max(a,b))
        # лишайник
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    # ----- Получить массив действий для фабрик -----------------------------------------------------------------
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    def getFactoryActions(self) -> dict:
        actions = self.factoryStrategy.getActions(self.step, self.env_cfg, self.game_state, data=self.data)
        return actions
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    # ----- Получить массив действий для роботов ----------------------------------------------------------------
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    def getRobotActions(self) -> dict:
        actions = self.robotStrategy.getActions(self.step, self.env_cfg, self.game_state, data=self.data,
                                                eyes=self.eyes)
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
