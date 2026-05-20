from django.core.management.base import BaseCommand
from django.utils import timezone
from django.core.mail import send_mail

from mailing.models import Mailings, Attempts


class Command(BaseCommand):
    """Команда для отправки рассылок вручную через терминал"""
    help = 'Отправляет активные рассылки'

    def handle(self, *args, **options):
        now = timezone.now()

        # Находим рассылки, которые можно отправлять
        # (текущее время между start_time и end_time, статус "Запущена")
        mailings = Mailings.objects.filter(
            start_time__lte=now,
            end_time__gte=now,
            status=Mailings.Status.STARTED
        )

        if not mailings:
            self.stdout.write(self.style.WARNING('Нет активных рассылок для отправки'))
            return

        total_sent = 0
        total_errors = 0

        for mailing in mailings:
            self.stdout.write(f'Обработка рассылки #{mailing.id} — {mailing.message.subject}')

            recipients = mailing.recipients.all()
            if not recipients:
                self.stdout.write(self.style.WARNING(f'  Нет получателей'))
                continue

            message = mailing.message

            for recipient in recipients:
                try:
                    send_mail(
                        subject=message.subject,
                        message=message.text,
                        from_email=None,
                        recipient_list=[recipient.email],
                        fail_silently=False,
                    )

                    Attempts.objects.create(
                        mailing=mailing,
                        status=Attempts.Status.SUCCESSFUL,
                        server_response='Отправлено через команду'
                    )
                    total_sent += 1
                    self.stdout.write(self.style.SUCCESS(f'  ✓ {recipient.email}'))

                except Exception as e:
                    Attempts.objects.create(
                        mailing=mailing,
                        status=Attempts.Status.UNSUCCESSFUL,
                        server_response=str(e)
                    )
                    total_errors += 1
                    self.stdout.write(self.style.ERROR(f'  ✗ {recipient.email}: {e}'))

        self.stdout.write(self.style.SUCCESS(
            f'\nИтого: отправлено {total_sent}, ошибок {total_errors}'
        ))