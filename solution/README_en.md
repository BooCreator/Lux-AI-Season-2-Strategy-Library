# Decision for X place
First of all, we are very happy to be part of such a well-developed and interesting competition, many thanks to the organizers for their support and to all the contestants who selflessly shared their knowledge and insights.

Many thanks to [@kerrit](https://www.kaggle.com/kerrit), a member of our QuData team! We are located and working in Ukraine and we want to thank everyone who now supports the people of Ukraine!

## Solution Description

The solution is a library of several strategies for different stages of the game and active units, as well as some auxiliary functions.
Each strategy is a set of rules on the basis of which the behavior of robots and factories is built.

The solution is based on the **DefaultStrategy** class from the basic.py file. It has a set of mandatory methods for implementing a full-fledged game strategy, in particular:
* *getBid(...)* - bid selection
* *getSpawnPos(...)* - select the position of the factory
* *getActions(...)* - action definitions for factories and robots

A complete strategy can be implemented in the **DefaultStrategy** class.

Next, the **DefaultStrategy** strategy is divided into two groups **Early** and **Game**.

### Early strategies

**Early** strategies are the strategies of the factory setup phase.
Each of the strategies has a set of mandatory methods for implementing the strategy for the game phase, in particular:
* *getBid(...)* - bid selection
* *getSpawnPos(...)* - select the position of the factory

In total, 6 **Early** strategies were implemented, located in the corresponding files.
* *default* - Basic strategy of the factory placement library. The position for the factory is chosen randomly based on a previously compiled weight matrix. An example of the algorithm can be viewed [here](https://docs.google.com/spreadsheets/d/e/2PACX-1vSxd6FtgHrewPwfVBQtcwuRW0I46YdhTiy38FRarN9gOhW1b9-N3miff7Gg5rfQ92cEzD_BzV99Htkc/pubhtml?gid=986897905&single=true).
* *from_kaggle_strategy* - This strategy is an extension of *default*. The strategy for calculating the weights uses algorithms from the notebook [@istinetz](https://www.kaggle.com/code/istinetz/picking-a-good-starting-location).
* *best_strategy* - This strategy is an improvement *default* in terms of position selection. The most important change was the elimination of randomness in position selection. In this strategy, the position of the factory is chosen based on the amount of rubble in the 3x3 square around the point. In addition, the coefficients of the weight matrix have been slightly changed.
* *single_strategy* - Strategy for test training of RL model. Based on *best_strategy*. A distinctive feature is that only one factory is exposed in the strategy.
* *new_from_kaggle* - Strategy using algorithms from notebook [@istinetz](https://www.kaggle.com/code/istinetz/picking-a-good-starting-location). A distinctive feature is that the ratio of the total number of cells around the factory to the "bad" (> 25) cells is used as weights.
* *next_generation* - The last and, according to tests, the best strategy implemented in the library. The strategy calculates separate weight matrices for ice and ore, and when choosing a factory position, the amount of rubble in a 7x7 square around the point is taken into account. In addition, if all the best positions adjacent to the ice are occupied, the weight matrix for ice is recalculated.

### Game strategies

**Game** strategies are the strategies of the game phase, which are divided into two groups **Factory** and **Robot**.
Each of the strategies has a set of mandatory methods for implementing the strategy for the game phase, in particular:
* *getFactoryActions(...)* - return actions for factories
* *getRobotActions(...)* - return actions for robots

#### Factory strategies

**Factory** strategies are strategies for how factories work.

In total, 6 strategies were implemented, located in the corresponding files.
* *default* - Basic strategy for factories. If resources are available, it creates 1 heavy and up to 3 light robots, and after 700 steps it starts growing lichen, reserving 1000-step water.
* *mean_water* - Improved *default* strategy. The strategy uses the average water change per step to calculate the lichen planting step.
* *for_best* - New factory strategy for *best_strategy*. The strategy creates up to 20 light robots, while the number of robots is calculated by the formula $min(max(round(step-step_{start})/l_{ts}*l_{max}, l_{min}), l_{max} )$, where $step_{start}$ - to what step should be $l_{min}$ robots, $l_{ts}$ - in how many steps the number of robots should increase to $l_{max}$. The number of heavy robots is not limited. To calculate the planting time of the lichen, the coefficient of increase in the cost of the lichen per step is also used.
* *for_best_v2* - A branch of the *for_best* strategy. Added accounting for lichen to the strategy, which we will potentially grow in $min(300, 1000-step)$ steps.
* *no_limit* - Improved *for_best* strategy. In the strategy, the threshold for light robots has been increased to 100 per factory, and the number of heavy ones is limited to 6.
* *no_limit_v2* - An offshoot of the *no_limit* strategy. Added accounting for lichen to the strategy, which we will potentially grow in $min(300, 1000-step)$ steps.

#### Robot strategies

**Robot** strategies are robot behavior strategies.
Robot strategies are the most complex among other strategies and use more auxiliary tools.

##### General information about tasks

In a general sense, the behavior of robots in strategies is determined by **task**.

**Task** is a set of algorithms for implementing robot behavior. Initially, the library had two tasks MINER (mines ice) and CLEANER (removes rubble). Later this list was expanded.

The duties of the mining robot included:
* find the position of the ice,
* build a route,
* add digging actions if the robot is on a resource,
* return to the factory if we can't dig anything else (run out of energy).

The responsibilities of the cleaning robot included:
* find the nearest rubble,
* build a route,
* add digging actions if the robot is on rubble,
* return to the factory if the energy runs out.

##### Description of strategies

To implement the algorithms of robot tasks, some auxiliary tools were used. The first of these are **Eyes**.

**Eyes** - This is a class that stores game state arrays, and also allows you to conveniently perform various operations with them.
Initially, the **Eyes** data was updated inside the **Game** strategy at every step. In later versions of the library, the **DataController** class was implemented to control the state of the game.
In total, N matrices were used in Eyes:
* *factories* - Location of enemy factories. All the cells occupied by the enemy's factory were entered in the matrix.
* *units(version 1)* - Location of allied units.
* *units(version 2)* - Location of allied units or their next turn.
* *units(version 3)* - Location of allied units or their next turn. In the case of a collision, the values are added together.
* *u_move* - Ally's possible moves. Later versions used robot type instead of 1.
* *e_move* - Possible enemy moves. Later versions used robot type instead of 1.
* *u_energy* - The energy of an ally, distributed over possible moves.
* *e_energy(version 1)* - Enemy's energy distributed over possible moves.
* *e_energy(version 2)* - Enemy's energy distributed over possible moves. In the event of a collision, the values are added together.
* *e_energy(version 3)* - Enemy's energy distributed over possible moves. In the event of a collision, the values are added together. In the position of the robot - 0.
* *e_lichen* - Enemy lichen location.

Using only **Eyes** the following 3 strategies were implemented.
* *default* - The basic strategy of the robots' behavior, the essence of which is that the robots performed only the MINER and CLEANER tasks. The robots took into account the position of the allies when building the route, thereby avoiding the collision with the allies. The task was assigned as follows: heavy robots were always MINER, light ones up to 500 steps were assigned the task MINER after 500 - CLEANER. The strategy used the Eyes matrices: *factories and units(1)*.
* *cautious* - Runaway strategy for robots. The strategy implemented a mechanism for escaping robots. The essence of the mechanism was that if the difference *e_energy(1)*-*u_energy* > 0, then we could be crushed and the robot would return to the base. The strategy used Eyes matrices: *factories, units(1), e_energy(1), u_energy*. Also, this strategy was implemented as a separate GameStrategy as an example of the fact that any convenient approach can be used when implementing the strategy.
* *curious* - Catching up strategy. This is an improved *cautious* strategy. A pursuit indicator was added to the strategists, which was responsible for how many steps the robot would pursue the enemy in order to crush. The strategy used Eyes matrices: *factories, units(2), e_energy(2), u_energy, u_move*. In addition, the u_energy and u_move matrices were individual for each robot, which eliminated some problems.

The next step was to implement the **Observer** auxiliary class, which dealt with the distribution of tasks to robots. The number of tasks has been expanded to: MINER, CLEANER, RETURN (go to base), JOBLESS (unemployed), WARRION (crushes opponents), LEAVER (runs away), RECHARGE (charges). This contributed to more flexible control of robots.

Using **Eyes** and **Observer** the following 2 strategies were implemented.
* *optimised* - Improved and optimized *curious* robot strategy for new challenges. The strategy used Eyes matrices: *factories, units(2), e_energy(2), u_energy, u_move*.
* *fixed* - Fixed version of *optimised* strategy. The RECHARGE(recharging) task was added to the strategy. The Eyes matrices were used in the strategy: *factories, units(3), e_energy(3), u_energy, u_move*.

The last auxiliary is the **TaskManager** class. The tasks of the class include a deeper indication of the tasks of the robot. On the **Observer** class, only the functions of monitoring the environment and informing that the task of the robot needs to be changed remained. In addition, new tasks were defined: WALKER (retreat if an ally is coming at us), CARRIER (removes rubble to the nearest resource), ENERGIZER (charges robots adjacent to the factory), DESTROYER (destroys enemy lichen), the MINER task is divided into ICE_MINER and ORE_MINER, and the tasks themselves were divided into permanent (ICE_MINER, CARRIER ...) and one-time (WALKER, LEAVER ...).
Permanent tasks are assigned to the robot and are redefined when the robot has run out of queue, one-time tasks are determined only when a certain event occurs (an enemy is coming at us and he will crush us (LEAVER) or an ally (WALKER), we have run out of energy (RECHARGE)).

* *next_generation* - This strategy fully implemented all the tasks of the robots, in addition, many errors were fixed. In the strategy, thanks to **TaskManager**, the number of robots on tasks was regulated, in particular, the ICE_MINER task was not assigned to three robots if there were only two ices next to us, etc. In addition, the number of ENERGIZER robots was controlled so that there were no more of them than ICE_MINER. CARRIER cleared the path to the resource only in the first 50 steps, and then went to extract the resource. For the ICE_MINER task, priority was given to heavy robots, if there were none, then light ones took their place. The amount of CLEANER was controlled. If the distance to the nearest rubble is > 14, then the robots become DESTROYER or WARRIOR if the enemy did not have lichen. In addition, the total number of MINER robots depended on the current step.


##### Auxiliary Functions

The **Path** class was implemented to search for the path of bots.
A distinctively and unexpectedly useful feature of pathfinding is the added window mode. Its essence boiled down to the fact that we are looking for a path not on the entire map, but on a cut-out area with a minimum size of 5x5. The starting point of the route and the end point were located in the corners of this area.

The picture below shows an example of a window mode:

![Example of window mode when searching for paths](https://github.com/BooCreator/Lux-AI-Season-2-Strategy-Library/blob/main/solution/window_mode.png)

## Solution Links

* You can see the complete solution code [here](https://github.com/BooCreator/Lux-AI-Season-2-Strategy-Library).
* [Here](https://github.com/BooCreator/Lux-AI-Season-2-Strategy-Library/tree/main/strategy) is the implementation of the solution strategies
* [Here](https://github.com/BooCreator/Lux-AI-Season-2-Strategy-Library/tree/main/bots) is the implementation of the latest uploaded bots
* [Here](https://github.com/BooCreator/Lux-AI-Season-2-Strategy-Library/tree/main/strategy/kits) is the implementation of all helpers and classes