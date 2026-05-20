from django.contrib import admin
from .models import Message, Mailings, MailingRecipient, Attempts


@admin.register(MailingRecipient)
class MailingRecipientAdmin(admin.ModelAdmin):
    list_display = ("id", "email", "full_name", "user")
    list_filter = ("user",)
    search_fields = ("email", "full_name")


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ("id", "subject", "user")
    list_filter = ("user",)
    search_fields = ("subject",)


@admin.register(Mailings)
class MailingsAdmin(admin.ModelAdmin):
    list_display = ("id", "status", "start_time", "end_time", "message", "user")
    list_filter = ("status", "user")
    filter_horizontal = ("recipients",)  # Удобный выбор получателей


@admin.register(Attempts)
class AttemptsAdmin(admin.ModelAdmin):
    list_display = ("id", "mailing", "status", "attempt_time")
    list_filter = ("status", "mailing")