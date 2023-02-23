from .tools import *
from datetime import datetime
from luxai_s2.env import LuxAI_S2
import numpy as np

class LuxAI:

    title = 'lux-ai-season-2'
    env = LuxAI_S2()

    def init(download=False, use_gpu=False):
        initCompetition(use_gpu=use_gpu)
        if download: LuxAI.loadCompetition()

    def loadCompetition(rw=False):
        if not rw and os.path.exists('bots/example'): return
        file = loadCompetition(LuxAI.title)
        unzip(file, 'bots/example')
        remove(file)

    def buildSubmission(name:str):
        datename = str(datetime.now()).split('.')[0].replace(':', '-').replace(' ', '_')
        zip(f'bots/{name}/', f'submissions/{name}_{datename}')

    def sendSubmission(filename, message=''):
        os.system(f'copy submissions\\{filename} submissions\\submission.tar.gz')
        sendSubmission(LuxAI.title, 'submissions\\submission.tar.gz', message if len(message) > 0 else filename)
        remove('submissions\\submission.tar.gz')

    def play(bots:list[dict],*, v=2, s=None):
        if not os.path.exists('replays'):os.mkdir('replays')
        replay = './replays/'
        datename = str(datetime.now()).split('.')[0].replace(':', '-').replace(' ', '_')
        if len(bots) == 1: 
            os.system(f'luxai-s2 {bots[0]["file"]} {bots[0]["file"]} -v {v} -o "{replay}{bots[0]["name"]}_self_{datename}.html"'
                        + (f' -s {s}' if s is not None else ''))
        elif len(bots) > 1:
            for i in range(0, len(bots)):
                for j in range(i+1, len(bots)):
                    os.system(f'luxai-s2 {bots[i]["file"]} {bots[j]["file"]} -v {v} -o "{replay}{bots[i]["name"]}_{bots[j]["name"]}_{datename}.html"'
                        + (f' -s {s}' if s is not None else ''))
    
    def tornament(bots_path):
        full_path = '.'
        datename = str(datetime.now()).split('.')[0].replace(':', '-').replace(' ', '_')
        for folder in ['replays', 'tornament', datename]:
            full_path += '/' + folder
            if not os.path.exists(full_path): os.mkdir(full_path)
        os.system(f'luxai-s2 {bots_path} -o "{full_path}/replay.html" --tournament -v 0 --tournament_cfg.concurrent=2')

    def interact(agents, steps=1000, *, s=None):
        # сбросить нашу среду
        obs = LuxAI.env.reset(seed=s)
        np.random.seed(0)
        imgs = []
        step = 0
        # Обратите внимание, что поскольку среда состоит из двух фаз, мы также отслеживаем значение, называемое
        # `real_env_steps` в состоянии окружения. Первая фаза заканчивается, когда `real_env_steps` становится равным 0 и используется ниже.

        # повторяем до тех пор, пока не закончится фаза 1
        step = 0
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
            step += 1
            if step >= 5: step = 0
            full_path = ''
            for folder in ['log', 'render']:
                full_path += folder + '/'
                if not os.path.exists(full_path): os.mkdir(full_path)
            toImage(frame[0], f'{full_path}frame_{step}')
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
            imgs += [LuxAI.env.render("rgb_array", width=640, height=640)]
            done = dones["player_0"] and dones["player_1"]
        full_path = ''
        date = datetime.now()
        datefolder = str(date.date()).replace(':', '-')
        datename = str(date.time()).split('.')[0].replace(':', '-')
        for folder in ['replays', 'video', datefolder]:
            full_path += folder + '/'
            if not os.path.exists(full_path): os.mkdir(full_path)
        full_path += datename + f'_s_{steps}'
        return toVideo(imgs, full_path)