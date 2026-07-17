from __future__ import annotations

import json

from asgiref.sync import sync_to_async
from django.test import AsyncClient, TestCase
from django.urls import reverse
from rest_framework import status

from backend.tests.factories import UserFactory


class AccountNativeAsyncAPITests(TestCase):
    async def test_signin_endpoint_runs_through_django_async_client(self):
        user = await sync_to_async(UserFactory.create, thread_sensitive=True)()
        client = AsyncClient()

        response = await client.post(
            reverse("token_obtain_pair"),
            data=json.dumps(
                {
                    "username": user.username,
                    "password": UserFactory.DEFAULT_PASSWORD,
                }
            ),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        payload = response.json()
        self.assertIn("token", payload)
        self.assertIn("refreshToken", payload)
        self.assertIsInstance(payload["expirationTime"], int)
