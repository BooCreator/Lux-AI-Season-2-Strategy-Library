import os
import cv2
import glob
import shutil
import tarfile
import zipfile
import numpy as np
from IPython.display import Video

try:
    from utils.visualiser import Visualizer
except:
    from visualiser import Visualizer

visualizer = Visualizer(48, 48)

def unzip(filename:str, path:str='.'):
    with zipfile.ZipFile(filename, 'r') as zip_ref:
        zip_ref.extractall(path)

def zip(path:str, filename:str):
    if os.path.exists(path + '__pycache__'): 
        shutil.rmtree(path + '__pycache__')
    with tarfile.open(filename+'.tar.gz', "w:gz") as tar:
        tar.add(path, arcname=os.path.basename(path))

def loadCompetition(name:str):
    os.system(f'kaggle competitions download -c {name}')
    return name + '.zip'

def loadDataset(name:str):
    os.system(f'kaggle datasets download -d {name}')
    return name + '.zip'

def sendSubmission(competition:str, filename:str, message:str=''):
    os.system(f'kaggle competitions submit -c {competition} -f {filename} -m {message}')

def remove(filename:str):
    os.remove(filename)
    print('-- remove: ' + filename)

def clearFolder(dir:str='', ext:str='.html',*, reg=None):
    for file in glob.glob(f'{dir}/*{ext}' if reg is None else reg):
        remove(file)

def initCompetition(name:str='', use_gpu:bool=False):
    os.system(f'pip install --upgrade luxai_s2')
    if use_gpu: os.system(f'pip install juxai-s2')
    os.system(f'pip install --upgrade kaggle')
    if len(name) > 0: loadCompetition(name)
    return name + '.zip'

def cloneFolder(path:str, to:str):
    path, to = path.replace('/', '\\'), to.replace('/', '\\')
    os.system(f'xcopy {path} {to} /e /y')

def toVideo(imgs:list[np.ndarray], filename:str='_blank', *, return_:bool=False, palette=cv2.COLOR_BGR2RGB):
    # использование cv2 для создания видео
    video_name = f'{filename}.mp4'
    height, width, __ = imgs[0].shape
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    video = cv2.VideoWriter(video_name, fourcc, 10, (width,height))

    for img in imgs:
        img = cv2.cvtColor(img, palette)
        video.write(img)
    video.release()
    if return_: return Video(video_name)

def toImage(imgs:np.ndarray, filename:str='_blank', *, render:bool=False, return_:bool=False, palette=cv2.COLOR_BGR2RGB, frames:int=5):
    # использование cv2 для создания видео
    frame = imgs.copy()
    if render:
        visualizer.update_scene(frame)
        frame = visualizer._create_image_array(visualizer.surf, (480, 480))
    if frames > 0:
        while(True):
            try:
                if os.path.exists(f'{filename}_{0}.png'): os.remove(f'{filename}_{0}.png')
                break
            except: pass
        for i in range(1, frames):
            while(True):
                try:
                    if os.path.exists(f'{filename}_{i}.png'): os.rename(f'{filename}_{i}.png', f'{filename}_{i-1}.png')
                    break
                except: pass
        while(True):
            try:
                if os.path.exists(f'{filename}_{frames-1}.png'): os.remove(f'{filename}_{frames-1}.png')
                break
            except: pass
        img = cv2.cvtColor(frame, palette)
        filename = f'{filename}_{frames-1}.png' if frames > 1 else f'{filename}.png'
        cv2.imwrite(filename, img)