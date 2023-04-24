from utils.competition import Log, LuxAI as Lux
#from utils.rl_pipeline import rl_interact

from test_env.agent import Agent

# ----- default -----
from strategy.basic import DefaultStrategy
# ----- early -----
from strategy.early.default import EarlyStrategy as DefaultEarly
from strategy.early.from_kaggle_strategy import EarlyStrategy as OptimisedEarly
from strategy.early.best_strategy import EarlyStrategy as BestEarly
from strategy.early.next_generation import EarlyStrategy as NextGenerationEarly
from strategy.early.new_from_kaggle import EarlyStrategy as NewFromKaggle
# ----- game -----
from strategy.game.default import GameStrategy as DefaultGame
from strategy.game.cautious import GameStrategy as CautiousStrategy
# ----- robot -----
from strategy.game.robot.cautious import RobotStrategy as CautiousRobots
from strategy.game.robot.curious import RobotStrategy as CuriousRobots
from strategy.game.robot.optimised import RobotStrategy as OptimisedRobots
from strategy.game.robot.fixed import RobotStrategy as FixedRobots
from strategy.game.robot.next_generation import RobotStrategy as NextGenerationRobots
# ----- factory -----
from strategy.game.factory.default import FactoryStrategy as DefaultFactoryStrategy
from strategy.game.factory.mean_water import FactoryStrategy as MeanWaterStrategy
from strategy.game.factory.for_best import FactoryStrategy as ForBestFactoryStrategy
from strategy.game.factory.for_best_v2 import FactoryStrategy as ForBestFactoryStrategyV2
from strategy.game.factory.no_limit import FactoryStrategy as NoLimit

#Lux.loadCompetition(rw=True) # if not exists - load

#zip_name = Lux.buildSubmission('sixteen_bot') # zip_name == 'example_2023-02-09_15-38-21.tar.gz'
#Lux.sendSubmission(zip_name, 'third bot')

ddf = {
    'basic': DefaultStrategy,
    'early': NewFromKaggle,
    'game': DefaultGame,
    'robot': NextGenerationRobots,
    'factory': NoLimit
}

Lux.render_log_count=10
log = Log(video=False, frames=True, step_time=False, obs_time=False, step_render=1, render_after=0)

bots = [ {'file':'./bots/sixteen_bot/main.py', 'name':'sixteen_bot'},]

agents = {'player_0':[Agent, ddf], 'player_1':[Agent, ddf]}

seed = 858487929 # 598640900 (плато+горы) # 990277527 (каньон) 5335240


#Lux.interact(agents, 1000, seed=seed, log=log.getLog(), show_steps=True, v=0)
Lux.play(bots, seed=seed)
#Lux.tornament('bots/')
