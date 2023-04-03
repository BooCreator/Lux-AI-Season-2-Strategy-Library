
from strategy.kits.data_controller import DataController
from strategy.kits.factory import FactoryData

from lux.kit import GameState
from lux.kit import EnvConfig

class FactoryStrategy:
    ''' Класс для стратегии фабрик на стадии игры '''

    def getActions(self, step:int, env_cfg:EnvConfig, game_state:GameState, data:DataController, **kwargs):
        ''' Получить список действий для фабрик '''
        f_data = data.getFactoryData()
        actions = {}
        for unit_id, item in f_data.items():
            item: FactoryData
            fact_free_loc = item.getFreeLocation()
            if fact_free_loc[1][1] == 1:
                if item.factory.power >= env_cfg.ROBOTS["HEAVY"].BATTERY_CAPACITY and \
                    item.factory.cargo.metal >= env_cfg.ROBOTS["HEAVY"].METAL_COST and item.getCount(type_is='HEAVY') < 1:
                    actions[unit_id] = item.factory.build_heavy()
                    continue
                elif item.factory.power >= env_cfg.ROBOTS["LIGHT"].POWER_COST and \
                    item.factory.cargo.metal >= env_cfg.ROBOTS["LIGHT"].METAL_COST and item.getCount(type_is='LIGHT') < 3:
                    actions[unit_id] = item.factory.build_light()
                    continue
            if step > 700:
                if item.factory.water_cost(game_state) <= item.factory.cargo.water-(1000-step):
                    actions[unit_id] = item.factory.water()
        return actions
