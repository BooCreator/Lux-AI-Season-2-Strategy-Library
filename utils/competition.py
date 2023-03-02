from .tools import *
from datetime import datetime
from luxai_s2.env import LuxAI_S2
import numpy as np

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
    def interact(agents:dict, steps:int=1000, *, seed:int=None, log:bool=True):
        ''' Запуск локальной игры между агентами '''
        # сбросить среду игры
        obs = LuxAI.env.reset(seed=seed)
        np.random.seed(0)
        log_path, imgs, step = '', [], 0
        for folder in ['log', 'render']:
            log_path += folder + '/'
            if not os.path.exists(log_path): os.mkdir(log_path)

        # Обратите внимание, что поскольку среда состоит из двух фаз, мы также отслеживаем значение, называемое
        # `real_env_steps` в состоянии окружения. Первая фаза заканчивается, когда `real_env_steps` становится равным 0 и используется ниже.
        # повторяем до тех пор, пока не закончится фаза 1
        while LuxAI.env.state.real_env_steps < 0:
            if step >= steps: break
            actions = {}
            for player in LuxAI.env.agents:
                o = obs[player]
                a = agents[player].early_setup(step, o)
                actions[player] = a
            step += 1
            obs, rewards, dones, infos = LuxAI.env.step(actions)
            frame = [LuxAI.env.render("rgb_array", width=640, height=640)]
            imgs += frame
            if log: toImage(frame[0], f'{log_path}frame', frames=LuxAI.render_log_count)
            print('\r', 'step:', step, 'of', steps, end='   ')
        
        # обработка основной фазы игры
        done = False
        while not done:
            if step >= steps: break
            actions = {}
            for player in LuxAI.env.agents:
                o = obs[player]
                a = agents[player].act(step, o)
                actions[player] = a
            step += 1
            obs, rewards, dones, infos = LuxAI.env.step(actions)
            frame = [LuxAI.env.render("rgb_array", width=640, height=640)]
            imgs += frame
            if log: toImage(frame[0], f'{log_path}frame', frames=LuxAI.render_log_count)
            done = dones["player_0"] and dones["player_1"]
            print('\r', 'step:', step, 'of', steps, end='   ')
        
        # сохраняем результаты игры
        full_path = ''
        date = datetime.now()
        datefolder = str(date.date()).replace(':', '-')
        datename = str(date.time()).split('.')[0].replace(':', '-')
        for folder in ['log', 'video', datefolder]:
            full_path += folder + '/'
            if not os.path.exists(full_path): os.mkdir(full_path)
        full_path += datename + f'_s_{seed}_e_{step}_of_{steps}'
        return toVideo(imgs, full_path)
# ===============================================================================================================
# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
# ===============================================================================================================