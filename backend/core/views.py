"""Adaptadores HTTP: autenticam, validam e delegam as regras nos serviços.
Desenvolvido com auxílio de IA; ver AI_USAGE.md.
"""

from django.contrib.auth import authenticate, get_user_model, login, logout
from django.db import IntegrityError, transaction
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie

from .errors import DomainError
from .forms import RegistrationForm
from .http import endpoint, problem, read_json
from .models import Wallet
from .services import claim_points, redeem_reward, snapshot
from .throttling import consume


def credentials(data, *, registration=False):
    fields = ["username", "password"] + (["confirmation"] if registration else [])
    invalid = {
        name: ["Preenche este campo com texto."]
        for name in fields
        if not isinstance(data.get(name), str) or not data[name]
    }
    if invalid:
        raise DomainError("Revê os campos assinalados.", fields=invalid)
    username = get_user_model().normalize_username(data["username"].strip())
    if (
        len(username) > 30
        or len(data["password"]) > 128
        or len(data.get("confirmation", "")) > 128
    ):
        raise DomainError(
            "O nome admite 30 caracteres e a palavra-passe 128.", code="invalid_length"
        )
    return username, data["password"]


@endpoint("GET")
@ensure_csrf_cookie
def session(request):
    return JsonResponse(
        snapshot(request.user) if request.user.is_authenticated else {"user": None}
    )


@endpoint("POST")
def register(request):
    data = read_json(request, required=["username", "password", "confirmation"])
    username, password = credentials(data, registration=True)
    consume("register-ip", request.META.get("REMOTE_ADDR", ""), limit=10, seconds=600)
    form = RegistrationForm(
        {"username": username, "password1": password, "password2": data["confirmation"]}
    )
    if not form.is_valid():
        fields = {}
        for name, errors in form.errors.get_json_data().items():
            for item in errors:
                target = name
                if name == "password1" or (
                    name == "password2"
                    and item.get("code") not in {"password_mismatch", "required"}
                ):
                    target = "password"
                elif name == "password2":
                    target = "confirmation"
                fields.setdefault(target, []).append(item["message"])
        raise DomainError(
            "Revê os campos assinalados.", code="validation_failed", fields=fields
        )
    try:
        with transaction.atomic():
            user = form.save()
            Wallet.objects.create(user=user)
    except IntegrityError:
        raise DomainError(
            "Este nome já está a ser utilizado.",
            code="username_taken",
            status=409,
            fields={"username": ["Escolhe outro nome de utilizador."]},
        ) from None
    login(request, user)
    return JsonResponse(snapshot(user), status=201)


@endpoint("POST")
def sign_in(request):
    data = read_json(request, required=["username", "password"])
    username, password = credentials(data)
    origin = request.META.get("REMOTE_ADDR", "")
    # Consumimos o orçamento antes do hashing. Os limites incluem tentativas bem-sucedidas.
    consume("login-ip", origin, limit=60, seconds=600)
    consume("login-identity", f"{origin}:{username}", limit=5, seconds=600)
    user = authenticate(request, username=username, password=password)
    if user is None:
        raise DomainError(
            "Nome ou palavra-passe incorretos.", code="invalid_credentials", status=401
        )
    # Também permite entrar com uma conta criada pelo comando createsuperuser.
    Wallet.objects.get_or_create(user=user)
    login(request, user)
    return JsonResponse(snapshot(user))


@endpoint("POST")
def sign_out(request):
    # Sair duas vezes tem o mesmo resultado, incluindo quando a sessão já expirou.
    logout(request)
    return JsonResponse({"user": None})


@endpoint("POST", authenticated=True)
def claim(request):
    data = read_json(request, required=["id", "answer"])
    check_account(request, data)
    message = claim_points(request.user, data["id"], data["answer"])
    return JsonResponse(snapshot(request.user) | {"message": message})


@endpoint("POST", authenticated=True)
def redeem(request):
    data = read_json(request, required=["id"])
    check_account(request, data)
    code = redeem_reward(request.user, data["id"])
    return JsonResponse(
        snapshot(request.user)
        | {
            "message": "Resgate confirmado. O teu código ficou guardado no histórico.",
            "redemption_code": code,
        }
    )


def check_account(request, data):
    # O nome não autoriza nada: apenas deteta uma troca de conta noutro separador.
    if "expected_user" in data and data["expected_user"] != request.user.username:
        raise DomainError(
            "A conta mudou noutro separador. Confirma o utilizador antes de continuar.",
            code="account_changed",
            status=409,
        )


def not_found(request):
    return problem(DomainError("Endpoint desconhecido.", code="not_found", status=404))
