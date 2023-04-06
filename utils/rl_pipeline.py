from luxai_s2 import LuxAI_S2
from lux.factory import Factory
from lux.unit import Unit

from lux.kit import GameState
from strategy.kits.eyes import Eyes

from strategy.kits.lux import obs_to_game_state
from strategy.kits.robot import RobotData
from strategy.kits.robot_struct import ROBOT_TYPE
from strategy.kits.utils import *
from utils.load_extensions import load_replay

from strategy.game.robot.optimised import RobotStrategy

def get_data(gs:GameState, pid:int):
    # фичи карты
    ice, ore, rubble, __ = getResFromState(gs)
    result = [ice, ore, rubble]
    u_lichens, e_lichens = [], []
    # фичи фабрик
    feyes = Eyes().clear(['factories', 'f_ice', 'f_ore', 'f_water', 'f_metal', 'f_energy', 'f_water_cost'])
    for factory in extended([gs.factories.get('player_0').values(), gs.factories.get('player_1').values()]):
        factory: Factory
        matrix = np.ones((3,3), dtype=int)
        feyes.update('factories',    factory.pos-1, matrix if factory.team_id == pid else -matrix)
        feyes.update('f_ice',        factory.pos, factory.cargo.ice)
        feyes.update('f_ore',        factory.pos, factory.cargo.ore)
        feyes.update('f_water',      factory.pos, factory.cargo.water)
        feyes.update('f_metal',      factory.pos, factory.cargo.metal)
        feyes.update('f_energy',     factory.pos, factory.power)
        feyes.update('f_water_cost', factory.pos, factory.water_cost(gs))
        if factory.team_id == pid:
            u_lichens.append(factory.strain_id)
        else:
            e_lichens.append(factory.strain_id)
    lichen = np.where(gs.board.lichen_strains in u_lichens, 1, 0)
    lichen = np.where(gs.board.lichen_strains in e_lichens, -1, lichen)
    result.append(lichen)

    # статические фичи роботов
    reyes = Eyes().clear(['robots', 'r_type', 'u_move', 'r_ice', 'r_ore', 'r_water', 'r_metal', 'r_energy', 'r_actions', 'r_actions_cost'])
    for unit in extended([gs.units.get('player_0').values(), gs.units.get('player_1').values()]):
        unit: Unit
        unit_type = ROBOT_TYPE.getType(unit.unit_type)
        reyes.update('robots',         unit.pos, 1 if unit.team_id == pid else -1)
        reyes.update('r_type',         unit.pos, unit.unit_type if unit.team_id == pid else -unit.unit_type)
        reyes.update('u_move',         getNextMovePos(unit), 1 if unit.team_id == pid else 0, collision=lambda a,b:a+b)
        reyes.update('r_ice',          unit.pos, unit.cargo.ice)
        reyes.update('r_ore',          unit.pos, unit.cargo.ore)
        reyes.update('r_water',        unit.pos, unit.cargo.water)
        reyes.update('r_metal',        unit.pos, unit.cargo.metal)
        reyes.update('r_energy',       unit.pos, unit.power)
        reyes.update('r_actions',      unit.pos, len(unit.action_queue))
        reyes.update('r_actions_cost', unit.pos, unit.action_queue_cost(gs))
        if unit.unit_id != pid:
            reyes.update('e_energy_cross', unit.pos, -unit.power, collision=lambda a,b: a+b)
            for [x, y] in getRad(unit.pos):
                reyes.update('e_move_cross', [x, y], unit_type, collision=lambda a,b: max(a,b))
                reyes.update('e_energy_cross', [x, y], unit.power, collision=lambda a,b: a+b)
    
    # зависимые фичи роботов
    #for unit in extended([gs.units.get('player_0').values(), gs.units.get('player_1').values()]):
    #    if unit.unit_id == pid:
    #        for [x, y] in getRad(unit.pos):
    #            reyes.update(unit.unit_id + '_move_cross', [x, y], unit_type, check_keys=False)
    #            reyes.update(unit.unit_id + '_energy_cross', [x, y], unit.power, check_keys=False)
    #        reyes.update(unit.unit_id + '_collision', [0, 0], reyes.diff([unit.unit_id + '_move_cross', 'e_move_cross']), check_keys=False)
    #        reyes.update(unit.unit_id + '_energy_collision', [0, 0], reyes.diff([unit.unit_id + '_energy_cross', 'e_energy_cross']), check_keys=False)
    #    reyes.update(unit.unit_id + '_move_map', [0, 0], getMoveMap(unit, reyes.map_size), check_keys=False)

    for eyes in [feyes, reyes]:
        for key in eyes.data.keys():
            result.append(eyes.get(key))

    return result, feyes.extend(reyes)

def get_actions(preds:dict, env_cfg:EnvConfig, gs:GameState, eyes:Eyes) -> dict:
    result = {}
    units = dict_extended([gs.units.get('player_0'), gs.units.get('player_1')])
    for unit, action in preds.items():
        result[unit] = RobotStrategy.getRLActions([RobotData(units.get(unit))], [action], env_cfg, gs, eyes.for_observer())


def rl_interact(url:str):
    ''' Запуск локальной игры между агентами '''
    env, actions = load_replay(url)
    for action in actions:
        state = env.get_state()
        if state.real_env_steps >= 0:
            gs = obs_to_game_state(state.env_steps, state.env_cfg, state.get_obs())
            features, eyes = get_data(gs, 1)
            # RL.send_features()
            # preds = RL.get_preds()
            # action[f'player_{pl}'] = get_actions(preds, state.env_cfg, gs, eyes)
        env.step(action)
        # -----