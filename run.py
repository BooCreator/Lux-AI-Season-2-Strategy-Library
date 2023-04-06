from utils.competition import Log, LuxAI as Lux
from utils.rl_pipeline import rl_interact

#Lux.loadCompetition(rw=True) # if not exists - load

bots = [
    {'file':'./bots/ten_bot/main.py', 'name':'ten'},
    {'file':'./bots/eleven_bot/main.py', 'name':'eleven'},
]

#Lux.play(bots, seed=7753391)
#Lux.tornament('bots/')
#zip_name = Lux.buildSubmission('twelve_fix_bot') # zip_name == 'example_2023-02-09_15-38-21.tar.gz'
#Lux.sendSubmission(zip_name, 'third bot')

from test_env.agent import Agent

# ----- default -----
from strategy.basic import DefaultStrategy
# ----- early -----
from strategy.early.default import EarlyStrategy as DefaultEarly
from strategy.early.from_kaggle_strategy import EarlyStrategy as OptimisedEarly
from strategy.early.best_strategy import EarlyStrategy as BestEarly
# ----- game -----
from strategy.game.default import GameStrategy as DefaultGame
from strategy.game.cautious import GameStrategy as CautiousStrategy
# ----- robot -----
from strategy.game.robot.cautious import RobotStrategy as CautiousRobots
from strategy.game.robot.curious import RobotStrategy as CuriousRobots
from strategy.game.robot.optimised import RobotStrategy as OptimisedRobots
# ----- factory -----
from strategy.game.factory.default import FactoryStrategy as DefaultFactoryStrategy
from strategy.game.factory.mean_water import FactoryStrategy as MeanWaterStrategy
from strategy.game.factory.for_best import FactoryStrategy as ForBestFactoryStrategy

ddf = {
    'basic': DefaultStrategy,
    'early': BestEarly,
    'game': DefaultGame,
    'robot': OptimisedRobots,
    'factory': ForBestFactoryStrategy
}

Lux.render_log_count=10
Lux.env.reset()
env_cfg = Lux.env.state.env_cfg
agents = {player: Agent(player, env_cfg, strategy=ddf) for player in Lux.env.agents}
#agents = {
#    'player_0': Agent('player_0', env_cfg, strategy={'early': OptimisedEarly, 'robot': CuriousRobots, 'factory': MeanWaterStrategy}),
#    'player_1': Agent('player_1', env_cfg, strategy={'early': DefaultEarly, 'robot': CuriousRobots, 'factory': MeanWaterStrategy})
#}
#agents = {player: Agent(player, env, game=CautiousStrategy) for player in Lux.env.agents}

#from bots.twelve_bot.agent import Agent as AgentTwelve
#from bots.thirteen_bot.agent import Agent as AgentThirteen
#agents = {
#    'player_0': AgentTwelve('player_0', env_cfg),
#    'player_1': AgentThirteen('player_1', env_cfg),
#}
#
log = Log(video=False, frames=True, step_time=False, obs_time=False) # 598640900
Lux.interact(agents, None, 1000, seed=6628359, log=log.getLog(), show_steps=True)


#rl_interact(f'D:\\ML\\Lux AI Season 2\\replays\\json\\{46215591}.json')