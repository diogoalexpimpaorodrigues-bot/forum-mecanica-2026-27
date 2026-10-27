"""As contas da primeira versão também precisam de uma revisão coerente com o histórico."""

from django.db import migrations
from django.db.models import Count


def fill_revisions(apps, schema_editor):
    wallet_model = apps.get_model("core", "Wallet")
    alias = schema_editor.connection.alias
    for wallet in (
        wallet_model.objects.using(alias).annotate(total=Count("movements")).iterator()
    ):
        wallet_model.objects.using(alias).filter(pk=wallet.pk).update(
            revision=wallet.total
        )


class Migration(migrations.Migration):
    dependencies = [("core", "0003_wallet_revision_alter_requestbudget_started_at")]
    operations = [migrations.RunPython(fill_revisions, migrations.RunPython.noop)]
