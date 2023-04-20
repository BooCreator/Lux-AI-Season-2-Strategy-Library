from strategy.kits.decorators import showMeanFuncTime
from .tools import *
from datetime import datetime
from luxai_s2.env import LuxAI_S2
import numpy as np


class Log:
    get_video:bool = True
    get_frames:bool = True
    mean_step_time:bool = True
    mean_obs_time:bool = True
    step_render:int = 1
    def __init__(self, video=True, frames=True, step_time=True, obs_time=True, step_render=1, render_after=0) -> None:
        self.get_video=video
        self.get_frames=frames
        self.mean_step_time=step_time
        self.mean_obs_time=obs_time
        self.step_render=step_render
        self.render_after=render_after
    
    def getLog(self)->list:
        return [self.get_video, self.get_frames, self.mean_step_time, self.mean_obs_time, self.step_render, self.render_after]


def timed(func=lambda x: 0):
    time = datetime.now()
    res = func()
    return datetime.now()-time, res

def createFolder(arr:list):
    res_path = ''
    for folder in arr:
        res_path += folder + '/'
        if not os.path.exists(res_path): os.mkdir(res_path)
    return res_path
# ===============================================================================================================
# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
# ===============================================================================================================
class LuxAI:
    render_log_count = 5      # количество сохранённых псоледних кадров игры в логе
    title = 'lux-ai-season-2' # название соревнования
    env = LuxAI_S2()          # python окружение LuxAI
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    # ----- Обновить состояние стратегии ------------------------------------------------------------------------
    # ------- Можно изменять стратегии в процессе игры ----------------------------------------------------------
    def init(download=False, use_gpu=False):
        initCompetition(use_gpu=use_gpu)
        if download: LuxAI.loadCompetition()
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    # ----- Загрузить данные соревнования -----------------------------------------------------------------------
    # ------- rw - перезаписать, rm - удалить лишние файлы ------------------------------------------------------
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    def loadCompetition(rw:bool=False, rm:bool=True):
        ''' Загрузить данные соревнования '''
        if not rw and os.path.exists('bots/example'): return
        file = loadCompetition(LuxAI.title)
        unzip(file, 'bots/example')
        cloneFolder('bots/example/lux', 'lux')
        remove(file)
        if rm:
            remove('bots/example/._lux')
            clearFolder('bots/example', ext='.ipynb')
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    # ----- Собрать архив засылки -------------------------------------------------------------------------------
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    def buildSubmission(name:str)->str:
        ''' Собрать архив засылки. Zip file to .tar.gz format '''
        datename = str(datetime.now()).split('.')[0].replace(':', '-').replace(' ', '_')
        zip(f'bots/{name}/', f'submissions/{name}_{datename}')
        return f'submissions/{name}_{datename}.tar.gz'
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    # ----- Отправить засылку -----------------------------------------------------------------------------------
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    def sendSubmission(filename:str, message:str=''):
        ''' Отправить засылку '''
        filename = filename.replace("/", "\\")
        sendSubmission(LuxAI.title, filename, message if len(message) > 0 else filename)
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    # ----- Запустить игры между ботами -------------------------------------------------------------------------
    # ------- bots - список ботов -------------------------------------------------------------------------------
    # ------- seed - генерация карты, None - каждый раз новая ---------------------------------------------------
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    def play(bots:list[dict], *, v:int=2, seed:int=None):
        ''' Запуск игры между ботами '''
        full_path = './'
        date = datetime.now()
        datefolder = str(date.date()).replace(':', '-')
        datename = str(date.time()).split('.')[0].replace(':', '-')
        for folder in ['replays', datefolder]:
            full_path += folder + '/'
            if not os.path.exists(full_path): os.mkdir(full_path)
        if len(bots) == 1: 
            os.system(f'luxai-s2 {bots[0]["file"]} {bots[0]["file"]} -v {v} -o "{full_path}{bots[0]["name"]}_self_{datename}.html"'
                        + (f' -s {seed}' if seed is not None else ''))
        elif len(bots) > 1:
            for i in range(0, len(bots)):
                for j in range(i+1, len(bots)):
                    os.system(f'luxai-s2 {bots[i]["file"]} {bots[j]["file"]} -v {v} -o "{full_path}{bots[i]["name"]}_{bots[j]["name"]}_{datename}.html"'
                        + (f' -s {seed}' if seed is not None else ''))
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    # ----- Запуск турнира между всеми ботами папки bots --------------------------------------------------------
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    def tornament(bots_path:str='bots/'):
        ''' Запуск турнира между всеми ботами папки bots '''
        full_path = '.'
        datename = str(datetime.now()).split('.')[0].replace(':', '-').replace(' ', '_')
        for folder in ['replays', 'tornament', datename]:
            full_path += '/' + folder
            if not os.path.exists(full_path): os.mkdir(full_path)
        os.system(f'luxai-s2 {bots_path} -o "{full_path}/replay.html" --tournament -v 0 --tournament_cfg.concurrent=2')
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
    # ----- Запуск локальной игры между агентами ----------------------------------------------------------------
    # ------- steps - количество шагов игры ---------------------------------------------------------------------
    # ------- seed - генерация карты, None - каждый раз новая ---------------------------------------------------
    # ------- log - сохранять ли в папку log каждый кадр игры ---------------------------------------------------
    # = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =   
    def interact(agents_data:dict, steps:int=1000, *, seed:int=None, log:list=True, show_steps:bool=True, v:int=0):
        ''' Запуск локальной игры между агентами '''
        step, imgs, mean_s, mean_o = 0, [], [], []
        log_path = createFolder(['log', 'render'])
        env = LuxAI_S2()
        np.random.seed(seed)
        obs = env.reset(seed=seed)
        env.env_cfg.verbose = v
        env_cfg = env.state.env_cfg
        agents = {}
        for player, agent in agents_data.items():
            agents[player] = agent[0](player, env_cfg, strategy=agent[1] if len(agent) > 1 else None)

        gtime = datetime.now()
        while env.state.real_env_steps < 0:
            if step >= steps: break
            actions = {}
            for player in env.agents:
                o = obs[player]
                if log==True or log[2]==True:
                    time_s, a = timed(lambda: agents[player].early_setup(step, o))
                    mean_s.append(time_s.microseconds)
                else:
                    a = agents[player].early_setup(step, o)
                actions[player] = a
            if log==True or log[3]==True:
                time_o, (obs, rewards, dones, infos) = timed(lambda: env.step(actions))
                mean_o.append(time_o.microseconds)
            else:
                obs, rewards, dones, infos = env.step(actions)
            if log==True or log[0]==True or log[1]==True:
                if (log[0] == True or step % log[4] == 0) and log[5] >= step:
                    frame = env.render("rgb_array", width=640, height=640)
                    imgs += [frame]
                    if log[1]: toImage(frame, f'{log_path}frame', frames=min(steps, LuxAI.render_log_count))
            step += 1
            print_str = f'\r step: {step} of {steps} '
            if log==True or log[2]:
                print_str += f'time_s: {time_s} mean_s: {round(sum(mean_s)/len(mean_s)/1_000_000, 4)} s '
            if log==True or log[3]:
                print_str += f'time_o: {time_o} mean_o: {round(sum(mean_o)/len(mean_o)/1_000_000, 4)} s '
            if show_steps: print(print_str, end='   ')
        
        # обработка основной фазы игры
        while True:
            if step >= steps: break
            actions = {}
            for player in env.agents:
                o = obs[player]
                if log==True or log[2]==True:
                    time_s, a = timed(lambda: agents[player].act(step, o))
                    mean_s.append(time_s.microseconds)
                else:
                    a = agents[player].act(step, o)
                actions[player] = a
            if log==True or log[3]==True:
                time_o, (obs, rewards, dones, infos) = timed(lambda: env.step(actions))
                mean_o.append(time_o.microseconds)
            else:
                obs, rewards, dones, infos = env.step(actions)
            if log==True or log[0]==True or log[1]==True:
                if (log[0] == True or step % log[4] == 0) and log[5] >= step:
                    frame = env.render("rgb_array", width=640, height=640)
                    imgs += [frame]
                    if log[1]: toImage(frame, f'{log_path}frame', frames=min(steps, LuxAI.render_log_count))
            step += 1
            print_str = f'\r step: {step} of {steps} '
            if log==True or log[2]:
                print_str += f'time_s: {time_s} mean_s: {round(sum(mean_s)/len(mean_s)/1_000_000, 4)} s '
            if log==True or log[3]:
                print_str += f'time_o: {time_o} mean_o: {round(sum(mean_o)/len(mean_o)/1_000_000, 4)} s '
            if show_steps: print(print_str, end='   ')
            if dones["player_0"] and dones["player_1"]: break

        print('\r\n session time:', datetime.now()-gtime)
        showMeanFuncTime()

        if log==True or log[0]==True:
            date = datetime.now()
            datefolder = str(date.date()).replace(':', '-')
            datename = str(date.time()).split('.')[0].replace(':', '-')
            full_path = createFolder(['log', 'video', datefolder])
            full_path += datename + f'_s_{seed}_e_{step}_of_{steps}'
            return toVideo(imgs, full_path)
# ===============================================================================================================
# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
# ===============================================================================================================