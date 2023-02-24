# Оглавление
1. [Структура окружения](#структура-окружения)

# Структура

* [early](https://github.com/BooCreator/Lux-AI-Season-2-Strategy-Library/tree/main/strategy/early) - стратегии ранней игры
  * __[default.py](https://github.com/BooCreator/Lux-AI-Season-2-Strategy-Library/tree/main/strategy/early/default.py)__ - базовая стратегия
* [game](https://github.com/BooCreator/Lux-AI-Season-2-Strategy-Library/tree/main/strategy/game) - стратегии основной фазы игры
  * __[default.py](https://github.com/BooCreator/Lux-AI-Season-2-Strategy-Library/tree/main/strategy/game/default.py)__ - базовая стратегия
* [kits](https://github.com/BooCreator/Lux-AI-Season-2-Strategy-Library/tree/main/strategy/kits) - полезные классы и функции
  * [eyes.py]() - 
  * [factory.py]() - 
  * [robot.py]() - 
  * [utils.py]() - 
* __[basic.py]__(https://github.com/BooCreator/Lux-AI-Season-2-Strategy-Library/tree/main/strategy/basic.py) - общий класс стратегий


# Как собирать ботов?

1. Создаём папку бота внутри bots
2. Копируем файлы __agent.py__ и __main.py__ из папки _test_env_ в папку с ботов
3. Копируем папку _lux_ в папку с ботом
4. Копируем папку _strategy_ в папку с ботом
5. В файле __agent.py__ заменяем _DefaultStrategy_ на Ваш класс стратегии