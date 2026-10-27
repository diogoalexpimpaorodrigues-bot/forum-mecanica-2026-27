"""Testes de regras e segurança, com clientes HTTP e uma base de dados isolada."""

import json
from datetime import timedelta

from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.utils import timezone

from .models import Movement, RequestBudget, Wallet


class PassportTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("invento", password="Uma!SenhaSegura2926")
        self.wallet = Wallet.objects.create(user=self.user)

    def post(self, path, data, client=None):
        return (client or self.client).post(
            "/api/" + path + "/", json.dumps(data), content_type="application/json"
        )

    def auth(self):
        self.client.force_login(self.user)

    def credit(self, id="energia", answer=1):
        return self.post("claim", {"id": id, "answer": answer})

    def test_public_session_has_no_user(self):
        self.assertEqual(self.client.get("/api/session/").json(), {"user": None})

    def test_register_creates_wallet_hashes_password_and_logs_in(self):
        response = self.post(
            "register",
            {
                "username": "novo",
                "password": "Uma!SenhaSegura2926",
                "confirmation": "Uma!SenhaSegura2926",
            },
        )
        self.assertEqual(response.status_code, 201)
        user = User.objects.get(username="novo")
        self.assertTrue(user.check_password("Uma!SenhaSegura2926"))
        self.assertNotEqual(user.password, "Uma!SenhaSegura2926")
        self.assertEqual(response.json()["balance"], 0)
        self.assertEqual(
            self.client.get("/api/session/").json()["user"]["username"], "novo"
        )
        self.assertEqual(user.email, "")

    def test_registration_validation(self):
        cases = [
            dict(
                username="invento",
                password="Forte!Senha98765",
                confirmation="Forte!Senha98765",
            ),
            dict(
                username="in válido",
                password="Forte!Senha98765",
                confirmation="Forte!Senha98765",
            ),
            dict(username="novo", password="123", confirmation="123"),
            dict(username="novo", password="Forte!Senha98765", confirmation="outra"),
            dict(
                username="x" * 31,
                password="Forte!Senha98765",
                confirmation="Forte!Senha98765",
            ),
        ]
        for data in cases:
            with self.subTest(data=data):
                self.assertEqual(self.post("register", data).status_code, 400)
        self.assertEqual(User.objects.count(), 1)

    def test_login_logout_and_persistence(self):
        self.assertEqual(
            self.post(
                "login", {"username": "invento", "password": "errada"}
            ).status_code,
            401,
        )
        self.assertEqual(
            self.post(
                "login", {"username": "invento", "password": "Uma!SenhaSegura2926"}
            ).status_code,
            200,
        )
        self.credit()
        self.assertEqual(self.post("logout", {}).status_code, 200)
        self.assertIsNone(self.client.get("/api/session/").json()["user"])
        self.post("login", {"username": "invento", "password": "Uma!SenhaSegura2926"})
        self.assertEqual(self.client.get("/api/session/").json()["balance"], 80)

    def test_rate_limit_and_expiry(self):
        for _ in range(5):
            self.assertEqual(
                self.post(
                    "login", {"username": "invento", "password": "errada"}
                ).status_code,
                401,
            )
        self.assertEqual(
            self.post(
                "login", {"username": "invento", "password": "Uma!SenhaSegura2926"}
            ).status_code,
            429,
        )
        RequestBudget.objects.update(started_at=timezone.now() - timedelta(minutes=11))
        self.assertEqual(
            self.post(
                "login", {"username": "invento", "password": "Uma!SenhaSegura2926"}
            ).status_code,
            200,
        )

    def test_requires_authentication(self):
        for action in ["claim", "redeem"]:
            self.assertEqual(self.post(action, {}).status_code, 401)

    def test_csrf_enforced_on_every_mutation(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.user)
        for action in ["register", "login", "logout", "claim", "redeem"]:
            self.assertEqual(self.post(action, {}, client).status_code, 403)
        client.get("/api/session/")
        response = client.post(
            "/api/claim/",
            json.dumps({"id": "energia", "answer": 1}),
            content_type="application/json",
            HTTP_X_CSRFTOKEN=client.cookies["csrftoken"].value,
        )
        self.assertEqual(response.status_code, 200)

    def test_wrong_answer_has_no_credit(self):
        self.auth()
        self.assertEqual(self.credit(answer=0).status_code, 400)
        self.wallet.refresh_from_db()
        self.assertEqual(self.wallet.balance, 0)
        self.assertEqual(Movement.objects.count(), 0)

    def test_credit_once_and_rollback_duplicate(self):
        self.auth()
        self.assertEqual(self.credit().json()["balance"], 80)
        self.assertEqual(self.credit().status_code, 409)
        self.wallet.refresh_from_db()
        self.assertEqual(self.wallet.balance, 80)
        self.assertEqual(Movement.objects.count(), 1)

    def test_server_ignores_client_points(self):
        self.auth()
        response = self.post(
            "claim", {"id": "energia", "answer": 1, "points": 999999, "user_id": 123}
        )
        self.assertEqual(response.json()["balance"], 80)

    def test_redeem_debits_and_returns_code(self):
        self.auth()
        self.credit()
        response = self.post("redeem", {"id": "autocolantes", "cost": 0})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["balance"], 0)
        self.assertTrue(response.json()["movements"][0]["code"])

    def test_insufficient_balance_changes_nothing(self):
        self.auth()
        self.assertEqual(self.post("redeem", {"id": "garrafa"}).status_code, 409)
        self.assertEqual(Movement.objects.count(), 0)
        self.wallet.refresh_from_db()
        self.assertEqual(self.wallet.balance, 0)

    def test_duplicate_redemption_rolls_back(self):
        self.auth()
        self.credit()
        self.credit("mecanica", 2)
        self.post("redeem", {"id": "autocolantes"})
        self.assertEqual(self.post("redeem", {"id": "autocolantes"}).status_code, 409)
        self.wallet.refresh_from_db()
        self.assertEqual(self.wallet.balance, 100)
        self.assertEqual(Movement.objects.filter(kind="redeem").count(), 1)

    def test_account_isolation(self):
        self.auth()
        self.credit()
        other = User.objects.create_user("outro", password="Uma!SenhaSegura2926")
        Wallet.objects.create(user=other)
        self.client.force_login(other)
        data = self.client.get("/api/session/").json()
        self.assertEqual(data["balance"], 0)
        self.assertEqual(data["movements"], [])
        self.assertFalse(any(c["completed"] for c in data["challenges"]))

    def test_bad_payloads(self):
        self.auth()
        for action in ["register", "login", "claim", "redeem"]:
            for payload in ["{", "[]", "null"]:
                with self.subTest(action=action, payload=payload):
                    self.assertEqual(
                        self.client.post(
                            "/api/" + action + "/",
                            payload,
                            content_type="application/json",
                        ).status_code,
                        400,
                    )
        self.assertEqual(self.credit(answer=True).status_code, 400)
        self.assertEqual(
            self.post("claim", {"id": "fake", "answer": 0}).status_code, 404
        )
        self.assertEqual(self.post("redeem", {"id": "fake"}).status_code, 404)

    def test_no_answers_in_catalog(self):
        self.auth()
        challenge = self.client.get("/api/session/").json()["challenges"][0]
        self.assertNotIn("answer", challenge)
        self.assertIsNone(challenge["explanation"])

    def test_get_cannot_mutate(self):
        self.auth()
        for path in ["login", "logout", "register", "claim", "redeem"]:
            self.assertEqual(self.client.get("/api/" + path + "/").status_code, 405)

    def test_unknown_api_is_json_404(self):
        self.assertEqual(self.client.get("/api/missing/").status_code, 404)
        self.assertIn("error", self.client.get("/api/missing/").json())

    def test_api_responses_are_not_cached(self):
        self.auth()
        self.assertEqual(self.client.get("/api/session/")["Cache-Control"], "no-store")
        self.assertEqual(self.credit()["Cache-Control"], "no-store")
