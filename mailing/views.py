from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.mail import send_mail
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.cache import cache_page, never_cache
from django.views.generic import (
    ListView, DetailView, TemplateView,
    CreateView, UpdateView, DeleteView,
)

from mailing.forms import RegisterForm
from mailing.models import MailingRecipient, Message, Mailings, Attempts


# === МИКСИНЫ ===
class OwnerRequiredMixin(UserPassesTestMixin):
    """Проверяет, что текущий пользователь — владелец объекта"""

    def test_func(self):
        obj = self.get_object()
        return obj.user == self.request.user


class ManagerRequiredMixin(UserPassesTestMixin):
    """Проверяет, что пользователь — менеджер (staff)"""

    def test_func(self):
        return self.request.user.is_staff


# === КАСТОМНЫЙ ЛОГАУТ (без кеша) ===
@method_decorator(never_cache, name='dispatch')
class CustomLogoutView(View):
    """Кастомный логаут — работает GET и POST"""

    def get(self, request):
        logout(request)
        return redirect('mailing:home')

    def post(self, request):
        logout(request)
        return redirect('mailing:home')


# === ГЛАВНАЯ (кеш 5 минут) ===
@method_decorator(cache_page(60 * 5), name='dispatch')
class HomeView(TemplateView):
    template_name = 'mailing/home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        now = timezone.now()
        context['total_mailings'] = Mailings.objects.count()
        context['active_mailings'] = Mailings.objects.filter(
            start_time__lte=now, end_time__gte=now, status=Mailings.Status.STARTED
        ).count()
        context['unique_clients'] = MailingRecipient.objects.values('email').distinct().count()
        return context


# === ПОЛУЧАТЕЛИ (кеш 2 минуты) ===
@method_decorator(cache_page(60 * 2), name='dispatch')
class MailingRecipientListView(LoginRequiredMixin, ListView):
    model = MailingRecipient
    template_name = 'mailing/recipient_list.html'
    context_object_name = 'recipients'

    def get_queryset(self):
        return MailingRecipient.objects.filter(user=self.request.user)


class MailingRecipientCreateView(LoginRequiredMixin, CreateView):
    model = MailingRecipient
    template_name = 'mailing/recipient_form.html'
    fields = ['email', 'full_name', 'comment']
    success_url = reverse_lazy('mailing:mailing_recipient_list')

    def form_valid(self, form):
        form.instance.user = self.request.user
        messages.success(self.request, 'Получатель успешно создан')
        return super().form_valid(form)


class MailingRecipientUpdateView(LoginRequiredMixin, OwnerRequiredMixin, UpdateView):
    model = MailingRecipient
    template_name = 'mailing/recipient_form.html'
    fields = ['email', 'full_name', 'comment']
    success_url = reverse_lazy('mailing:mailing_recipient_list')

    def form_valid(self, form):
        messages.success(self.request, 'Получатель успешно обновлён')
        return super().form_valid(form)


class MailingRecipientDeleteView(LoginRequiredMixin, OwnerRequiredMixin, DeleteView):
    model = MailingRecipient
    template_name = 'mailing/recipient_confirm_delete.html'
    success_url = reverse_lazy('mailing:mailing_recipient_list')

    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Получатель удалён')
        return super().delete(request, *args, **kwargs)


# === СООБЩЕНИЯ (кеш 2 минуты) ===
@method_decorator(cache_page(60 * 2), name='dispatch')
class MessageListView(LoginRequiredMixin, ListView):
    model = Message
    template_name = 'mailing/message_list.html'
    context_object_name = 'messages_list'

    def get_queryset(self):
        return Message.objects.filter(user=self.request.user)


class MessageCreateView(LoginRequiredMixin, CreateView):
    model = Message
    template_name = 'mailing/message_form.html'
    fields = ['subject', 'text']
    success_url = reverse_lazy('mailing:message_list')

    def form_valid(self, form):
        form.instance.user = self.request.user
        messages.success(self.request, 'Сообщение успешно создано')
        return super().form_valid(form)


class MessageUpdateView(LoginRequiredMixin, OwnerRequiredMixin, UpdateView):
    model = Message
    template_name = 'mailing/message_form.html'
    fields = ['subject', 'text']
    success_url = reverse_lazy('mailing:message_list')

    def form_valid(self, form):
        messages.success(self.request, 'Сообщение обновлено')
        return super().form_valid(form)


class MessageDeleteView(LoginRequiredMixin, OwnerRequiredMixin, DeleteView):
    model = Message
    template_name = 'mailing/message_confirm_delete.html'
    success_url = reverse_lazy('mailing:message_list')

    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Сообщение удалено')
        return super().delete(request, *args, **kwargs)


# === РАССЫЛКИ (кеш 2 минуты) ===
@method_decorator(cache_page(60 * 2), name='dispatch')
class MailingsListView(LoginRequiredMixin, ListView):
    model = Mailings
    template_name = 'mailing/mailings_list.html'
    context_object_name = 'mailings'

    def get_queryset(self):
        return Mailings.objects.filter(user=self.request.user)


