import numpy as np
from math import floor

class RobotData:
    ''' Класс данных робота '''

    class TYPE:
        ''' Тип робота LIGHT - 0, HEAVY - 1 '''
        LIGHT = 0
        HEAVY = 1

        def getType(type_name:str) -> int:
            return 0 if type_name == 'LIGHT' else 1

    class TASK:
        ''' Тип работы робота: MINER - 0, CLEANER - 1'''
        JOBLESS = -1
        MINER = 0
        CLEANER = 1
        # COURIER = 2
        # WARRION = 3

        def getTask(task_name:str) -> int:
            return 0 if task_name == 'MINER' else 1

    robot = None
    robot_type: TYPE = -1
    robot_task: TASK = -1
    min_task: int = 0 # сколько раз, минимально, нужно выполнить task
    
    def __init__(self, robot) -> None:
        self.robot = robot
        self.robot_type = RobotData.TYPE.getType(robot.unit_type)
        self.robot_task = RobotData.TASK.JOBLESS

    def on_position(self, pos:np.ndarray,*, size:int=1) -> bool:
        size = floor(size/2) + 1
        loc = self.robot.pos - pos
        return True if loc[0] > -size and loc[1] > -size and loc[0] < size and loc[1] < size else False