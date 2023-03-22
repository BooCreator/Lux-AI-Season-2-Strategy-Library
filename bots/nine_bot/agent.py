from lux.utils import my_turn_to_place_factory
from strategy.kits.lux import obs_to_game_state
from lux.config import EnvConfig
import numpy as np

# ----- default -----
from strategy.basic import DefaultStrategy
# ----- early -----
from strategy.early.default import EarlyStrategy as DefaultEarly
from strategy.early.from_kaggle_strategy import EarlyStrategy as OptimisedEarly
# ----- game -----
from strategy.game.default import GameStrategy as DefaultGame
from strategy.game.cautious import GameStrategy as CautiousStrategy
# ----- robot -----
from strategy.game.robot.cautious import RobotStrategy as CautiousRobots
from strategy.game.robot.curious import RobotStrategy as CuriousRobots
from strategy.game.robot.optimised import RobotStrategy as OptimisedRobots
# ----- factory -----
from strategy.game.factory.mean_water import FactoryStrategy as MeanWaterStrategy

ddf = {
    'basic': DefaultStrategy,
    'early': OptimisedEarly,
    'game': DefaultGame,
    'robot': OptimisedRobots,
    'factory': MeanWaterStrategy
}

def initStrategy(env_cfg:EnvConfig, strategy:dict)->DefaultStrategy:
    if strategy is None: return DefaultStrategy(env_cfg)
    elif type(strategy) is type: return strategy()
    elif type(strategy) is dict:
        basic = strategy.get('basic', DefaultStrategy)
        early = strategy.get('early', DefaultEarly)
        game = strategy.get('game', DefaultGame)
        robot = strategy.get('robot', OptimisedRobots)
        factory = strategy.get('factory', MeanWaterStrategy)
        return basic(env_cfg, early=early(env_cfg), game=game(env_cfg, robotStrategy=robot, factoryStrategy=factory))
    else: return strategy

# ===============================================================================================================
# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
# ===============================================================================================================
class Agent():
    ''' Агент для игры '''
    strategy: DefaultStrategy = None # стратегия игры, общая (включающая в себя early и game стратегии)
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    def __init__(self, player:str, env_cfg:EnvConfig, *, strategy:dict=None) -> None:
        self.player = player
        self.opp_player = "player_1" if self.player == "player_0" else "player_0"
        self.env_cfg = env_cfg
        self.strategy = initStrategy(env_cfg, ddf)
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