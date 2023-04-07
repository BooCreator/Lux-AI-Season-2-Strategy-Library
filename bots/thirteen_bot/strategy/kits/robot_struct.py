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
    RETURN    = -2 # возвращается на базу
    JOBLESS   = -1 # без задачи
    ORE_MINER  = 0 # добывает руду
    ICE_MINER  = 1 # добывает лёд
    CLEANER    = 2 # чистит щебень округ базы
    #COURIER_IN = 3 # курьер, который забирает
    #COURIER_OUT= 4 # курьер, который отдаёт
    WARRION    = 5 # давит противников
    LEAVER     = 6 # убегает от противников
    DESTROYER  = 7 # уничтожает лишайник
    WALKER     = 8 # задача - отойти
    RECHARGE   = 9 # если не хватает энергии, чтобы сделать шаг
    def getTask(task_name:str) -> int:
        if type(task_name) is int: return task_name 
        return -1
# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =