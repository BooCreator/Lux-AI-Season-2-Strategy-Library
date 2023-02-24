# Оглавление
1. [Структура окружения](#структура-окружения)
2. [Как собирать ботов](#как-собирать-ботов)

# Структура окружения

* [bots](https://github.com/BooCreator/Lux-AI-Season-2-Strategy-Library/tree/main/bots) - боты проекта
  * [example](https://github.com/BooCreator/Lux-AI-Season-2-Strategy-Library/tree/main/bots/example) - пример бота от разработчиков
  * _more..._
* [cmd](https://github.com/BooCreator/Lux-AI-Season-2-Strategy-Library/tree/main/cmd) - команды windows для работы с kaggle, вызываются из кода
  * _competition.cmd_ - загрузить competition
  * _dataset.cmd_ - загрузить dataset
  * _install.cmd_ - установить/обновить пакеты python - kaggle, luxai_s2
  * _submit.cmd_ - засылка
* [log](https://github.com/BooCreator/Lux-AI-Season-2-Strategy-Library/tree/main/log) - папка для логов
  * [render](https://github.com/BooCreator/Lux-AI-Season-2-Strategy-Library/tree/main/log/render) - последние N фреймов игры, используется при дебаге
  * [step](https://github.com/BooCreator/Lux-AI-Season-2-Strategy-Library/tree/main/log/step) - таблицы текущего состояния из "глазок" (units, factories, e_energy и т.д) 
  * [video](https://github.com/BooCreator/Lux-AI-Season-2-Strategy-Library/tree/main/log/video) - видеозаписи локальных игр
* [lux](https://github.com/BooCreator/Lux-AI-Season-2-Strategy-Library/tree/main/lux) - библиотека lux
* [replays](https://github.com/BooCreator/Lux-AI-Season-2-Strategy-Library/tree/main/replays) - реплеи игр в формате .html
  * [tournament](https://github.com/BooCreator/Lux-AI-Season-2-Strategy-Library/tree/main/replays/tornament) - турнирные реплеи
* [strategy](https://github.com/BooCreator/Lux-AI-Season-2-Strategy-Library/tree/main/strategy) - папка для разработки стратегий и локальной проверки
  * [early](https://github.com/BooCreator/Lux-AI-Season-2-Strategy-Library/tree/main/strategy/early) - папка стратегий ранней игры
  * [game](https://github.com/BooCreator/Lux-AI-Season-2-Strategy-Library/tree/main/strategy/game) - папка стратегий основной фазы игры
  * [kits](https://github.com/BooCreator/Lux-AI-Season-2-Strategy-Library/tree/main/strategy/kits) - папка с полезными классами и функциями
* [submissions](https://github.com/BooCreator/Lux-AI-Season-2-Strategy-Library/tree/main/submissions) - архивы засылок
* [test_env](https://github.com/BooCreator/Lux-AI-Season-2-Strategy-Library/tree/main/test_env) - файлы для локальнго запуска и тестов
  * _agent.py_ - файл агента для тестового запуска. При коздании нового агента использовать его
  * _main.py_ - файл главный файл агента
* [utils](https://github.com/BooCreator/Lux-AI-Season-2-Strategy-Library/tree/main/utils) - различные функции для работы с соревнованием и окружением
  * _clear.py_ - удалить реплеи из папки с реплеями (не турнирные)
  * _competition.py_ - функции и классы для работы с соревнованием LuxAI
  * _create_bot.py_ - создать нового бота (копируется папка bots/example)
  * _tools.py_ - полезные функции
  * _visualiser.py_ - визуализатор матриц. Превращает матрицы в изображение
* _run.py_ - файл запуска всего


# Как собирать ботов?

1. Создаём папку бота внутри bots
2. Копируем файлы __agent.py__ и __main.py__ из папки _[test_env](https://github.com/BooCreator/Lux-AI-Season-2-Strategy-Library/tree/main/test_env)_ в папку с ботов
3. Копируем папку _[lux](https://github.com/BooCreator/Lux-AI-Season-2-Strategy-Library/tree/main/lux)_ в папку с ботом
4. Копируем папку _[strategy](https://github.com/BooCreator/Lux-AI-Season-2-Strategy-Library/tree/main/strategy)_ в папку с ботом
5. В файле __agent.py__ заменяем _DefaultStrategy_ на Ваш класс стратегии