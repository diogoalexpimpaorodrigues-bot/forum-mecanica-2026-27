"""Simula a atualização de uma instalação da versão inicial, com contas e pontos reais."""

from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import User
from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.test import TransactionTestCase

from .services import snapshot


class UpgradeTests(TransactionTestCase):
    def tearDown(self):
        # Mesmo se uma asserção falhar, os testes seguintes recebem o esquema atual.
        executor = MigrationExecutor(connection)
        executor.migrate(executor.loader.graph.leaf_nodes())
        super().tearDown()

    def test_v1_account_and_history_survive_upgrade(self):
        before = ("core", "0001_initial")
        after = ("core", "0004_backfill_wallet_revision")
        executor = MigrationExecutor(connection)
        executor.migrate([before])
        old = executor.loader.project_state([before]).apps
        old_user = old.get_model("auth", "User").objects.create(
            username="conta_antiga", password=make_password("Senha!Antiga2026")
        )
        wallet = old.get_model("core", "Wallet").objects.create(
            user_id=old_user.pk, balance=100
        )
        movement = old.get_model("core", "Movement")
        movement.objects.create(
            wallet_id=wallet.pk,
            kind="credit",
            reference="energia",
            title="Energia em movimento",
            amount=80,
        )
        movement.objects.create(
            wallet_id=wallet.pk,
            kind="credit",
            reference="mecanica",
            title="O essencial da mecânica",
            amount=100,
        )
        redemption = movement.objects.create(
            wallet_id=wallet.pk,
            kind="redeem",
            reference="autocolantes",
            title="Pack de autocolantes",
            amount=-80,
        )
        code = str(redemption.code)
        executor = MigrationExecutor(connection)
        executor.migrate([after])
        user = User.objects.get(username="conta_antiga")
        self.assertTrue(user.check_password("Senha!Antiga2026"))
        state = snapshot(user)
        self.assertEqual(state["balance"], 100)
        self.assertEqual(state["revision"], 3)
        self.assertEqual(state["earned"], 180)
        self.assertEqual(state["spent"], 80)
        self.assertEqual(len(state["movements"]), 3)
        self.assertEqual(
            next(m["code"] for m in state["movements"] if m["kind"] == "redeem"), code
        )
