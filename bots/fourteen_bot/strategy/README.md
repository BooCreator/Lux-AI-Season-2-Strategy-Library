# Оглавление
* __[Структура папки](#структура)__
* __[Общие стратегии](#общие-стратегии)__
  * [общий класс базовых стратегий](#базовая-стратегия)
* __[Стратегии ранней стадии игры](#ранняя-стадия)__
  * [базовая стратегия](#базовая-стратегия-ранней-игры)
* __[Стратегии основной стадии игры](#основная-стадия)__
  * [базовая стратегия](#базовая-стратегия-основной-стадии-игры)

# Структура

* [early](https://github.com/BooCreator/Lux-AI-Season-2-Strategy-Library/tree/main/strategy/early) - стратегии ранней игры
  * __[default.py](https://github.com/BooCreator/Lux-AI-Season-2-Strategy-Library/tree/main/strategy/early/default.py)__ - [базовая стратегия](#базовая-стратегия-ранней-игры)
* [game](https://github.com/BooCreator/Lux-AI-Season-2-Strategy-Library/tree/main/strategy/game) - стратегии основной фазы игры
  * __[default.py](https://github.com/BooCreator/Lux-AI-Season-2-Strategy-Library/tree/main/strategy/game/default.py)__ - [базовая стратегия](#базовая-стратегия-основной-стадии-игры)
* [kits](https://github.com/BooCreator/Lux-AI-Season-2-Strategy-Library/tree/main/strategy/kits) - полезные классы и функции
  * __[eyes.py]()__ - класс "Глазки", с помощью которого можно отслеживать ситуацию в игре
  * __[factory.py]()__ - класс данных фабрики. Хранит всех роботов и имеет некоторые вычислительные функции
  * __[robot.py]()__ - класс данных робота. Имеет тип, задачу ,а также некоторые вычислительные функции
  * __[utils.py]()__ - полезные функции
* __[basic.py](https://github.com/BooCreator/Lux-AI-Season-2-Strategy-Library/tree/main/strategy/basic.py)__ - [общий класс базовых стратегий](#базовая-стратегия)

# Описание стратегий

Ниже описаны общие принципы работы стратегий. В рамках библиотеки существует три типа стратегий:
* [Стратегии ранней стадии игры](#ранняя-стадия)
* [Стратегии основной стадии игры](#основная-стадия)
* [Общие стратегии](#общие-стратегии)

# Общие стратегии

__Общие стратегии__ - это стратегии, включающие в себя стратегию ранней и средней стадии игры. 
В настоящий момент реализованы следующие стратегии:
* __[Базовая стратегия](#базовая-стратегия)__

## Базовая стратегия

Базовая общая стратегия не выполняет никаких особенных действий. Она подключает базовые версии стратегий ранней и основной стадий игры и передаёт параметры им.

[>> Открыть код](https://github.com/BooCreator/Lux-AI-Season-2-Strategy-Library/tree/main/strategy/basic.py)

# Ранняя стадия

__Стратегии ранней игры__ - это стратегии, функции которых заключаются в выборе ставки и расстановке фабрик.
В настоящий момент реализованы следующие стратегии:
* __[Базовая стратегия](#базовая-стратегия-ранней-игры)__

## Базовая стратегия ранней игры

Базовая стратегий ранней игры начинает игру с 0 ставки, чтобы не тратить ресурсы.
Для установки фабрики использует алгоритм распространения и выбирает наиболее релевантные позиции возре льда.
Ресурсы по умолчанию распределяются равномерно.

[>> Открыть код](https://github.com/BooCreator/Lux-AI-Season-2-Strategy-Library/tree/main/strategy/early/default.py)

# Основная стадия

__Стратегии основной стадии игры__ - это стратегии, которые реализуют управление фабриками и роботами.
В настоящий момент реализованы следующие стратегии:
* __[Базовая стратегия](#базовая-стратегия-основной-стадии-игры)__

## Базовая стратегия основной стадии игры

Базовая стратегия основной стадии игры предполагает следующий алгоритм.
Во время всей игры мы создаём одновремеено 3 лёгких робота и 1 тяжёлого.
Каждый из роботов добывает лёд.
Если лёд далеко, то робот начинает расчищать область вокруг фабрик от щебня.
При передвижении робот учитывает энергию других роботов, если у него больше, то он давит робота.

[>> Открыть код](https://github.com/BooCreator/Lux-AI-Season-2-Strategy-Library/tree/main/strategy/game/default.py)