# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
class ROBOT_TYPE:
    ''' Тип робота LIGHT - 1, HEAVY - 2 '''
    LIGHT = 1
    HEAVY = 2
    def getType(type_name:str) -> int:
        return 1 if type_name == 'LIGHT' else 2
# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =
class ROBOT_TASK:
    ''' Тип работы робота: MINER - 0, CLEANER - 1'''
    RETURN = -2
    JOBLESS = -1
    MINER   = 0
    CLEANER = 1
    COURIER = 2
    WARRION = 3
    LEAVER  = 4
    def getTask(task_name:str) -> int:
        return 0 if task_name == 'MINER' else 1
# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =