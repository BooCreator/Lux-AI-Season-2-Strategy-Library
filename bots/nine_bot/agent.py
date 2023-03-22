from lux.utils import my_turn_to_place_factory
from strategy.kits.lux import obs_to_game_state
from lux.config import EnvConfig
import numpy as np

from strategy.basic import DefaultStrategy as Strategy
from strategy.early.default import EarlyStrategy as Early
from strategy.game.default import GameStrategy as Game

from strategy.game.robot.optimised import RobotStrategy as Robot
from strategy.game.factory.mean_water import FactoryStrategy as Factory

def initStrategy(env_cfg, strategy:dict)->Strategy:
    if strategy is None: return Strategy()
    elif type(strategy) is type: return strategy()
    elif type(strategy) is dict:
        basic = strategy.get('basic', Strategy)
        early = strategy.get('early', Early)
        game = strategy.get('game', Game)
        robot = strategy.get('robot', Robot)
        factory = strategy.get('factory', Factory)
        return basic(env_cfg, early=early(env_cfg), game=game(env_cfg, robotStrategy=robot, factoryStrategy=factory))
    else: return strategy

# ===============================================================================================================
# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
# ===============================================================================================================
class Agent():
    ''' Агент для игры '''
    strategy: Strategy = None # стратегия игры, общая (включающая в себя early и game стратегии)
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    def __init__(self, player:str, env_cfg:EnvConfig, *, strategy:dict=None) -> None:
        self.player = player
        self.opp_player = "player_1" if self.player == "player_0" else "player_0"
        self.env_cfg = env_cfg
        self.strategy = initStrategy(env_cfg, strategy)
        self.strategy.setPlayer(self.player)
        np.random.seed(0)
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    # ----- Фаза расстановки фабрик -----------------------------------------------------------------------------
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    def early_setup(self, step: int, obs, remainingOverageTime: int = 60):
        if step == 0: return self.strategy.getBid()
        else:
            game_state = obs_to_game_state(step, self.env_cfg, obs)
            if my_turn_to_place_factory(game_state.teams[self.player].place_first, step):
                self.strategy.update(game_state, step, early=True)
                return self.strategy.getSpawnPos()
            return dict()
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    # ----- Фаза игры -------------------------------------------------------------------------------------------
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    def act(self, step: int, obs, remainingOverageTime: int = 60):
        game_state = obs_to_game_state(step, self.env_cfg, obs)
        self.strategy.update(game_state, step)
        return self.strategy.getActions()
# ===============================================================================================================
# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
# ===============================================================================================================