"""Contrato HTTP comum: validação de JSON, autenticação e erros previsíveis."""

import json
import logging
from functools import wraps

from django.core.exceptions import RequestDataTooBig
from django.db import OperationalError
from django.http import JsonResponse

from .errors import DomainError

logger = logging.getLogger(__name__)


def problem(error):
    data = {"error": error.message, "code": error.code}
    if error.fields:
        data["fields"] = error.fields
    if error.retry_after is not None:
        data["retry_after"] = error.retry_after
    response = JsonResponse(data, status=error.status)
    if error.retry_after is not None:
        response["Retry-After"] = str(error.retry_after)
    return response


def endpoint(method, *, authenticated=False):
    def decorate(view):
        @wraps(view)
        def wrapped(request, *args, **kwargs):
            try:
                if request.method != method:
                    response = problem(
                        DomainError(
                            "Método não permitido.",
                            code="method_not_allowed",
                            status=405,
                        )
                    )
                    response["Allow"] = method
                    return response
                if authenticated and not request.user.is_authenticated:
                    raise DomainError(
                        "A tua sessão terminou. Entra novamente para continuar.",
                        code="unauthenticated",
                        status=401,
                    )
                return view(request, *args, **kwargs)
            except DomainError as error:
                return problem(error)
            except RequestDataTooBig:
                return problem(
                    DomainError(
                        "O pedido é demasiado grande.",
                        code="payload_too_large",
                        status=413,
                    )
                )
            except OperationalError:
                # Não confundimos uma escrita indisponível com dados inválidos.
                logger.warning(
                    "Base de dados temporariamente indisponível em %s", request.path
                )
                return problem(
                    DomainError(
                        "O serviço está ocupado. Atualiza o estado e tenta novamente.",
                        code="service_busy",
                        status=503,
                        retry_after=2,
                    )
                )

        return wrapped

    return decorate


def reject_nonfinite(value):
    raise ValueError("JSON não admite números não finitos")


def read_json(request, *, required):
    if request.content_type != "application/json":
        raise DomainError(
            "Envia o pedido em formato JSON.", code="unsupported_media_type", status=415
        )
    try:
        data = json.loads(request.body, parse_constant=reject_nonfinite)
    except (ValueError, UnicodeDecodeError, RecursionError):
        raise DomainError(
            "Não foi possível ler os dados enviados.", code="invalid_json"
        ) from None
    if not isinstance(data, dict):
        raise DomainError("O pedido deve conter um objeto JSON.", code="invalid_json")
    missing = {
        field: ["Preenche este campo."] for field in required if field not in data
    }
    if missing:
        raise DomainError("Preenche os campos obrigatórios.", fields=missing)
    return data


def csrf_failure(request, reason=""):
    # O motivo técnico fica no logger do Django; a interface recebe uma instrução segura.
    return problem(
        DomainError(
            "A proteção da sessão foi atualizada. Tenta novamente.",
            code="csrf_failed",
            status=403,
        )
    )
