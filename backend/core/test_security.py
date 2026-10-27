"""Casos adversos: não basta o percurso feliz para confiar numa API de contas."""

import json
from unittest.mock import patch

from django.contrib.auth.models import User
from django.db import IntegrityError, OperationalError, transaction
from django.test import Client, TestCase
from django.utils import timezone

from .errors import DomainError
from .models import Movement, RequestBudget, Wallet
from .services import claim_points, redeem_reward
from .throttling import consume


class SecurityTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("teste", password="Senha!Segura2099")
        self.wallet = Wallet.objects.create(user=self.user)
        self.client.force_login(self.user)

    def post(self, path, data):
        return self.client.post(
            f"/api/{path}/", json.dumps(data), content_type="application/json"
        )

    def test_all_endpoint_methods_return_json(self):
        for path in ["register", "login", "logout", "claim", "redeem"]:
            response = self.client.get(f"/api/{path}/")
            self.assertEqual(response.status_code, 405)
            self.assertEqual(response.json()["code"], "method_not_allowed")
            self.assertEqual(response["Allow"], "POST")

    def test_csrf_errors_are_json_and_do_not_mutate(self):
        secure = Client(enforce_csrf_checks=True)
        secure.force_login(self.user)
        response = secure.post(
            "/api/claim/",
            json.dumps({"id": "energia", "answer": 1}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json()["code"], "csrf_failed")
        self.assertEqual(Movement.objects.count(), 0)

    def test_wrong_origin_is_rejected_even_with_token(self):
        secure = Client(enforce_csrf_checks=True)
        secure.force_login(self.user)
        secure.get("/api/session/")
        response = secure.post(
            "/api/claim/",
            json.dumps({"id": "energia", "answer": 1}),
            content_type="application/json",
            HTTP_X_CSRFTOKEN=secure.cookies["csrftoken"].value,
            HTTP_ORIGIN="https://untrusted.example",
        )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(Movement.objects.count(), 0)

    def test_non_json_media_type_is_rejected(self):
        response = self.client.post("/api/claim/", {"id": "energia", "answer": 1})
        self.assertEqual(response.status_code, 415)
        self.assertEqual(response.json()["code"], "unsupported_media_type")

    def test_oversized_payload_returns_json_413(self):
        response = self.post(
            "claim", {"id": "energia", "answer": 1, "padding": "x" * 20000}
        )
        self.assertEqual(response.status_code, 413)
        self.assertEqual(response.json()["code"], "payload_too_large")

    def test_pathological_json_does_not_crash(self):
        for payload in [
            '{"id":"energia","answer":NaN}',
            "[" * 2000 + "0" + "]" * 2000,
            b"\xff\xfe",
            "true",
            "0",
            '"text"',
        ]:
            with self.subTest(payload=str(payload)[:30]):
                response = self.client.post(
                    "/api/claim/", payload, content_type="application/json"
                )
                self.assertEqual(response.status_code, 400)
                self.assertEqual(response.json()["code"], "invalid_json")

    def test_missing_fields_have_field_errors(self):
        response = self.post("register", {})
        self.assertEqual(
            set(response.json()["fields"]), {"username", "password", "confirmation"}
        )

    def test_confirmation_and_password_types_are_checked(self):
        for value in [None, True, {}, [], 12]:
            response = self.post(
                "register",
                {
                    "username": "outro",
                    "password": "Senha!Segura2099",
                    "confirmation": value,
                },
            )
            self.assertEqual(response.status_code, 400)
            self.assertIn("confirmation", response.json()["fields"])

    def test_normalization_is_consistent_on_registration_and_login(self):
        response = self.post(
            "register",
            {
                "username": "  nova_conta  ",
                "password": "Senha!Segura2099",
                "confirmation": "Senha!Segura2099",
            },
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["user"]["username"], "nova_conta")
        self.post("logout", {})
        self.assertEqual(
            self.post(
                "login", {"username": "  nova_conta  ", "password": "Senha!Segura2099"}
            ).status_code,
            200,
        )

    def test_html_cannot_be_a_username(self):
        response = self.post(
            "register",
            {
                "username": "<script>alert(1)</script>",
                "password": "Senha!Segura2099",
                "confirmation": "Senha!Segura2099",
            },
        )
        self.assertEqual(response.status_code, 400)

    def test_unknown_account_and_wrong_password_have_same_response(self):
        a = self.post("login", {"username": "teste", "password": "errada"})
        b = self.post("login", {"username": "inexistente", "password": "errada"})
        self.assertEqual(a.status_code, b.status_code)
        self.assertEqual(a.json(), b.json())

    def test_disabled_user_cannot_login(self):
        self.user.is_active = False
        self.user.save()
        self.assertEqual(
            self.post(
                "login", {"username": "teste", "password": "Senha!Segura2099"}
            ).status_code,
            401,
        )

    def test_logout_is_idempotent(self):
        self.assertEqual(self.post("logout", {}).json(), {"user": None})
        self.assertEqual(self.post("logout", {}).json(), {"user": None})

    def test_login_creates_missing_wallet_for_external_account(self):
        User.objects.create_user("externo", password="Senha!Segura2099")
        self.assertEqual(
            self.post(
                "login", {"username": "externo", "password": "Senha!Segura2099"}
            ).status_code,
            200,
        )
        self.assertEqual(Wallet.objects.get(user__username="externo").balance, 0)

    def test_duplicate_redemption_reports_duplicate_even_without_balance(self):
        claim_points(self.user, "energia", 1)
        redeem_reward(self.user, "autocolantes")
        response = self.post("redeem", {"id": "autocolantes"})
        self.assertEqual(response.json()["code"], "already_redeemed")
        self.wallet.refresh_from_db()
        self.assertEqual(self.wallet.balance, 0)

    def test_completed_challenge_reveals_learning_explanation(self):
        before = self.client.get("/api/session/").json()
        self.assertIsNone(before["challenges"][0]["explanation"])
        after = self.post("claim", {"id": "energia", "answer": 1}).json()
        self.assertIn("renovável", after["challenges"][0]["explanation"])
        self.assertEqual(after["spent"], 0)

    def test_failed_movement_insert_rolls_back_credit(self):
        with patch(
            "core.services.Movement.objects.create",
            side_effect=IntegrityError("simulated"),
        ):
            with self.assertRaises(DomainError):
                claim_points(self.user, "energia", 1)
        self.wallet.refresh_from_db()
        self.assertEqual(self.wallet.balance, 0)

    def test_failed_movement_insert_rolls_back_redemption(self):
        claim_points(self.user, "energia", 1)
        with patch(
            "core.services.Movement.objects.create",
            side_effect=IntegrityError("simulated"),
        ):
            with self.assertRaises(DomainError):
                redeem_reward(self.user, "autocolantes")
        self.wallet.refresh_from_db()
        self.assertEqual(self.wallet.balance, 80)
        self.assertEqual(Movement.objects.count(), 1)

    def test_database_rejects_negative_balance(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            Wallet.objects.filter(pk=self.wallet.pk).update(balance=-1)

    def test_database_rejects_wrong_movement_sign(self):
        for kind, amount in [
            ("credit", -1),
            ("redeem", 1),
            ("credit", 0),
            ("other", 4),
        ]:
            with (
                self.subTest(kind=kind, amount=amount),
                self.assertRaises(IntegrityError),
                transaction.atomic(),
            ):
                Movement.objects.create(
                    wallet=self.wallet,
                    kind=kind,
                    reference="fake",
                    title="Inválido",
                    amount=amount,
                )

    def test_busy_database_has_retry_after(self):
        with patch(
            "core.views.claim_points", side_effect=OperationalError("database locked")
        ):
            response = self.post("claim", {"id": "energia", "answer": 1})
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response["Retry-After"], "2")
        self.assertNotIn("locked", response.content.decode())

    def test_budget_includes_retry_after_and_hides_identifiers(self):
        consume("test", "private-ip", limit=1, seconds=60)
        with self.assertRaises(DomainError) as result:
            consume("test", "private-ip", limit=1, seconds=60)
        self.assertEqual(result.exception.status, 429)
        self.assertGreaterEqual(result.exception.retry_after, 1)
        self.assertNotIn("private-ip", RequestBudget.objects.get().key)

    def test_budget_resets_after_window(self):
        from datetime import timedelta

        consume("test", "private-ip", limit=1, seconds=60)
        RequestBudget.objects.update(started_at=timezone.now() - timedelta(seconds=61))
        consume("test", "private-ip", limit=1, seconds=60)
        self.assertEqual(RequestBudget.objects.get().used, 1)

    def test_forwarded_ip_header_cannot_bypass_budget(self):
        for index in range(5):
            response = self.client.post(
                "/api/login/",
                json.dumps({"username": "teste", "password": "errada"}),
                content_type="application/json",
                HTTP_X_FORWARDED_FOR=f"192.0.2.{index}",
            )
            self.assertEqual(response.status_code, 401)
        self.assertEqual(
            self.post("login", {"username": "teste", "password": "errada"}).status_code,
            429,
        )

    def test_session_rotates_on_login(self):
        old_key = self.client.session.session_key
        self.post("login", {"username": "teste", "password": "Senha!Segura2099"})
        # Django conserva a chave numa reautenticação da mesma conta. A entrada anónima roda-a.
        self.post("logout", {})
        session = self.client.session
        session["temporary"] = "value"
        session.save()
        anonymous_key = session.session_key
        self.post("login", {"username": "teste", "password": "Senha!Segura2099"})
        self.assertNotEqual(self.client.session.session_key, anonymous_key)
        self.assertNotEqual(self.client.session.session_key, old_key)

    def test_blank_password_is_not_a_valid_registration(self):
        response = self.post(
            "register",
            {"username": "espacos", "password": " " * 12, "confirmation": " " * 12},
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("password", response.json()["fields"])
        self.assertFalse(User.objects.filter(username="espacos").exists())

    def test_password_validator_explains_the_rule(self):
        from .validators import NotBlankPasswordValidator

        self.assertIn("espaços", NotBlankPasswordValidator().get_help_text())
        NotBlankPasswordValidator().validate("Uma palavra-passe com espaços!")

    def test_api_post_without_trailing_slash_does_not_crash(self):
        response = self.client.post(
            "/api/login",
            json.dumps({"username": "teste", "password": "errada"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["code"], "not_found")
