from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from mailing.models import MailingRecipient, Message, Mailings


class RegisterForm(UserCreationForm):
    """Форма регистрации с email"""
    email = forms.EmailField(required=True, label='Email')

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
        return user


class MailingRecipientForm(forms.ModelForm):
    """Форма получателя (на всякий случай, если нужна кастомизация)"""
    class Meta:
        model = MailingRecipient
        fields = ['email', 'full_name', 'comment']
        widgets = {
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'full_name': forms.TextInput(attrs={'class': 'form-control'}),
            'comment': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class MessageForm(forms.ModelForm):
    """Форма сообщения"""
    class Meta:
        model = Message
        fields = ['subject', 'text']
        widgets = {
            'subject': forms.TextInput(attrs={'class': 'form-control'}),
            'text': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
        }


class MailingsForm(forms.ModelForm):
    """Форма рассылки"""
    class Meta:
        model = Mailings
        fields = ['start_time', 'end_time', 'message', 'recipients']
        widgets = {
            'start_time': forms.DateTimeInput(
                attrs={'type': 'datetime-local', 'class': 'form-control'},
                format='%Y-%m-%dT%H:%M'
            ),
            'end_time': forms.DateTimeInput(
                attrs={'type': 'datetime-local', 'class': 'form-control'},
                format='%Y-%m-%dT%H:%M'
            ),
        }