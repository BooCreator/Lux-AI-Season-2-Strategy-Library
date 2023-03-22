#@time_wrapper('func_name')
def time_wrapper(title):
    def decorator(func):
        from datetime import datetime
        def wrapper(*args, **kwargs):
            time = datetime.now()
            result = func(*args, **kwargs)
            time = datetime.now() - time
            print(f'--> "{title}" time:', time, '<--')
            return result
        return wrapper
    return decorator


