
# Магазин Megano

Проект интернет-магазина с предварительно настроенным фронтендом


## Использованные технологии

**Versio control:** Poetry

**Client:** JavaScript, 

**Server:** Django, DRF, 


## Развертывание

Чтобы развернуть этот проект, у вас должен быть установлен Poetry.

Скопируйте репозиторий

Для запуска приложения выполните команду из директории `megano/`

```bash
  python manage.py runserver
```

Приложение будет доступно по адресу `http://127.0.0.1:8000/`

Чтение документации swagger:

- `http://127.0.0.1:8000/swagger/upload/` - выберите файл swagger
- Нажмите кнопку `Загрузить`
- Если все прошло успешно, вы будете перенаправлены на страницу `http://127.0.0.1:8000/swagger/ui/<имя_файла>/` где сможете увидеть содержание своего файла по стандарту OpenAPI

