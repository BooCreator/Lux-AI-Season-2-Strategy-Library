from collections import defaultdict


meaning = defaultdict(list)
m_lvls = {}

#@time_wrapper('func_name')
def time_wrapper(title, lvl:int=2, mean:bool=True):
    def decorator(func):
        from datetime import datetime
        def wrapper(*args, **kwargs):
            time = datetime.now()
            result = func(*args, **kwargs)
            time = datetime.now() - time
            if mean: 
                meaning[title].append(time.seconds*1_000_000 + time.microseconds)
                m_lvls[title] = lvl
            elif time.microseconds > 0:
                print('-'*lvl, f'> "{title}" time:', time, '< --')
            return result
        return wrapper
    return decorator

def showMeanFuncTime(titles:str=None):
    if type(titles) is str:
        titles = [titles]
    elif titles is None or len(titles) == 0:
        titles = meaning.keys()
    for title in titles:
        if title in meaning.keys():
            print('-'*m_lvls.get(title, 2),
                  f'> mean for "{title}" time:', round(sum(meaning[title])/len(meaning[title])/1_000, 4), 'ms of', len(meaning[title]), '< --')
