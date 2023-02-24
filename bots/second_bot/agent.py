from lux.utils import my_turn_to_place_factory
from lux.kit import obs_to_game_state
from lux.config import EnvConfig
import numpy as np

from strategy.basic import DefaultStrategy as Strategy

# ===============================================================================================================
# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
# ===============================================================================================================
class Agent():
    ''' Агент для игры '''
    strategy: Strategy = None # стратегия игры, общая (включающая в себя early и game стратегии)
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    def __init__(self, player: str, env_cfg: EnvConfig, *, strategy=None) -> None:
        self.player = player
        self.opp_player = "player_1" if self.player == "player_0" else "player_0"
        np.random.seed(0)
        self.env_cfg: EnvConfig = env_cfg
        self.strategy = strategy if strategy is not None else Strategy(env_cfg)
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    # ----- Фаза расстановки фабрик -----------------------------------------------------------------------------
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    def early_setup(self, step: int, obs, remainingOverageTime: int = 60):
        if step == 0:
            return dict(faction="AlphaStrike", bid=self.strategy.early.getBid())
        else:
            game_state = obs_to_game_state(step, self.env_cfg, obs)
            # если ваша очередь ставить фабрику
            if my_turn_to_place_factory(game_state.teams[self.player].place_first, step):
                self.strategy.update(game_state, self.player, step, early=True)
                factories_to_place = game_state.teams[self.player].factories_to_place
                # если фабрики есть для расстановки
                if factories_to_place > 0:
                    # определяем сколько ресурсов давать фабрике
                    metal, water = self.strategy.early.getResourcesForFactory(game_state, self.player, factories_to_place)
                    # получаем позицию для установки фабрики
                    spawn_loc = self.strategy.early.getSpawnPos(game_state, step)
                    return dict(spawn=spawn_loc, metal=metal, water=water)
            return dict()
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    # ----- Фаза игры -------------------------------------------------------------------------------------------
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    def act(self, step: int, obs, remainingOverageTime: int = 60):
        actions = dict()
        game_state = obs_to_game_state(step, self.env_cfg, obs)

        # обновляем данные стратегии
        self.strategy.update(game_state, self.player, step)

        # получаем список действий для фабрик
        for key, value in self.strategy.game.getFactoryActions(step).items():
            actions[key] = value

        # получаем список действий для роботов
        for key, value in self.strategy.game.getRobotActions(step).items():
            actions[key] = value

        return actions
# ===============================================================================================================
# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
# ===============================================================================================================