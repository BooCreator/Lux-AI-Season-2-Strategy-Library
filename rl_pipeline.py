from collections import defaultdict
from luxai_s2 import LuxAI_S2
from lux.factory import Factory
from lux.unit import Unit

from lux.kit import GameState
from strategy.kits.eyes import Eyes

from strategy.kits.lux import obs_to_game_state
from strategy.kits.robot import RobotData
from strategy.kits.factory import FactoryData
from strategy.kits.robot_struct import ROBOT_TYPE
from strategy.kits.robot_struct import ROBOT_TASK
from strategy.kits.utils import *
from utils.competition import createFolder
from utils.load_extensions import load_replay

from strategy.game.robot.optimised import RobotStrategy
from utils.tools import toImage

# reset() -> features
# step(actions(48x48x2)) -> features, reward, term:bool
# 

# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
# ----- Генерация фич ---------------------------------------------------------------------------------------
# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
def getFeatures(gs:GameState, pid:int, sample:bool=False):
    ''' Генерация фич '''
    # фичи карты
    ice, ore, rubble, __ = getResFromState(gs)
    result = [ice]#, ore, rubble]
    u_lichens, e_lichens = [], []
    # фичи фабрик
    feyes = Eyes()
    for factory in extended([gs.factories.get('player_0').values(), gs.factories.get('player_1').values()]):
        factory: Factory
        matrix = np.ones((3,3), dtype=int)
        feyes.update('factories',    factory.pos-1, matrix if factory.team_id == pid else -matrix, check_keys=False)
        feyes.update('f_ice',        factory.pos, factory.cargo.ice, check_keys=False)
        feyes.update('f_water',      factory.pos, factory.cargo.water, check_keys=False)
        if not sample:
            feyes.update('f_ore',        factory.pos, factory.cargo.ore, check_keys=False)
            feyes.update('f_metal',      factory.pos, factory.cargo.metal, check_keys=False)
            feyes.update('f_energy',     factory.pos, factory.power, check_keys=False)
            feyes.update('f_water_cost', factory.pos, factory.water_cost(gs), check_keys=False)
            if factory.team_id == pid:
                u_lichens.append(factory.strain_id)
            else:
                e_lichens.append(factory.strain_id)
    if not sample:
        lichen = np.ones((48, 48), dtype=int)
        for id in u_lichens:
            lichen = np.where(gs.board.lichen_strains == id, 1, lichen)
        for id in e_lichens:
            lichen = np.where(gs.board.lichen_strains == id, -1, lichen)
        result.append(lichen)

    # статические фичи роботов
    reyes = Eyes()
    for unit in extended([gs.units.get('player_0').values(), gs.units.get('player_1').values()]):
        unit: Unit
        unit_type = ROBOT_TYPE.getType(unit.unit_type)
        reyes.update('robots',         unit.pos, 1 if unit.team_id == pid else -1, check_keys=False)
        reyes.update('u_move',         getNextMovePos(unit), 1 if unit.team_id == pid else 0, collision=lambda a,b:a+b, check_keys=False)
        reyes.update('r_ice',          unit.pos, unit.cargo.ice, check_keys=False)
        reyes.update('r_energy',       unit.pos, unit.power, check_keys=False)
        reyes.update('r_actions',      unit.pos, len(unit.action_queue), check_keys=False)
        reyes.update('r_actions_cost', unit.pos, unit.action_queue_cost(gs), check_keys=False)
        if not sample:
            reyes.update('r_type',         unit.pos, unit.unit_type if unit.team_id == pid else -unit.unit_type, check_keys=False)
            reyes.update('r_ore',          unit.pos, unit.cargo.ore, check_keys=False)
            reyes.update('r_water',        unit.pos, unit.cargo.water, check_keys=False)
            reyes.update('r_metal',        unit.pos, unit.cargo.metal, check_keys=False)
            if unit.unit_id != pid:
                reyes.update('e_energy_cross', unit.pos, -unit.power, collision=lambda a,b: a+b, check_keys=False)
                for [x, y] in getRad(unit.pos):
                    reyes.update('e_move_cross', [x, y], unit_type, collision=lambda a,b: max(a,b), check_keys=False)
                    reyes.update('e_energy_cross', [x, y], unit.power, collision=lambda a,b: a+b, check_keys=False)

    for eyes in [feyes, reyes]:
        for key in eyes.data.keys():
            result.append(eyes.get(key))

    return result, feyes.extend(reyes)
# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
# ----- Генерация базово набора действий для теста ----------------------------------------------------------
# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
def genActions(gs:GameState, pid:int):
    ''' Генерация базово набора действий для теста '''
    player = f'player_{pid}'
    result = np.zeros((48, 48, 2), dtype=int)
    for __, unit in gs.units.get(player).items():
        result[unit.pos[0], unit.pos[1]][1] = 1
    return result


class move_to:
    ''' Направления движения роботов '''
    center = 0
    up     = 1
    right  = 2
    down   = 3
    left   = 4