class MailingsDetailView(LoginRequiredMixin, OwnerRequiredMixin, DetailView):
    model = Mailings
    template_name = 'mailing/mailings_detail.html'
    context_object_name = 'mailing'

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        obj.update_status()
        return obj


class MailingsCreateView(LoginRequiredMixin, CreateView):
    model = Mailings
    template_name = 'mailing/mailings_form.html'
    fields = ['start_time', 'end_time', 'message', 'recipients']
    success_url = reverse_lazy('mailing:mailing_list')

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields['message'].queryset = Message.objects.filter(user=self.request.user)
        form.fields['recipients'].queryset = MailingRecipient.objects.filter(user=self.request.user)
        return form

    def form_valid(self, form):
        form.instance.user = self.request.user
        messages.success(self.request, 'Рассылка создана')
        return super().form_valid(form)


class MailingsUpdateView(LoginRequiredMixin, OwnerRequiredMixin, UpdateView):
    model = Mailings
    template_name = 'mailing/mailings_form.html'
    fields = ['start_time', 'end_time', 'message', 'recipients']
    success_url = reverse_lazy('mailing:mailing_list')

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields['message'].queryset = Message.objects.filter(user=self.request.user)
        form.fields['recipients'].queryset = MailingRecipient.objects.filter(user=self.request.user)
        return form

    def form_valid(self, form):
        messages.success(self.request, 'Рассылка обновлена')
        return super().form_valid(form)


class MailingsDeleteView(LoginRequiredMixin, OwnerRequiredMixin, DeleteView):
    model = Mailings
    template_name = 'mailing/mailings_confirm_delete.html'
    success_url = reverse_lazy('mailing:mailing_list')

    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Рассылка удалена')
        return super().delete(request, *args, **kwargs)


# === ОТПРАВКА ===
def send_mailing(request, pk):
    mailing = get_object_or_404(Mailings, pk=pk, user=request.user)
    mailing.update_status()

    if not mailing.can_send():
        messages.error(request, 'Рассылка не может быть отправлена: время отправки не подходит')
        return redirect('mailing:mailing_detail', pk=pk)

    recipients = mailing.recipients.all()
    if not recipients:
        messages.error(request, 'Нет получателей для отправки')
        return redirect('mailing:mailing_detail', pk=pk)

    message = mailing.message
    success_count = 0
    error_count = 0

    for recipient in recipients:
        try:
            send_mail(
                subject=message.subject,
                message=message.text,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[recipient.email],
                fail_silently=False,
            )
            Attempts.objects.create(
                mailing=mailing,
                status=Attempts.Status.SUCCESSFUL,
                server_response='Письмо отправлено успешно'
            )
            success_count += 1

        except Exception as e:
            Attempts.objects.create(
                mailing=mailing,
                status=Attempts.Status.UNSUCCESSFUL,
                server_response=str(e)
            )
            error_count += 1

    if success_count > 0:
        messages.success(request, f'Отправлено: {success_count}. Ошибок: {error_count}')
    else:
        messages.error(request, f'Отправка не удалась. Ошибок: {error_count}')

    return redirect('mailing:mailing_detail', pk=pk)


# === ПОПЫТКИ (кеш 1 минута) ===
@method_decorator(cache_page(60 * 1), name='dispatch')
class AttemptsListView(LoginRequiredMixin, ListView):
    model = Attempts
    template_name = 'mailing/attempt_list.html'
    context_object_name = 'attempts'

    def get_queryset(self):
        return Attempts.objects.filter(mailing__user=self.request.user).select_related('mailing')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        attempts = self.get_queryset()
        context['attempts_success'] = attempts.filter(status=Attempts.Status.SUCCESSFUL).count()
        context['attempts_failed'] = attempts.filter(status=Attempts.Status.UNSUCCESSFUL).count()
        return context


# === РЕГИСТРАЦИЯ ===
class RegisterView(CreateView):
    form_class = RegisterForm
    template_name = 'registration/register.html'
    success_url = reverse_lazy('mailing:home')

    def form_valid(self, form):
        user = form.save()
        login(self.request, user)
        messages.success(self.request, 'Регистрация успешна! Вы вошли в систему.')
        return redirect(self.success_url)


# === МЕНЕДЖЕР ===
@method_decorator(cache_page(60 * 2), name='dispatch')
class ManagerMailingsListView(LoginRequiredMixin, ManagerRequiredMixin, ListView):
    model = Mailings
    template_name = 'mailing/mailings_list.html'
    context_object_name = 'mailings'

    def get_queryset(self):
        return Mailings.objects.all()


@method_decorator(cache_page(60 * 2), name='dispatch')
class ManagerRecipientsListView(LoginRequiredMixin, ManagerRequiredMixin, ListView):
    model = MailingRecipient
    template_name = 'mailing/recipient_list.html'
    context_object_name = 'recipients'

    def get_queryset(self):
        return MailingRecipient.objects.all()


@method_decorator(cache_page(60 * 2), name='dispatch')
class ManagerUsersListView(LoginRequiredMixin, ManagerRequiredMixin, ListView):
    template_name = 'mailing/users_list.html'
    context_object_name = 'users'

    def get_queryset(self):
        from django.contrib.auth.models import User
        return User.objects.all()