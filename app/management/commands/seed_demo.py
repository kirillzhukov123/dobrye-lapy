# -*- coding: utf-8 -*-
"""Тестовые данные для отчёта 5: приют для животных."""
import shutil
from datetime import datetime, timedelta
from pathlib import Path

from django.conf import settings
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.utils import timezone

from app.models import (
    AdoptionApplication, Enclosure, GuardianshipPayment, HomePhotoReport,
    Interview, Pet, TransferContract, VetCard, WalkBooking,
)
from app.seed_texts import CHAR, MSGS, STORY, VACC


class Command(BaseCommand):
    help = "Заполняет базу тестовыми данными (34 питомца и связанные таблицы)"

    def _copy_photos(self):
        source = Path(settings.BASE_DIR) / 'app' / 'static' / 'images' / 'pets'
        target = Path(settings.MEDIA_ROOT) / 'pets'
        target.mkdir(parents=True, exist_ok=True)
        for image in source.glob('*.jpg'):
            destination = target / image.name
            if not destination.exists():
                shutil.copy2(image, destination)

    def handle(self, *args, **options):
        self._copy_photos()

        if Pet.objects.count() >= 30:
            self.stdout.write("Данные уже есть, пропускаю")
            return

        # вольеры
        for i in range(1, 13):
            Enclosure.objects.get_or_create(number=str(i))

        # пользователи
        people = [
            ("applicant2", "Анна", "Соколова", "anna@example.com", False),
            ("volunteer2", "Павел", "Морозов", "pavel@example.com", False),
            ("applicant3", "Екатерина", "Лебедева", "ekaterina@example.com", False),
            ("volunteer3", "Сергей", "Волков", "sergey@example.com", False),
            ("applicant4", "Ольга", "Никитина", "olga@example.com", False),
            ("volunteer4", "Илья", "Фролов", "ilya@example.com", False),
            ("applicant5", "Татьяна", "Новикова", "tatyana@example.com", False),
            ("volunteer5", "Артём", "Захаров", "artem@example.com", False),
            ("applicant6", "Нина", "Орлова", "nina@example.com", False),
            ("volunteer6", "Виктор", "Белов", "viktor@example.com", False),
        ]
        for username, first, last, email, staff in people:
            user, created = User.objects.get_or_create(username=username)
            user.first_name = first
            user.last_name = last
            user.email = email
            user.is_staff = staff
            if created:
                user.set_password("demo12345")
            user.save()

        users = {u.username: u for u in User.objects.all()}
        applicants = [users[n] for n in ("applicant", "applicant2", "applicant3", "applicant4", "applicant5", "applicant6")]
        volunteers = [users[n] for n in ("volunteer", "volunteer2", "volunteer3", "volunteer4", "volunteer5", "volunteer6")]
        curator = users["curator"]

        # питомцы
        pets_data = [
            ("Рекс", "dog", "Немецкая овчарка", 36, "ready", 6, "Спокойный, слушается команд."),
            ("Белла", "cat", "Британская короткошёрстная", 24, "ready", 7, "Ласковая, любит сидеть на руках."),
            ("Чарли", "dog", "Бигль", 18, "ready", 8, "Активный, любит прогулки и игры."),
            ("Луна", "cat", "Мейн-кун", 30, "ready", 9, "Спокойная, привыкла к другим кошкам."),
            ("Макс", "dog", "Лабрадор", 48, "ready", 10, "Добрый, хорошо ладит с детьми."),
            ("Мия", "cat", "Шотландская вислоухая", 12, "ready", 11, "Игривая, но быстро устаёт."),
            ("Тоби", "dog", "Спаниель", 60, "ready", 12, "Спокойный, любит воду."),
            ("Нора", "cat", "Сибирская", 42, "ready", 6, "Независимая, но идёт на контакт."),
            ("Грей", "dog", "Хаски", 24, "reserved", 7, "Энергичный, нужен большой двор."),
            ("Соня", "cat", "Персидская", 36, "reserved", 8, "Тихая, любит лежать на солнце."),
            ("Барон", "dog", "Ротвейлер", 54, "quarantine", 9, "Наблюдаем после поступления."),
            ("Клео", "cat", "Абиссинская", 8, "quarantine", 10, "Молодая, пугливая."),
            ("Уголёк", "cat", "Дымчатая", 6, "treatment", 11, "Проходит лечение глаз."),
            ("Дана", "dog", "Колли", 30, "treatment", 12, "Лечение лапы, идёт на поправку."),
            ("Тиша", "cat", "Русская голубая", 18, "ready", 6, "Спокойная, чистоплотная."),
            ("Арчи", "dog", "Корги", 14, "ready", 7, "Весёлый, любит внимание."),
            ("Ева", "cat", "Бенгальская", 22, "ready", 8, "Любопытная, активная."),
            ("Зевс", "dog", "Доберман", 40, "ready", 9, "Служебный, нужен опытный хозяин."),
            ("Кира", "cat", "Абиссинская", 16, "ready", 10, "Ласковая, общительная."),
            ("Оскар", "dog", "Такса", 28, "ready", 11, "Спокойный, любит копать."),
            ("Плюша", "cat", "Персидская", 20, "ready", 12, "Пушистая, требует ухода за шерстью."),
            ("Ральф", "dog", "Боксёр", 34, "home", None, "Уехал в новую семью."),
            ("Мила", "cat", "Британская", 26, "home", None, "Уехала в новую семью."),
            ("Тимка", "dog", "Метис", 12, "home", None, "Уехал в новую семью."),
            ("Ася", "cat", "Метис", 10, "home", None, "Уехала в новую семью."),
        ]
        photos = {
            "dog": ["pets/dog1.jpg", "pets/dog2.jpg", "pets/dog3.jpg", "pets/dog4.jpg", "pets/dog5.jpg"],
            "cat": ["pets/cat1.jpg", "pets/cat2.jpg", "pets/cat3.jpg", "pets/cat4.jpg", "pets/cat5.jpg"],
        }
        photo_index = {"dog": 0, "cat": 0}
        for idx, (name, species, breed, age, status, enc, character) in enumerate(pets_data):
            pet, created = Pet.objects.get_or_create(name=name)
            pet.species = species
            pet.breed = breed
            pet.age_months = age
            pet.status = status
            pet.character = CHAR.get(name, character)
            pet.rescue_story = STORY.get(name, "")
            pet.enclosure = Enclosure.objects.get(number=str(enc)) if enc else None
            if created:
                pet.photo = photos[species][photo_index[species] % 5]
            photo_index[species] += 1
            pet.save()
            VetCard.objects.get_or_create(
                pet=pet, defaults={"vaccinations": VACC.get(name, "Вакцинация по графику.")})

        pets = {p.name: p for p in Pet.objects.all()}

        # анкеты
        applications_data = [
            ("Рекс", "applicant2", "new", "Живу в частном доме, есть опыт с крупными собаками."),
            ("Белла", "applicant3", "new", "Хочу взять кошку в квартиру, детей нет."),
            ("Чарли", "applicant4", "new", "Готов гулять два раза в день, есть свой двор."),
            ("Луна", "applicant5", "new", "Ищу спокойную кошку для мамы."),
            ("Макс", "applicant6", "new", "Есть дом и участок, дети 8 и 12 лет."),
            ("Рекс", "applicant3", "rejected", "Подавала анкету, но не подошла по условиям."),
            ("Белла", "applicant5", "rejected", "Передумала брать животное."),
            ("Тиша", "applicant6", "new", "Люблю кошек, готова ухаживать."),
            ("Арчи", "applicant2", "new", "Ищу небольшую собаку для квартиры."),
            ("Ева", "applicant4", "new", "Есть опыт с бенгальскими кошками."),
            ("Ральф", "applicant2", "approved", "Готов забрать собаку домой."),
            ("Мила", "applicant3", "approved", "Кошка понравилась всей семье."),
            ("Тимка", "applicant4", "approved", "Давно искали молодого пса."),
            ("Ася", "applicant5", "approved", "Готова оформить опекунство и забрать домой."),
        ]
        for pet_name, username, status, message in applications_data:
            app, created = AdoptionApplication.objects.get_or_create(
                pet=pets[pet_name], applicant=users[username],
                defaults={"status": status,
                          "message": MSGS.get((pet_name, username), message)},
            )
            if not created and status == "approved" and app.status != status:
                app.status = status
                app.save(update_fields=["status"])

        # собеседования
        interviews_data = [
            ("Рекс", "applicant2", 3, "Пришёл вовремя, ответил на вопросы."),
            ("Белла", "applicant3", 5, "Обсудили условия содержания."),
            ("Чарли", "applicant4", 7, "Показал место для прогулок."),
            ("Луна", "applicant5", 10, "Согласовали дату передачи."),
            ("Макс", "applicant6", 12, "Семья готова, нужен повторный визит."),
            ("Рекс", "applicant3", 14, "Отказ по условиям проживания."),
            ("Белла", "applicant5", 15, "Кандидат передумал."),
            ("Тиша", "applicant6", 18, "Назначено на следующей неделе."),
            ("Арчи", "applicant2", 20, "Обсудили режим прогулок."),
            ("Ева", "applicant4", 22, "Проверили опыт содержания."),
            ("Ральф", "applicant2", 24, "Решение положительное."),
            ("Мила", "applicant3", 25, "Решение положительное."),
            ("Тимка", "applicant4", 26, "Решение положительное."),
            ("Ася", "applicant5", 27, "Решение положительное."),
        ]
        for pet_name, username, day, result in interviews_data:
            app = AdoptionApplication.objects.filter(pet=pets[pet_name], applicant=users[username]).first()
            if not app:
                continue
            scheduled = timezone.make_aware(datetime(2026, 10, day, 11, 0))
            Interview.objects.get_or_create(
                application=app,
                defaults={"curator": curator, "scheduled_at": scheduled, "result": result},
            )

        # прогулки
        walk_pairs = [
            ("Рекс", "volunteer", 1, 15, True),
            ("Грей", "volunteer2", 2, 12, True),
            ("Чарли", "volunteer3", 3, 10, False),
            ("Макс", "volunteer4", 4, 16, False),
            ("Тоби", "volunteer5", 5, 11, False),
            ("Арчи", "volunteer6", 6, 14, False),
            ("Зевс", "volunteer", 7, 9, False),
            ("Оскар", "volunteer2", 8, 17, False),
            ("Дана", "volunteer3", 9, 10, False),
            ("Барон", "volunteer4", 10, 12, False),
            ("Тиша", "volunteer5", 11, 15, False),
            ("Ева", "volunteer6", 12, 13, False),
            ("Кира", "volunteer", 13, 10, False),
            ("Плюша", "volunteer2", 14, 16, False),
            ("Нора", "volunteer3", 15, 11, False),
            ("Белла", "volunteer4", 16, 14, False),
            ("Луна", "volunteer5", 17, 9, False),
            ("Мия", "volunteer6", 18, 17, False),
        ]
        for pet_name, username, day, hour, done in walk_pairs:
            when = timezone.make_aware(datetime(2026, 11, day, hour, 0))
            WalkBooking.objects.get_or_create(
                pet=pets[pet_name], when=when,
                defaults={"volunteer": users[username], "is_done": done},
            )

        # опекунские взносы
        payments_data = [
            ("Рекс", "applicant2", 500, "2026-07"),
            ("Белла", "applicant3", 700, "2026-07"),
            ("Чарли", "applicant4", 300, "2026-08"),
            ("Луна", "applicant5", 1000, "2026-08"),
            ("Макс", "applicant6", 1500, "2026-09"),
            ("Тиша", "applicant2", 400, "2026-09"),
            ("Арчи", "applicant3", 600, "2026-10"),
            ("Ева", "applicant4", 800, "2026-10"),
            ("Зевс", "applicant5", 1200, "2026-11"),
            ("Кира", "applicant6", 500, "2026-11"),
        ]
        for pet_name, username, amount, period in payments_data:
            GuardianshipPayment.objects.get_or_create(
                pet=pets[pet_name], guardian=users[username], period=period,
                defaults={"amount": amount},
            )

        # договоры и фотоотчёты
        contracts_data = [
            ("Ральф", "applicant2", "PET-31", 1),
            ("Мила", "applicant3", "PET-32", 2),
            ("Тимка", "applicant4", "PET-33", 3),
            ("Ася", "applicant5", "PET-34", 4),
        ]
        for pet_name, username, number, day in contracts_data:
            app = AdoptionApplication.objects.filter(pet=pets[pet_name], applicant=users[username]).first()
            if not app:
                continue
            if app.status != "approved":
                app.status = "approved"
                app.save(update_fields=["status"])
            pets[pet_name].status = "home"
            pets[pet_name].save(update_fields=["status"])
            contract, created = TransferContract.objects.get_or_create(
                application=app,
                defaults={
                    "pet": pets[pet_name],
                    "document_number": number,
                    "signed_at": timezone.make_aware(datetime(2026, 10, day + 20, 12, 0)),
                },
            )
            for k in range(1, 3):
                HomePhotoReport.objects.get_or_create(
                    contract=contract, photo=f"reports/report{day}_{k}.jpg",
                    defaults={"comment": "Фото из нового дома, животное освоилось."},
                )

        self.stdout.write(self.style.SUCCESS(
            "Готово: питомцев %d, анкет %d, собеседований %d, прогулок %d, взносов %d, договоров %d, фотоотчётов %d" % (
                Pet.objects.count(), AdoptionApplication.objects.count(), Interview.objects.count(),
                WalkBooking.objects.count(), GuardianshipPayment.objects.count(),
                TransferContract.objects.count(), HomePhotoReport.objects.count(),
            )
        ))
