from utils.competition import LuxAI as Lux

Lux.loadCompetition() # if not exists - load

bots = [
    #{'file':'./bots/example/main.py', 'name':'example'},
    {'file':'./bots/second_bot/main.py', 'name':'second'},
    {'file':'./bots/third_bot/main.py', 'name':'third'},
]

#Lux.play(bots, seed=None)
Lux.tornament('bots/')
#zip_name = Lux.buildSubmission('example') # zip_name == 'example_2023-02-09_15-38-21.tar.gz'
#Lux.sendSubmission(zip_name)

#from test_env.agent import Agent
#from strategy.basic import DefaultStrategy
#from strategy.game.cautious import GameStrategy as CautiousStrategy
#
#Lux.render_log_count=10
#Lux.env.reset()
#env = Lux.env.state.env_cfg
#agents = {player: Agent(player, env, game=CautiousStrategy) for player in Lux.env.agents}
#
#Lux.interact(agents, 1000, seed=41)