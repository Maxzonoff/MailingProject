from django.core.exceptions import ValidationError
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class MailingRecipient(models.Model):
    """Получатель рассылки"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='recipients')
    email = models.EmailField(unique=True, verbose_name='Email')
    full_name = models.CharField(max_length=255, verbose_name='Ф.И.О.')
    comment = models.TextField(blank=True, verbose_name='Комментарий')

    class Meta:
        verbose_name = 'Получатель рассылки'
        verbose_name_plural = 'Получатели рассылок'
        ordering = ['full_name']

    def __str__(self):
        return f"{self.full_name} ({self.email})"


class Message(models.Model):
    """Сообщение"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='messages')
    subject = models.CharField(max_length=255, verbose_name='Тема письма')
    text = models.TextField(verbose_name='Тело письма')

    class Meta:
        verbose_name = 'Сообщение'
        verbose_name_plural = 'Сообщения'
        ordering = ['subject']

    def __str__(self):
        return self.subject


class Mailings(models.Model):
    """Рассылки"""

    class Status(models.TextChoices):
        CREATED = 'created', 'Создана'
        STARTED = 'started', 'Запущена'
        DONE = 'done', 'Завершена'

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='mailings')
    start_time = models.DateTimeField(verbose_name='Дата и время начала')
    end_time = models.DateTimeField(verbose_name='Дата и время окончания')
    status = models.CharField(
        max_length=16,
        choices=Status.choices,
        default=Status.CREATED,
        verbose_name='Статус'
    )
    message = models.ForeignKey(
        Message,
        on_delete=models.CASCADE,
        verbose_name='Сообщение',
        related_name='mailings'
    )
    recipients = models.ManyToManyField(
        MailingRecipient,
        verbose_name='Получатели',
        related_name='mailings'
    )

    class Meta:
        verbose_name = 'Рассылка'
        verbose_name_plural = 'Рассылки'
        ordering = ['-start_time']

    def __str__(self):
        return f"Рассылка {self.id} — {self.get_status_display()}"

    def clean(self):
        """Валидация дат"""
        if not self.start_time or not self.end_time:
            raise ValidationError('Дата начала и окончания должны быть заполнены')

        if self.start_time >= self.end_time:
            raise ValidationError({
                'start_time': 'Дата начала должна быть раньше даты окончания',
                'end_time': 'Дата окончания должна быть позже даты начала'
            })

        # Проверка: start_time не может быть в прошлом (только при создании)
        # При редактировании разрешаем — рассылка уже могла начаться
        if not self.pk and self.start_time < timezone.now():
            raise ValidationError({
                'start_time': 'Дата начала не может быть в прошлом'
            })

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def update_status(self):
        """
        Динамически обновляет статус рассылки на основе текущего времени.
        Вызывать при просмотре рассылки (в get_object() во View).
        """
        now = timezone.now()
        old_status = self.status

        if now < self.start_time:
            new_status = self.Status.CREATED
        elif self.start_time <= now <= self.end_time:
            new_status = self.Status.STARTED
        else:  # now > self.end_time
            new_status = self.Status.DONE

        if old_status != new_status:
            self.status = new_status
            self.save(update_fields=['status'])

        return self.status

    def can_send(self):
        """Проверяет, можно ли сейчас отправлять рассылку"""
        now = timezone.now()
        return self.start_time <= now <= self.end_time


class Attempts(models.Model):
    """Попытки рассылок"""

    class Status(models.TextChoices):
        SUCCESSFUL = 'successful', 'Успешно'
        UNSUCCESSFUL = 'unsuccessful', 'Не успешно'

    attempt_time = models.DateTimeField(auto_now_add=True, verbose_name='Дата и время попытки')
    status = models.CharField(max_length=16, choices=Status.choices, verbose_name='Статус')
    server_response = models.TextField(verbose_name='Ответ сервера', blank=True)
    mailing = models.ForeignKey(
        Mailings,
        on_delete=models.CASCADE,
        verbose_name='Рассылка',
        related_name='attempts'
    )

    class Meta:
        verbose_name = 'Попытка рассылки'
        verbose_name_plural = 'Попытки рассылок'
        ordering = ['-attempt_time']

    def __str__(self):
        return f"Попытка {self.id} — {self.get_status_display()}"