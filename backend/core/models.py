"""O saldo é materializado e o histórico guarda cada movimento de forma auditável."""

import uuid

from django.conf import settings
from django.db import models
from django.db.models import Q


class Wallet(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    balance = models.PositiveIntegerField(default=0)
    revision = models.PositiveIntegerField(default=0)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=Q(balance__gte=0), name="saldo_nao_negativo"
            )
        ]


class Movement(models.Model):
    wallet = models.ForeignKey(
        Wallet, on_delete=models.CASCADE, related_name="movements"
    )
    kind = models.CharField(
        max_length=10, choices=[("credit", "Crédito"), ("redeem", "Resgate")]
    )
    reference = models.CharField(max_length=40)
    title = models.CharField(max_length=100)
    amount = models.IntegerField()
    code = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "-id"]
        constraints = [
            models.UniqueConstraint(
                fields=["wallet", "kind", "reference"], name="movimento_unico"
            ),
            models.CheckConstraint(
                condition=(
                    Q(kind="credit", amount__gt=0) | Q(kind="redeem", amount__lt=0)
                ),
                name="sinal_movimento",
            ),
        ]


class RequestBudget(models.Model):
    """Uma linha por origem/âmbito; a chave usa HMAC com o segredo da aplicação."""

    key = models.CharField(max_length=64, unique=True)
    used = models.PositiveIntegerField(default=0)
    started_at = models.DateTimeField(db_index=True)
