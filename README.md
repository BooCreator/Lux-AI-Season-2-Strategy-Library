# Оглавление
1. [Структура окружения](#структура-окружения)
2. [Как собирать ботов](#как-собирать-ботов)

# Структура окружения

* [bots](https://github.com/BooCreator/Lux-AI-Season-2-Strategy-Library/tree/main/bots) - боты проекта
  * [example](https://github.com/BooCreator/Lux-AI-Season-2-Strategy-Library/tree/main/bots/example) - пример бота от разработчиков
  * ... 
* [cmd](https://github.com/BooCreator/Lux-AI-Season-2-Strategy-Library/tree/main/cmd) - команды windows для работы с kaggle, вызываются из кода
  * _competition.cmd_ - загрузить competition
  * _dataset.cmd_ - загрузить dataset
  * _install.cmd_ - установить/обновить пакеты python - kaggle, luxai_s2
  * _submit.cmd_ - засылка
* [log](https://github.com/BooCreator/Lux-AI-Season-2-Strategy-Library/tree/main/log) - папка для логов
  * [render](https://github.com/BooCreator/Lux-AI-Season-2-Strategy-Library/tree/main/log/render) - последние N фреймов игры. используется при дебаге
  * [step](https://github.com/BooCreator/Lux-AI-Season-2-Strategy-Library/tree/main/log/step) - таблицы текущего состояния из "глазок" (units, factories, e_energy и т.* 
  * [video](https://github.com/BooCreator/Lux-AI-Season-2-Strategy-Library/tree/main/log/video) - видеозаписи локальных игр
* [lux](https://github.com/BooCreator/Lux-AI-Season-2-Strategy-Library/tree/main/lux) - библиотека lux
  * ...
* [replays](https://github.com/BooCreator/Lux-AI-Season-2-Strategy-Library/tree/main/replays) - реплеи игр в формате html
  * [tournament](https://github.com/BooCreator/Lux-AI-Season-2-Strategy-Library/tree/main/replays/tornament) - турнирные реплеи
* [strategy](https://github.com/BooCreator/Lux-AI-Season-2-Strategy-Library/tree/main/strategy) - папка для разработки стратегий и локальной проверки
  * [early](https://github.com/BooCreator/Lux-AI-Season-2-Strategy-Library/tree/main/strategy/early) - папка стратегий ранней игры
  * [game](https://github.com/BooCreator/Lux-AI-Season-2-Strategy-Library/tree/main/strategy/game) - папка стратегий основной фазы игры
  * [kits](https://github.com/BooCreator/Lux-AI-Season-2-Strategy-Library/tree/main/strategy/kits) - папка с полезными классами и функциями
  * ...
* [submissions](https://github.com/BooCreator/Lux-AI-Season-2-Strategy-Library/tree/main/submissions) - архивы засылок
  * ...
* [test_env](https://github.com/BooCreator/Lux-AI-Season-2-Strategy-Library/tree/main/test_env) - файлы для локальнго запуска и тестов
  * __agent.py__ - файл агента для тестового запуска. При коздании нового агента использовать его
  * __main.py__ - файл главный файл агента
* [utils](https://github.com/BooCreator/Lux-AI-Season-2-Strategy-Library/tree/main/utils) - различные функции для работы с соревнованием и окружением
  * __clear.py__ - удалить реплеи из папки с реплеями (не турнирные)
  * __competition.py__ - функции и классы для работы с соревнованием LuxAI
  * __create_bot.py__ - создать нового бота (копируется папка bots/example)
  * __tools.py__ - полезные функции
  * __visualiser.py__ - визуализатор матриц. Превращает матрицы в изображение
* __run.py__


# Как собирать ботов?

1. Создаём папку бота внутри bots
2. Копируем файлы __agent.py__ и __main.py__ из папки _test_env_ в папку с ботов
3. Копируем папку _lux_ в папку с ботом
4. Копируем папку _strategy_ в папку с ботом
5. В файле __agent.py__ заменяем _DefaultStrategy_ на Ваш класс стратегии