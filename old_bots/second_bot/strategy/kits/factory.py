import numpy as np
from strategy.kits.utils import *
from strategy.kits.robot import RobotData

class FactoryData:
    ''' Класс данных фабрики '''
    factory = None
    robots: dict[str, RobotData] = []
    alive = False

    def __init__(self, factory) -> None:
        self.factory = factory
        self.robots = dict[str, RobotData]()
        self.alive = True

    def getRobotsOnType(self, robot_type: int = 0) -> int:
        result = []
        if type(robot_type) is str: robot_type = RobotData.TYPE.getType(robot_type)
        for unit in self.robots.values():
            if unit.robot_type == robot_type: result.append(unit)
        return result

    def getRobotstOnTask(self, robot_task: int = 0) -> int:
        result = []
        if type(robot_task) is str: robot_task = RobotData.TASK.getTask(robot_task)
        for unit in self.robots.values():
            if unit.robot_task == robot_task: result.append(unit)
        return result

    def getCountOnType(self, robot_type: int = 0) -> int:
        n = 0
        if type(robot_type) is str: robot_type = RobotData.TYPE.getType(robot_type)
        for unit in self.robots.values():
            if unit.robot_type == robot_type: n += 1
        return n

    def getCountOnTask(self, robot_task: int = 0) -> int:
        n = 0
        if type(robot_task) is str: robot_task = RobotData.TASK.getTask(robot_task)
        for unit in self.robots.values():
            if unit.robot_task == robot_task: n += 1
        return n

    def getFreeLocation(self):
        matrix = np.ones((3,3), dtype=int)
        for unit in self.robots.values():
            loc = unit.robot.pos - self.factory.pos
            if loc[0] > -2 and loc[1] > -2 and loc[0] < 2 and loc[1] < 2:
                matrix[loc[0]+1, loc[1]+1] = 0
        return matrix
    
    def getNeareastPoint(self, point: np.ndarray) -> np.ndarray:
        minX, minY = self.factory.pos[0], self.factory.pos[1]
        min = abs(point[0]-minX) + abs(point[1]-minY)
        x, y = getRect(minX, minY, 1)
        for x, y in zip(x, y):
            if abs(point[0]-x) + abs(point[1]-y) < min:
                minX, minY = x, y
        return np.array([minX, minY])