from strategy.kits.data_controller import DataController
from strategy.kits.factory import FactoryData

from lux.kit import GameState
from lux.kit import EnvConfig

class FactoryStrategy:
    ''' Класс для стратегии фабрик на стадии игры '''

    l_ts = 1000
    l_min = 10
    l_max = 20
    max_to = 500

    #@time_wrapper('mean_water_getFactoryActions', 5)
    def getActions(self, step:int, env_cfg:EnvConfig, game_state:GameState, data:DataController, **kwargs):
        ''' Получить список действий для фабрик '''
        f_data = data.getFactoryData()
        actions = {}
        for unit_id, item in f_data.items():
            item: FactoryData
            item.energy_cost = 0
            fact_free_loc = item.getFreeLocation()
            if fact_free_loc[1][1] == 1:
                #cnt = min(round(self.l_ts+self.max_to-step)/self.l_ts*self.l_max, self.l_max)
                cnt = min(max(round(step-self.max_to)/self.l_ts*self.l_max, self.l_min), self.l_max)
                if item.factory.power >= env_cfg.ROBOTS["HEAVY"].POWER_COST and \
                    item.factory.cargo.metal >= env_cfg.ROBOTS["HEAVY"].METAL_COST:
                    actions[unit_id] = item.factory.build_heavy()
                    item.energy_cost = env_cfg.ROBOTS["HEAVY"].POWER_COST
                    continue
                elif item.factory.power >= env_cfg.ROBOTS["LIGHT"].POWER_COST and \
                    item.factory.cargo.metal >= env_cfg.ROBOTS["LIGHT"].METAL_COST and item.getCount(type_is='LIGHT') < cnt:
                    actions[unit_id] = item.factory.build_light()
                    item.energy_cost = env_cfg.ROBOTS["LIGHT"].POWER_COST
                    continue
            water_on_steps = item.getMeanWaterOnStep()*(1000-step) # сколько воды можно получить до конца игры
            water_for_liches = item.factory.cargo.water-(1001-step) # сколько воды остаётся на лишайник
            water_cost_to_end = max(item.factory.water_cost(game_state), 2) # минимум воды для лишайника
            if water_cost_to_end*(1001-step) < water_for_liches + water_on_steps:
                if water_cost_to_end < water_for_liches:
                    actions[unit_id] = item.factory.water()
        return actions
