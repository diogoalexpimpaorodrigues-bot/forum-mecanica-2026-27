"""Limpa apenas sessões expiradas e orçamentos de pedidos já sem utilidade."""

from datetime import timedelta

from django.core.management import BaseCommand, call_command
from django.utils import timezone

from core.models import RequestBudget


class Command(BaseCommand):
    help = "Remove sessões expiradas e contadores de pedidos com mais de um dia."

    def handle(self, *args, **options):
        deleted, _ = RequestBudget.objects.filter(
            started_at__lt=timezone.now() - timedelta(days=1)
        ).delete()
        call_command("clearsessions", verbosity=0)
        self.stdout.write(
            self.style.SUCCESS(
                f"Limpeza concluída: {deleted} contadores antigos removidos."
            )
        )
