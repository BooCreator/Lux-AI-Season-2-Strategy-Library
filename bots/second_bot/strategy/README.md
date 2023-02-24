# Стратегии #
strategy.py

## Общий класс стратегии ##
strategy.DefaultStrategy {
    early: EarlyStrategy - класс стратегии ранней стадии игры (расстановка баз)
    game:  GameStrategy  - класс стратегии основной стадии игры

    def __init__  (self, env_cfg, early:EarlyStrategy=None, game:GameStrategy=None) {
        ''' Инициализация класса стратегии. Вызывается при инициализации игры '''
        env_cfg              - класс окружения игры Lux. Можно посмотреть в файле Lux.config
        early: EarlyStrategy - класс стратегии ранней стадии игры (расстановка баз)
        game: GameStrategy   - класс стратегии основной стадии игры
    }

    def update (self, game_state, player:str, step:int, early:bool=False) {
        ''' Функция, вызываемая на каждом шаге игры '''
        game_state - файл состояния игры Lux, можно посмотреть в файле Lux.kit
        player     - имя игрока 'player_0' или 'player_1'
        step       - текущий шаг игры
        early      - показываем, что идёт ранняя стадия игры
    }
}

## Класс стратегии ранней игры. Можно реализовать свой ##
strategy.EarlyStrategy {
    spreadRubble: int   - уровень распространения для щебня.
    spreadResource: int - уровень распространения для ресурсов.
    factory_size: typle[int, int] - размер фабрики 3х3
    
    def getBid(self) -> int {
        ''' Получить ставку для выбора позиции. Если ставка N > 0, то мы хотим быть первыми, N < 0 - вторыми. '''
        ''' Если наша ставка выигрывает, то мы теряем N ресурсов. Функция вызывается на шаге 0 '''
    }

    def update(self, game_state, player:str, step:int) {
        ''' Функция обновления состояний стратегии. Вызывается на каждом шаге из основного файла стратегий. '''
        game_state - файл состояния игры Lux, можно посмотреть в файле Lux.kit
        player     - имя игрока 'player_0' или 'player_1'
        step       - текущий шаг игры
    }

    def getSpawnPos(self, game_state, step:int) -> np.ndarray[x, y] {
        ''' Функция вычисления позиции для установки фабрики. '''
        ''' Функция вызывается при каждом нашем шаге установки фабрики '''
        game_state - файл состояния игры Lux, можно посмотреть в файле Lux.kit. Из него можно получить различные карты ресурсов
        step       - текущий шаг игры
    }

    getResourcesForFactory(self, game_state, player:str, n_factories:int) -> tuple[int, int] (metal, water) {
        ''' Функция указания, сколько ресурсов нужно дать текущей устанавливаемой фабрике. '''
        ''' Функция вызывается после определения позиции фабрики, чтобы дать ей ресурсы.  '''
        game_state - файл состояния игры Lux, можно посмотреть в файле Lux.kit
        player     - имя игрока. Нужно чтобы получить из game_state наше количество оставшихся ресурсов
        n_factories - сколько фабрик у нас ещё осталось установить, без учёта текущей 
    }
}


## Класс стратегии основной стадии игры. Можно реализовать свой ##
strategy.GameStrategy {
    f_data:dict[str, f_data]    - внутренняя память класса о фабриках и их роботах
    free_robots: list[str]      - свободные роботы (без фабрики)
    eyes: dict[str, np.ndarray] - глазки. Матрицы с расположением динамических объектов (фабрики, роботы, свободные ресурсы)
    game_state - файл состояния игры Lux, можно посмотреть в файле Lux.kit
    env        - класс окружения игры Lux. Можно посмотреть в файле Lux.config
    step       - текущий шаг игры

    def __init__(self, env) {
        env - класс окружения игры Lux. Можно посмотреть в файле Lux.config
    }

    def update(self, game_state, player:str, step:int) {
        ''' Функция обновления состояний стратегии. Вызывается на каждом шаге из основного файла стратегий. '''
        ''' В базовой реализации мы проверяем наличие всех фабрик, роботов. Привязываес свободных роботов к ближайшим фабрикам, работаем глазками. '''
        game_state - файл состояния игры Lux, можно посмотреть в файле Lux.kit
        player     - имя игрока 'player_0' или 'player_1'
        step       - текущий шаг игры
    }

    def checkFactories(self, factories) {
        ''' Проверяем что у нас нет уничтоженных фабрик '''
        ''' Если такие есть, то удаляем из основного массива и делаем ей роботов свободными '''
        factories - массив фабрик из game_state для игрока
    }

    def checkRobots(self, robots:dict[str]) {
        ''' Проверяем роботов. Удалённых - удаляем из данных фабрик, только созданных - добавляем в массив свободных '''
    }

    def getFactoryInfo(self) -> tuple[list[list],list] {
        ''' Получить информацию о фабриках. Нужно для некоторых функций. '''
        ''' Возвращает два массива - factory_tiles - позиции фабрик, factory_units - классы фабрик '''
    }

    def look(self, game_state, player: str) {
        ''' Функция работы глазками. Смотрим все данных карты и обновляем матрицы. '''
        ''' 'factories' - расположение всех фабрик '''
        ''' 'units' - расположение роботов игрока '''
        ''' 'enemy' - расположение роботов соперника'''
        ''' 'u_energy' - распределение энергии роботов игрока по возможным шагам'''
        ''' 'e_energy' - распределение энергии роботов соперника по возможным шагам'''
        ''' 'free_resources' - расположение всех не занятых ресурсов. Чтобы не ходить к ближайшему занятому '''
        game_state - файл состояния игры Lux, можно посмотреть в файле Lux.kit
        player     - имя игрока 'player_0' или 'player_1'
    }

    def getFactoryActions(self, step:int) -> dict {
        ''' Составить список действий для фабрик {'factory_0': 1, ...} '''
        ''' Функция вызывается во время основной стадии игры '''
        step       - текущий шаг игры
    }

    def getRobotActions(self, step:int) -> dict {
        ''' Составить список действий для роботов {'unit_1': [0, 0, 0, 4, 0, 1], ...} '''
        ''' Функция вызывается во время основной стадии игры '''
        step       - текущий шаг игры
    }
}