"""Erros de domínio: mensagens seguras para a API, sem detalhes internos da base."""


class DomainError(Exception):
    def __init__(
        self,
        message,
        *,
        code="invalid_request",
        status=400,
        fields=None,
        retry_after=None,
    ):
        super().__init__(message)
        self.message = message
        self.code = code
        self.status = status
        self.fields = fields or {}
        self.retry_after = retry_after
