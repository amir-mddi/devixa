from django.test import TestCase
from django.urls import reverse

from dealio.tests.factories import RoleFactory, UserFactory


class AdminPanelAccessTests(TestCase):
    def setUp(self):
        self.admin_role = RoleFactory.create(name="ادمین", symbol="admin")
        self.user_role = RoleFactory.create(name="کاربر", symbol="user")

    def test_anonymous_user_is_redirected_to_login(self):
        response = self.client.get(reverse("admin_panel:dashboard"))

        self.assertEqual(response.status_code, 302)
        self.assertIn("/login/", response.url)

    def test_normal_user_cannot_open_management_panel(self):
        user = UserFactory.create(role=self.user_role)
        self.client.force_login(user)

        response = self.client.get(reverse("admin_panel:dashboard"))

        self.assertEqual(response.status_code, 403)

    def test_admin_role_can_open_management_panel_without_django_staff_flag(self):
        admin = UserFactory.create(
            role=self.admin_role,
            is_staff=False,
            is_superuser=False,
        )
        self.client.force_login(admin)

        response = self.client.get(reverse("admin_panel:dashboard"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "داشبورد مدیریت")
        self.assertContains(response, "روبیکا")

    def test_admin_can_render_all_management_index_and_create_pages(self):
        admin = UserFactory.create(role=self.admin_role)
        self.client.force_login(admin)
        route_names = (
            "admin_panel:dashboard",
            "admin_panel:tickets",
            "admin_panel:reviews",
            "admin_panel:billing",
            "admin_panel:users",
            "admin_panel:user_create",
            "admin_panel:courses",
            "admin_panel:course_create",
            "admin_panel:discounts",
            "admin_panel:notifications",
            "admin_panel:bot_settings",
        )

        for route_name in route_names:
            with self.subTest(route_name=route_name):
                response = self.client.get(reverse(route_name))
                self.assertEqual(response.status_code, 200)
