from utils.competition import LuxAI as Lux

#Lux.loadCompetition() # if not exists - load

bots = [
    #{'file':'./bots/example/main.py', 'name':'example'},
    #{'file':'./bots/second_bot/main.py', 'name':'second'},
    {'file':'./bots/third_bot/main.py', 'name':'third'},
]

#Lux.play(bots, seed=None)
Lux.tornament('bots/')
#zip_name = Lux.buildSubmission('fourth_bot') # zip_name == 'example_2023-02-09_15-38-21.tar.gz'
#Lux.sendSubmission(zip_name, 'third bot')

#from test_env.agent import Agent
#from strategy.basic import DefaultStrategy
#from strategy.game.default import GameStrategy
#
#from strategy.game.robot.cautious import RobotStrategy as CautiousRobots
#from strategy.game.factory.mean_water import FactoryStrategy as MeanWaterStrategy
#from strategy.game.cautious import GameStrategy as CautiousStrategy


#Lux.render_log_count=10
#Lux.env.reset()
#env = Lux.env.state.env_cfg
##agents = {player: Agent(player, env, game=GameStrategy(env, robotStrategy=CautiousRobots)) for player in Lux.env.agents}
#agents = {
#    'player_0': Agent('player_0', env, game=GameStrategy(env, robotStrategy=CautiousRobots)),
#    'player_1': Agent('player_1', env, game=GameStrategy(env, robotStrategy=CautiousRobots))
#}
##agents = {player: Agent(player, env, game=CautiousStrategy) for player in Lux.env.agents}
#
#Lux.interact(agents, 1000, seed=541)