"""Sequências de operações e invariantes que têm de resistir a entradas repetidas."""

import io
import random
import tempfile
from copy import deepcopy
from datetime import timedelta
from pathlib import Path
from unittest.mock import patch

from django.conf import settings
from django.contrib.auth.models import User
from django.core.management import call_command
from django.db import IntegrityError
from django.test import TestCase, override_settings
from django.utils import timezone

from .catalog import CHALLENGES, REWARDS
from .errors import DomainError
from .models import Movement, RequestBudget, Wallet
from .services import claim_points, redeem_reward, snapshot


class InvariantTests(TestCase):
    def test_random_sequences_reconcile_with_independent_ledger(self):
        for seed in range(20):
            rng = random.Random(seed)
            user = User.objects.create_user(f"participant_{seed}")
            Wallet.objects.create(user=user)
            balance, claimed, redeemed, expected = 0, set(), set(), []
            for _ in range(100):
                if rng.random() < 0.6:
                    challenge = rng.choice(CHALLENGES)
                    correct = rng.random() < 0.8
                    answer = (
                        challenge["answer"]
                        if correct
                        else (challenge["answer"] + 1) % len(challenge["options"])
                    )
                    allowed = correct and challenge["id"] not in claimed
                    try:
                        claim_points(user, challenge["id"], answer)
                        self.assertTrue(allowed, (seed, challenge))
                        balance += challenge["points"]
                        claimed.add(challenge["id"])
                        expected.append(
                            ("credit", challenge["id"], challenge["points"])
                        )
                    except DomainError as error:
                        self.assertFalse(allowed)
                        self.assertEqual(
                            error.code,
                            "incorrect_answer" if not correct else "already_completed",
                        )
                else:
                    reward = rng.choice(REWARDS)
                    allowed = reward["id"] not in redeemed and balance >= reward["cost"]
                    try:
                        redeem_reward(user, reward["id"])
                        self.assertTrue(allowed, (seed, reward))
                        balance -= reward["cost"]
                        redeemed.add(reward["id"])
                        expected.append(("redeem", reward["id"], -reward["cost"]))
                    except DomainError as error:
                        self.assertFalse(allowed)
                        self.assertEqual(
                            error.code,
                            "already_redeemed"
                            if reward["id"] in redeemed
                            else "insufficient_balance",
                        )
                actual = snapshot(user)
                self.assertEqual(actual["balance"], balance)
                self.assertEqual(actual["revision"], len(expected))
                self.assertGreaterEqual(balance, 0)
                self.assertCountEqual(
                    [
                        (m["kind"], m["reference"], m["amount"])
                        for m in actual["movements"]
                    ],
                    expected,
                )

    def test_expected_account_mismatch_never_mutates_wallet(self):
        user = User.objects.create_user("conta_atual")
        wallet = Wallet.objects.create(user=user, balance=300)
        self.client.force_login(user)
        import json

        for action, fields in [
            ("claim", {"id": "energia", "answer": 1}),
            ("redeem", {"id": "caderno"}),
        ]:
            response = self.client.post(
                f"/api/{action}/",
                json.dumps(fields | {"expected_user": "outra_conta"}),
                content_type="application/json",
            )
            self.assertEqual(response.status_code, 409)
            self.assertEqual(response.json()["code"], "account_changed")
        wallet.refresh_from_db()
        self.assertEqual(wallet.balance, 300)
        self.assertFalse(Movement.objects.filter(wallet=wallet).exists())

    def test_unsuccessful_operations_do_not_advance_revision(self):
        user = User.objects.create_user("revisoes")
        Wallet.objects.create(user=user)
        with self.assertRaises(DomainError):
            redeem_reward(user, "garrafa")
        self.assertEqual(snapshot(user)["revision"], 0)
        claim_points(user, "energia", 1)
        with self.assertRaises(DomainError):
            claim_points(user, "energia", 1)
        self.assertEqual(snapshot(user)["revision"], 1)

    def test_insufficient_balance_has_specific_error(self):
        user = User.objects.create_user("sem_pontos")
        Wallet.objects.create(user=user)
        self.client.force_login(user)
        import json

        response = self.client.post(
            "/api/redeem/",
            json.dumps({"id": "garrafa"}),
            content_type="application/json",
        )
        self.assertEqual(response.json()["code"], "insufficient_balance")

    def test_non_string_identifiers_are_domain_errors(self):
        user = User.objects.create_user("identificadores")
        Wallet.objects.create(user=user)
        for identifier in [None, True, 42, [], {}]:
            with (
                self.subTest(identifier=identifier),
                self.assertRaises(DomainError) as raised,
            ):
                claim_points(user, identifier, 0)
            self.assertEqual(raised.exception.code, "invalid_identifier")

    def test_registration_race_returns_field_error(self):
        import json

        with patch(
            "core.views.RegistrationForm.save",
            side_effect=IntegrityError("simulated concurrent registration"),
        ):
            response = self.client.post(
                "/api/register/",
                json.dumps(
                    {
                        "username": "nova",
                        "password": "Bastante!Segura2099",
                        "confirmation": "Bastante!Segura2099",
                    }
                ),
                content_type="application/json",
            )
        self.assertEqual(response.status_code, 409)
        self.assertIn("username", response.json()["fields"])
        self.assertFalse(User.objects.filter(username="nova").exists())

    def test_cleanup_keeps_active_counters_and_all_accounts(self):
        now = timezone.now()
        RequestBudget.objects.create(
            key="old", used=5, started_at=now - timedelta(days=2)
        )
        RequestBudget.objects.create(key="current", used=3, started_at=now)
        user = User.objects.create_user("preservada")
        call_command("cleanup_expired", stdout=io.StringIO())
        self.assertEqual(
            list(RequestBudget.objects.values_list("key", flat=True)), ["current"]
        )
        self.assertTrue(User.objects.filter(pk=user.pk).exists())

    def test_rebuilt_frontend_does_not_use_cached_index(self):
        with tempfile.TemporaryDirectory() as directory:
            template = Path(directory) / "index.html"
            config = deepcopy(settings.TEMPLATES)
            config[0]["DIRS"] = [directory]
            with override_settings(TEMPLATES=config):
                template.write_text("primeira-compilacao")
                self.assertContains(self.client.get("/"), "primeira-compilacao")
                template.write_text("segunda-compilacao")
                self.assertContains(self.client.get("/"), "segunda-compilacao")

    def test_assets_cannot_expose_backend_files(self):
        for url in [
            "/assets/../backend/manage.py",
            "/assets/%2e%2e/manage.py",
            "/assets/../../db.sqlite3",
        ]:
            response = self.client.get(url)
            self.assertIn(response.status_code, [400, 404])
            self.assertNotIn(b"execute_from_command_line", response.content)
