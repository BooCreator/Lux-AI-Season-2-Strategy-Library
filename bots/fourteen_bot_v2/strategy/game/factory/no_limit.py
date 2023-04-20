import numpy as np
from strategy.kits.data_controller import DataController
from strategy.kits.factory import FactoryData

from lux.kit import GameState
from lux.kit import EnvConfig

class FactoryStrategy:
    ''' Класс для стратегии фабрик на стадии игры '''

    l_ts = 300
    l_min = 7
    l_max = 100
    max_to = 700

    lichens = []
    last_water = 0

    #@time_wrapper('mean_water_getFactoryActions', 5)
    def getActions(self, step:int, env_cfg:EnvConfig, game_state:GameState, data:DataController, **kwargs):
        ''' Получить список действий для фабрик '''
        f_data = data.getFactoryData()
        actions = {}
        step -= 11
        for unit_id, item in f_data.items():
            item: FactoryData
            item.energy_cost = 0
            fact_free_loc = item.getFreeLocation()
            if fact_free_loc[1][1] == 1:
                cnt = min(max(round(step-self.max_to)/self.l_ts*self.l_max, self.l_min), self.l_max)
                if item.factory.power >= env_cfg.ROBOTS["HEAVY"].POWER_COST and \
                    item.factory.cargo.metal >= env_cfg.ROBOTS["HEAVY"].METAL_COST and item.getCount(type_is='HEAVY') < 6:
                    actions[unit_id] = item.factory.build_heavy()
                    item.energy_cost = env_cfg.ROBOTS["HEAVY"].POWER_COST
                    continue
                elif item.factory.power >= env_cfg.ROBOTS["LIGHT"].POWER_COST and \
                    item.factory.cargo.metal >= env_cfg.ROBOTS["LIGHT"].METAL_COST and item.getCount(type_is='LIGHT') < cnt:
                    actions[unit_id] = item.factory.build_light()
                    item.energy_cost = env_cfg.ROBOTS["LIGHT"].POWER_COST
                    continue
            # --- расчёт времени полива лишайника ---
            mean_water = item.getMeanWaterOnStep() # изменение воды в среднем
            water_to_end = mean_water*(1000-step) # итоговое изменение количества воды к концу игры

            water_cost = item.factory.water_cost(game_state) # нужно воды для лишайника
            mean_lichen = sum(self.lichens)/ len(self.lichens) if len(self.lichens) > 0 else 1 # коэффициент увеличения стоимости лишайника
            
            need_water = 1001-step # сколько воды нужно для фабрики
            water_for_liches = item.factory.cargo.water-need_water # сколько воды остаётся на лишайник

            if (max(water_cost, 2)*need_water)*(1-(mean_lichen-1)) < water_for_liches + water_to_end:
                if water_cost < water_for_liches:
                    actions[unit_id] = item.factory.water()
                    if self.last_water > 0:
                        if len(self.lichens) > 0:
                            self.lichens.append((self.last_water+water_cost)/self.last_water)
                        else:
                            self.lichens.append(water_cost)
                    self.last_water += water_cost
        return actions
