from django.urls import path
from mailing.views import (
    HomeView,
    # Получатели
    MailingRecipientListView,
    MailingRecipientCreateView,
    MailingRecipientUpdateView,
    MailingRecipientDeleteView,
    # Сообщения
    MessageListView,
    MessageCreateView,
    MessageUpdateView,
    MessageDeleteView,
    # Рассылки
    MailingsListView,
    MailingsCreateView,
    MailingsDetailView,
    MailingsUpdateView,
    MailingsDeleteView,
    send_mailing,
    # Попытки
    AttemptsListView,
    # Регистрация
    RegisterView,
    ManagerMailingsListView,
    ManagerRecipientsListView,
    ManagerUsersListView,
)

app_name = "mailing"

urlpatterns = [
    # === ГЛАВНАЯ ===
    path("", HomeView.as_view(), name="home"),

    # === ПОЛУЧАТЕЛИ ===
    path("recipients/", MailingRecipientListView.as_view(), name="mailing_recipient_list"),
    path("recipients/new/", MailingRecipientCreateView.as_view(), name="mailing_recipient_create"),
    path("recipients/<int:pk>/update/", MailingRecipientUpdateView.as_view(), name="mailing_recipient_update"),
    path("recipients/<int:pk>/delete/", MailingRecipientDeleteView.as_view(), name="mailing_recipient_delete"),

    # === СООБЩЕНИЯ ===
    path("messages/", MessageListView.as_view(), name="message_list"),
    path("messages/new/", MessageCreateView.as_view(), name="message_create"),
    path("messages/<int:pk>/update/", MessageUpdateView.as_view(), name="message_update"),
    path("messages/<int:pk>/delete/", MessageDeleteView.as_view(), name="message_delete"),

    # === РАССЫЛКИ ===
    path("mailings/", MailingsListView.as_view(), name="mailing_list"),
    path("mailings/new/", MailingsCreateView.as_view(), name="mailing_create"),
    path("mailings/<int:pk>/", MailingsDetailView.as_view(), name="mailing_detail"),
    path("mailings/<int:pk>/update/", MailingsUpdateView.as_view(), name="mailing_update"),
    path("mailings/<int:pk>/delete/", MailingsDeleteView.as_view(), name="mailing_delete"),
    path("mailings/<int:pk>/send/", send_mailing, name="mailing_send"),

    # === ПОПЫТКИ ===
    path("attempts/", AttemptsListView.as_view(), name="attempt_list"),

    # === РЕГИСТРАЦИЯ ===
    path("users/register/", RegisterView.as_view(), name="register"),

# === МЕНЕДЖЕР ===
    path("manager/mailings/", ManagerMailingsListView.as_view(), name="manager_mailing_list"),
    path("manager/recipients/", ManagerRecipientsListView.as_view(), name="manager_recipient_list"),
    path("manager/users/", ManagerUsersListView.as_view(), name="manager_user_list"),
]