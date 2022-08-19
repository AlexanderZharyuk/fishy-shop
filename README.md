# FISHY SHOP
Бот-магазин по продаже рыбы.

Ссылка на бота:
* [Telegram](https://t.me/FishyStoreBot)

### ▽ Начало работы
Для начала работы необходимо установить зависимости и библиотеки:
```shell
pip install -r requirements.txt
```

После чего создать `.env`-файл с переменными окружения:
```
MOLTIN_CLIENT_ID=<MOLTIN-CLIENT-ID>
MOLTIN_CLIENT_SECRET=<MOLTIN-CLIENT-SECRET>
TELEGRAM_BOT_TOKEN=<TELEGRAM-BOT-TOKEN>
REDIS_HOST=<REDIS-HOST>
REDIS_PORT=<REDIS-PORT>
REDIS_PASSWORD=<REDIS-PASSWORD>
```

- Для получения БД Redis и доступа к ней, обратитесь к официальному сайту [Redis](https://redis.com/).
- Для получения секретных данных сервиса [moltin](https://www.elasticpath.com/) - перейдите на главную страницу вашего магазина.


Запуск бота осуществляется командами:
```shell
python3 bots/main.py
```

### ▽ Автор
* [Alexander Zharyuk](https://github.com/AlexanderZharyuk)