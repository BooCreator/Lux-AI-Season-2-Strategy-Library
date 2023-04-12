from utils.competition import Log, LuxAI as Lux
#from utils.rl_pipeline import rl_interact

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
from strategy.game.robot.fixed import RobotStrategy as FixedRobots
from strategy.game.robot.next_generation import RobotStrategy as NextGenerationRobots
# ----- factory -----
from strategy.game.factory.default import FactoryStrategy as DefaultFactoryStrategy
from strategy.game.factory.mean_water import FactoryStrategy as MeanWaterStrategy
from strategy.game.factory.for_best import FactoryStrategy as ForBestFactoryStrategy

#Lux.loadCompetition(rw=True) # if not exists - load

#zip_name = Lux.buildSubmission('thirteen_bot') # zip_name == 'example_2023-02-09_15-38-21.tar.gz'
#Lux.sendSubmission(zip_name, 'third bot')

ddf = {
    'basic': DefaultStrategy,
    'early': BestEarly,
    'game': DefaultGame,
    'robot': NextGenerationRobots,
    'factory': ForBestFactoryStrategy
}

Lux.render_log_count=10
log = Log(video=False, frames=False, step_time=False, obs_time=False, step_render=1) 

bots = [ {'file':'./bots/fourteen_bot/main.py', 'name':'fourteen_bot'},]

agents = {'player_0':[Agent, ddf], 'player_1':[Agent, ddf]}

seed = 990277527 # 598640900 (плато+горы) # 990277527 (каньон)


#Lux.interact(agents, 1000, seed=seed, log=log.getLog(), show_steps=True, v=2)
Lux.play(bots, seed=seed)
#Lux.tornament('bots/')