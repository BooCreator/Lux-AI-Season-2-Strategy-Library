from utils.competition import Log, LuxAI as Lux

#Lux.loadCompetition(rw=True) # if not exists - load

bots = [
    #{'file':'./bots/example/main.py', 'name':'example'},
    #{'file':'./bots/second_bot/main.py', 'name':'second'},
    #{'file':'./bots/five_bot/main.py', 'name':'five'},
    #{'file':'./bots/six_bot/main.py', 'name':'six'},
    #{'file':'./bots/seven_bot/main.py', 'name':'seven'},
    #{'file':'./bots/eight_bot/main.py', 'name':'eight'},
    {'file':'./bots/nine_bot/main.py', 'name':'nine'},
]

#Lux.play(bots, seed=None)
#Lux.tornament('bots/')
#zip_name = Lux.buildSubmission('nine_bot') # zip_name == 'example_2023-02-09_15-38-21.tar.gz'
#Lux.sendSubmission(zip_name, 'third bot')

from test_env.agent import Agent

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

Lux.render_log_count=10
Lux.env.reset()
env_cfg = Lux.env.state.env_cfg
agents = {player: Agent(player, env_cfg, strategy=ddf) for player in Lux.env.agents}
#agents = {
#    'player_0': Agent('player_0', env_cfg, strategy={'early': OptimisedEarly, 'robot': CuriousRobots, 'factory': MeanWaterStrategy}),
#    'player_1': Agent('player_1', env_cfg, strategy={'early': DefaultEarly, 'robot': CuriousRobots, 'factory': MeanWaterStrategy})
#}
#agents = {player: Agent(player, env, game=CautiousStrategy) for player in Lux.env.agents}

#from bots.seven_bot.agent import Agent
#agents = {player: Agent(player, env) for player in Lux.env.agents}

#log = Log(video=False, frames=False, step_time=False, obs_time=False)
#Lux.interact(agents, None, 100, seed=156, log=log.getLog(), show_steps=True)