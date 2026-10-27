"""Regras de pontos sem dependência de HTTP, para poderem ser testadas isoladamente.

Nunca se aceitam preços ou saldos calculados no navegador. A alteração da carteira
 e o respetivo movimento são confirmados juntos, ou ambos são revertidos.
Desenvolvido com auxílio de IA; ver AI_USAGE.md.
"""

from django.db import IntegrityError, transaction
from django.db.models import F

from .catalog import CHALLENGES, REWARDS
from .errors import DomainError
from .models import Movement, Wallet


def find_item(catalog, identifier):
    if not isinstance(identifier, str):
        raise DomainError("Identificador inválido.", code="invalid_identifier")
    item = next((item for item in catalog if item["id"] == identifier), None)
    if item is None:
        raise DomainError("Este item não existe.", code="not_found", status=404)
    return item


@transaction.atomic
def snapshot(user):
    wallet = Wallet.objects.get(user=user)
    movements = list(wallet.movements.all())
    completed = {m.reference for m in movements if m.kind == "credit"}
    redeemed = {m.reference for m in movements if m.kind == "redeem"}
    return {
        "user": {"username": user.username},
        "balance": wallet.balance,
        "revision": wallet.revision,
        "earned": sum(m.amount for m in movements if m.amount > 0),
        "spent": -sum(m.amount for m in movements if m.amount < 0),
        "challenges": [
            {k: v for k, v in c.items() if k not in ("answer", "explanation")}
            | {
                "completed": c["id"] in completed,
                "explanation": c["explanation"] if c["id"] in completed else None,
            }
            for c in CHALLENGES
        ],
        "rewards": [r | {"redeemed": r["id"] in redeemed} for r in REWARDS],
        "movements": [
            {
                "id": m.id,
                "reference": m.reference,
                "title": m.title,
                "amount": m.amount,
                "kind": m.kind,
                "code": str(m.code) if m.kind == "redeem" else None,
                "date": m.created_at.isoformat(),
            }
            for m in movements
        ],
    }


def claim_points(user, identifier, answer):
    challenge = find_item(CHALLENGES, identifier)
    if type(answer) is not int or not 0 <= answer < len(challenge["options"]):
        raise DomainError(
            "Escolhe uma das respostas disponíveis.", code="invalid_answer"
        )
    if answer != challenge["answer"]:
        raise DomainError(
            "Ainda não é essa a resposta. Pensa novamente e tenta outra vez.",
            code="incorrect_answer",
        )
    try:
        with transaction.atomic():
            Wallet.objects.filter(user=user).update(
                balance=F("balance") + challenge["points"], revision=F("revision") + 1
            )
            Movement.objects.create(
                wallet=Wallet.objects.get(user=user),
                kind="credit",
                reference=identifier,
                title=challenge["title"],
                amount=challenge["points"],
            )
    except IntegrityError:
        raise DomainError(
            "Este desafio já foi concluído. Os pontos continuam guardados.",
            code="already_completed",
            status=409,
        ) from None
    return challenge["explanation"]


def redeem_reward(user, identifier):
    reward = find_item(REWARDS, identifier)
    try:
        with transaction.atomic():
            # Esta escrita também serializa a verificação de repetição em SQLite.
            Wallet.objects.filter(user=user).update(balance=F("balance"))
            wallet = Wallet.objects.get(user=user)
            if wallet.movements.filter(kind="redeem", reference=identifier).exists():
                raise DomainError(
                    "Já resgataste este brinde. O código está no histórico.",
                    code="already_redeemed",
                    status=409,
                )
            updated = Wallet.objects.filter(
                pk=wallet.pk, balance__gte=reward["cost"]
            ).update(balance=F("balance") - reward["cost"], revision=F("revision") + 1)
            if not updated:
                raise DomainError(
                    "Ainda não tens pontos suficientes para este brinde.",
                    code="insufficient_balance",
                    status=409,
                )
            movement = Movement.objects.create(
                wallet=wallet,
                kind="redeem",
                reference=identifier,
                title=reward["title"],
                amount=-reward["cost"],
            )
    except IntegrityError:
        raise DomainError(
            "Já resgataste este brinde. O código está no histórico.",
            code="already_redeemed",
            status=409,
        ) from None
    return str(movement.code)
