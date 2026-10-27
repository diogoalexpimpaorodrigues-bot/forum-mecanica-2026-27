"""Rejeita uma palavra-passe visualmente vazia sem a transformar ou cortar."""

from django.core.exceptions import ValidationError


class NotBlankPasswordValidator:
    def validate(self, password, user=None):
        if not password.strip():
            raise ValidationError(
                "A palavra-passe não pode ser composta apenas por espaços.",
                code="password_blank",
            )

    def get_help_text(self):
        return "A palavra-passe deve conter caracteres para além de espaços."
