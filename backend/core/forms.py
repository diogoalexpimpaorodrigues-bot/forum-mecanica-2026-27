"""Validação de registo partilhada com os validadores de segurança do Django."""

from django.contrib.auth.forms import UserCreationForm, UsernameField


class RegistrationForm(UserCreationForm):
    username = UsernameField(min_length=3, max_length=30, label="Nome de utilizador")
