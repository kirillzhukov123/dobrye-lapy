# Приют «Добрые лапы»

Сайт городского приюта для собак и кошек. Проект на Django.

Сайт: https://kirillzhukov123.github.io/dobrye-lapy/

## Что сделано

- проект Django и приложение `app`
- шаблоны: главная, каталог, карточка питомца, поиск, опекунство, личный кабинет, о приюте, вход и регистрация
- данные из моделей: питомцы, вольеры, ветеринарные карточки, анкеты, прогулки, взносы и договоры
- фильтры и сортировка каталога, пагинация по 20 записей
- адаптивная вёрстка и меню-бургер на мобильных экранах
- один файл стилей и общий файл скриптов

## Структура

- `project/` — настройки и корневые маршруты
- `app/models.py` — модели приюта
- `app/views.py` — представления страниц
- `app/forms.py` — формы
- `app/templates/` — шаблоны
- `app/static/` — стили, скрипты и изображения
- `app/fixtures/initial_data.json` — тестовые данные
- `app/management/commands/seed_demo.py` — подготовка демонстрационной базы и фотографий

## Запуск

```
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py loaddata initial_data
python manage.py seed_demo
python manage.py runserver
```

Сайт откроется по адресу http://127.0.0.1:8000/

Демонстрационные пользователи: `applicant` и `curator`, пароль `demo12345`.
