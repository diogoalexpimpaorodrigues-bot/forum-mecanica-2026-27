"""Evita guardar respostas da API em caches partilhadas ou no histórico HTTP.
Desenvolvido com auxílio de IA; ver AI_USAGE.md.
"""


class ApiCacheControlMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if request.path.startswith("/api/"):
            response["Cache-Control"] = "no-store"
        response["Content-Security-Policy"] = (
            "default-src 'self'; script-src 'self'; style-src 'self'; "
            "img-src 'self' data:; font-src 'self'; connect-src 'self'; "
            "form-action 'self'; frame-ancestors 'none'; base-uri 'self'; object-src 'none'"
        )
        response["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        return response
