import numpy as np
from lux.cargo import UnitCargo
from lux.config import EnvConfig
from lux.team import Team, FactionTypes
from lux.unit import Unit
from lux.factory import Factory

from lux.kit import GameState
from lux.kit import Board

def checkType(arr):
    if type(arr) is np.ndarray: return arr
    elif type(arr) is list: return np.array(arr)
    return arr

def obs_to_game_state(step, env_cfg: EnvConfig, obs):
    
    units = dict()
    for agent in obs["units"]:
        units[agent] = dict()
        for unit_id in obs["units"][agent]:
            unit_data = obs["units"][agent][unit_id]
            unit_data['pos'] = checkType(unit_data['pos'])
            cargo = UnitCargo(**unit_data["cargo"])
            unit = Unit(
                **unit_data,
                unit_cfg=env_cfg.ROBOTS[unit_data["unit_type"]],
                env_cfg=env_cfg
            )
            unit.cargo = cargo
            units[agent][unit_id] = unit
            

    factory_occupancy_map = np.ones_like(obs["board"]["rubble"], dtype=int) * -1
    factories = dict()
    for agent in obs["factories"]:
        factories[agent] = dict()
        for unit_id in obs["factories"][agent]:
            f_data = obs["factories"][agent][unit_id]
            f_data['pos'] = checkType(f_data['pos'])
            cargo = UnitCargo(**f_data["cargo"])
            factory = Factory(
                **f_data,
                env_cfg=env_cfg
            )
            factory.cargo = cargo
            factories[agent][unit_id] = factory
            factory_occupancy_map[factory.pos_slice] = factory.strain_id
    teams = dict()
    for agent in obs["teams"]:
        team_data = obs["teams"][agent]
        faction = FactionTypes[team_data["faction"]]
        teams[agent] = Team(**team_data, agent=agent)

    return GameState(
        env_cfg=env_cfg,
        env_steps=step,
        board=Board(
            rubble  = checkType(obs["board"]["rubble"]),
            ice     = checkType(obs["board"]["ice"]),
            ore     = checkType(obs["board"]["ore"]),
            lichen  = checkType(obs["board"]["lichen"]),
            lichen_strains = checkType(obs["board"]["lichen_strains"]),
            factory_occupancy_map = checkType(factory_occupancy_map),
            factories_per_team  = checkType(obs["board"]["factories_per_team"]),
            valid_spawns_mask   = checkType(obs["board"]["valid_spawns_mask"])
        ),
        units=units,
        factories=factories,
        teams=teams
    )