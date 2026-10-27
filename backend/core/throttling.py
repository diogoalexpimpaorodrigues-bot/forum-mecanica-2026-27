"""Orçamento de pedidos persistente, partilhado por todos os processos Django.

A escrita inicial é intencional: no SQLite, reserva o escritor antes da leitura.
Assim, duas tentativas não conseguem consumir a última vaga em simultâneo.
Desenvolvido com auxílio de IA; ver AI_USAGE.md.
"""

import math

from django.db import transaction
from django.db.models import F
from django.utils import timezone
from django.utils.crypto import salted_hmac

from .errors import DomainError
from .models import RequestBudget


def consume(scope, identity, *, limit, seconds):
    key = salted_hmac(
        "forum.request-budget", f"{scope}:{identity}", algorithm="sha256"
    ).hexdigest()
    now = timezone.now()
    with transaction.atomic():
        RequestBudget.objects.filter(key=key).update(used=F("used"))
        budget, _ = RequestBudget.objects.get_or_create(
            key=key, defaults={"started_at": now}
        )
        elapsed = (now - budget.started_at).total_seconds()
        if elapsed >= seconds:
            budget.started_at = now
            budget.used = 0
            elapsed = 0
        if budget.used >= limit:
            retry = max(1, math.ceil(seconds - elapsed))
            raise DomainError(
                "Demasiadas tentativas. Aguarda alguns minutos e volta a tentar.",
                code="rate_limited",
                status=429,
                retry_after=retry,
            )
        budget.used += 1
        budget.save(update_fields=["used", "started_at"])
