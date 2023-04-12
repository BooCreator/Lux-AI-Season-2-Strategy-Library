# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
class ROBOT_TYPE:
    ''' Тип робота LIGHT - 1, HEAVY - 2 '''
    LIGHT = 1
    HEAVY = 2
    def getType(type_name:str) -> int:
        if type(type_name) is int: return type_name 
        return 1 if type_name == 'LIGHT' else 2
# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
class ROBOT_TASK:
    ''' Тип работы робота: MINER - 0, CLEANER - 1'''
    # временные - одноразовые задачи, зависящие от обстоятельств
    RETURN    = 0 # возвращается на базу
    LEAVER    = 1 # убегает от противников
    WALKER    = 2 # задача - отойти
    RECHARGE  = 3 # если не хватает энергии, чтобы сделать шаг
    # постоянные - постоянные задачи робота
    JOBLESS   = 4 # без задачи
    ORE_MINER = 5 # добывает руду
    ICE_MINER = 6 # добывает лёд
    CLEANER   = 7 # чистит щебень округ базы
    DESTROYER = 8 # уничтожает лишайник
    ENERGIZER = 9 # если не хватает энергии, чтобы сделать шаг
    # общие - задачи, которые могут как назначаться одноразово, так и быть постоянными
    WARRION   = 10 # давит противников
    def getTask(task_name:str) -> int:
        if type(task_name) is int: return task_name 
        return -1
# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =