from utils.competition import LuxAI as Lux

Lux.loadCompetition() # if not exists - load

bots = [
    #{'file':'./bots/example/main.py', 'name':'example'},
    {'file':'./bots/second_bot/main.py', 'name':'second'},
]

#Lux.play(bots, s=None)
#Lux.tornament('bots/')
#Lux.buildSubmission('example')
#Lux.sendSubmission('example_2023-02-09_15-38-21.tar.gz')

#from test_env.agent import Agent
#from strategy.basic import DefaultStrategy
#
#Lux.render_log_count=10
#Lux.env.reset()
#agents = {player: Agent(player, Lux.env.state.env_cfg) for player in Lux.env.agents}
#
#Lux.interact(agents, 100, seed=41)