# ===============================================================================================================
# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
# ===============================================================================================================
class LuxRL:
    ''' Класс для RL '''
    env  = LuxAI_S2() # python окружение LuxAI
    pid  = 0          # id игрока
    feat: np.ndarray = None
    eyes: Eyes = None
    gs: GameState = None
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    # ----- Agent - класс агента для расстановки фабрик ---------------------------------------------------------
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    def __init__(self, Agent) -> None:
        ''' * Agent - класс агента для расстановки фабрик '''
        self.eyes = Eyes()
        self.feat = None
        self.env.reset()
        self.gs = None
        self.agents = {player: Agent(player, self.env.state.env_cfg) for player in self.env.agents}
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    # ----- Фаза расстановки фабрик -----------------------------------------------------------------------------
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    def factoryPlace(self, log:bool=False) -> int:
        ''' Фаза расстановки фабрик '''
        step = 0
        while self.env.state.real_env_steps < 0:
            actions = {}
            for player in self.env.agents:
                o = self.obs[player]
                a = self.agents[player].early_setup(step, o)
                actions[player] = a
            self.obs = self.env.step(actions)[0]
            step += 1
        if log:
            log_path = createFolder(['log', 'render'])
            frame = self.env.render("rgb_array", width=640, height=640)
            toImage(frame, f'{log_path}frame', frames=1)
        return step
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    # ----- Передвижение роботов по умолчанию -------------------------------------------------------------------
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    def getMoves(self, unit:Unit, n:int, max:int=1):
        ''' Передвижение роботов по умолчанию '''
        if max <= 5:
            if n == 0:
                return [unit.move(move_to.up)]
            elif n == 1:
                return [unit.move(move_to.down)]
            elif n == 2:
                return [unit.move(move_to.left)]
            elif n == 3:
                return [unit.move(move_to.right)]
            elif n == 4:
                return [unit.move(move_to.center)]
        elif max-(5+n) > 0:
            if n == 0:
                return [unit.move(move_to.up), unit.move(move_to.left)]
            elif n == 1:
                return [unit.move(move_to.down), unit.move(move_to.right)]
            elif n == 2:
                return [unit.move(move_to.up), unit.move(move_to.right)]
            elif n == 3:
                return [unit.move(move_to.down), unit.move(move_to.left)]
        else:
            return self.getMoves(unit, (5+n)-max, max-5)
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    # ----- Сбросить среду --------------------------------------------------------------------------------------
    # ----- n_robots кличество создаваемых роботов (min - 0, max - 9) -------------------------------------------
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    def reset(self, seed:int=None, n_robots:int=3, log:bool=False) -> np.ndarray:
        ''' Сбросить среду
            * n_robots кличество создаваемых роботов (min - 0, max - 9) '''
        self.obs = self.env.reset(seed=seed)
        n_robots = max(0, min(n_robots, 9))
        np.random.seed(0)
        player = f'player_{self.pid}'
        step = self.factoryPlace(log)
        robots = []
        for __ in range(n_robots):
            actions = defaultdict(dict)
            gs = obs_to_game_state(step, self.env.env_cfg, self.obs[player])
            for fid, factory in gs.factories.get(player).items():
                actions[player][fid] = factory.build_light()
            if n_robots > 1:
                for n, (uid, unit) in enumerate(gs.units.get(player).items()):
                    if uid not in robots:
                        actions[player][uid] = self.getMoves(unit, n, n_robots)
                        robots.append(uid)
            self.obs = self.env.step(actions)[0]
            step += 1
        self.gs = obs_to_game_state(step, self.env.env_cfg, self.obs[player])
        self.features, self.eyes = getFeatures(gs, self.pid, True)
        if log:
            log_path = createFolder(['log', 'render'])
            frame = self.env.render("rgb_array", width=640, height=640)
            toImage(frame, f'{log_path}frame', frames=1)
        return self.features
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    # ----- Выполнить шаг ---------------------------------------------------------------------------------------
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    def step(self, preds: np.ndarray, log:bool=False):
        ''' Выполнить шаг '''
        actions = {}
        player = f'player_{self.pid}'
        actions[player] = self.toActions(preds)
        self.obs, __, dones, __ = self.env.step(actions)
        self.gs = obs_to_game_state(self.env.env_steps, self.env.env_cfg, self.obs[player])
        reward = self.calcReward(dones)
        self.features, self.eyes = getFeatures(self.gs, self.pid, True)
        if log:
            log_path = createFolder(['log', 'render'])
            frame = self.env.render("rgb_array", width=640, height=640)
            toImage(frame, f'{log_path}frame', frames=1)
        return self.features, reward, (dones["player_0"] and dones["player_1"])
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    # ----- Преобразовать предикт в действия --------------------------------------------------------------------
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    def toActions(self, preds:np.ndarray) -> dict:
        ''' Преобразовать предикт в действия '''
        result = {}
        player = f'player_{self.pid}'
        tiles, units = [], []
        for factory in self.gs.factories.get(player).values():
            tiles.append(factory.pos)
            units.append(factory)
        for uid, unit in self.gs.units.get(player).items():
            actions = np.argwhere(preds[unit.pos[0], unit.pos[1]]==1)
            if len(actions > 0):
                robot = RobotData(unit)
                factory = findClosestFactory(unit.pos, tiles, units)
                robot.factory = FactoryData(factory)
                result = dict_extended([result, RobotStrategy.getRLActions([robot], actions[0], self.env.env_cfg, self.gs, self.eyes.for_observer())])
        return result
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    # ----- Считать награду -------------------------------------------------------------------------------------
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    def calcReward(self, dones) -> int:
        ''' Считать награду '''
        reward = 0
        player = f'player_{self.pid}'
        if not dones[player]: reward -= 100
        else: reward += 100
        return reward
# ===============================================================================================================
# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
# ===============================================================================================================


from test_env.rl_agent import Agent as RLAgent

lux_rl = LuxRL(RLAgent)
lux_rl.reset(7998038, log=True)
lux_rl.step(genActions(lux_rl.gs, lux_rl.pid))
for step in range(10):
    lux_rl.step(np.zeros((48, 48, 2), dtype=int), log=True)