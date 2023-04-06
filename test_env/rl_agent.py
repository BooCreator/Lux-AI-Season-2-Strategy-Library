from lux.utils import my_turn_to_place_factory
from strategy.kits.lux import obs_to_game_state
from lux.config import EnvConfig
import numpy as np

# ----- early -----
from strategy.early.single_strategy import EarlyStrategy as SingleEarly

# ===============================================================================================================
# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
# ===============================================================================================================
class Agent():
    ''' Агент для игры '''
    strategy = None # стратегия игры, общая (включающая в себя early и game стратегии)
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    #@time_wrapper('agent_init', 1)
    def __init__(self, player:str, env_cfg:EnvConfig, *, strategy:dict=None) -> None:
        self.player = player
        self.opp_player = "player_1" if self.player == "player_0" else "player_0"
        self.env_cfg = env_cfg
        self.strategy = SingleEarly(self.env_cfg)
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
                self.strategy.update(game_state, step)
                return self.strategy.getSpawnPos()
            return dict()
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    # ----- Фаза игры -------------------------------------------------------------------------------------------
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    def act(self, step: int, obs, remainingOverageTime: int = 60):
        return {}
# ===============================================================================================================
# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
# ===============================================================================================================