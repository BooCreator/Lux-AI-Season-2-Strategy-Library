
from strategy.kits.factory import FactoryData
from math import floor

class FactoryStrategy:
    ''' Класс для стратегии фабрик на стадии игры '''

    def getActions(self, step:int, env, game_state, **kwargs):
        ''' Получить список действий для фабрик '''
        f_data:dict[str, FactoryData] = kwargs.get('f_data')
        if f_data is None: raise Exception('f_data is not found in args')
        actions = {}
        for unit_id, item in f_data.items():
            fact_free_loc = item.getFreeLocation()
            if fact_free_loc[1][1] == 1:
                if item.factory.power >= env.ROBOTS["HEAVY"].BATTERY_CAPACITY and \
                    item.factory.cargo.metal >= env.ROBOTS["HEAVY"].METAL_COST and item.getCount(type_is='HEAVY') < 1:
                    actions[unit_id] = item.factory.build_heavy()
                    continue
                elif item.factory.power >= env.ROBOTS["LIGHT"].POWER_COST and \
                    item.factory.cargo.metal >= env.ROBOTS["LIGHT"].METAL_COST and item.getCount(type_is='LIGHT') < 3:
                    actions[unit_id] = item.factory.build_light()
                    continue
            water_on_steps = item.getMeanWaterOnStep()*(1001-step) # сколько воды можно получить до конца игры
            water_for_liches = item.factory.cargo.water-(1001-step) # сколько воды остаётся на лишайник
            water_cost_to_end = item.factory.water_cost(game_state) # минимум воды для лишайника
            if water_cost_to_end*(1000-step) < water_for_liches + water_on_steps:
                if water_cost_to_end < water_for_liches:
                    actions[unit_id] = item.factory.water()
        return actions
