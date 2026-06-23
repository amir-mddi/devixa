from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.db import models
from django.utils.timezone import now

from dealio.apps.core_models.entities.base.base import BaseModel


class Access(BaseModel):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return f"{self.name}"


class Role(BaseModel):
    name = models.CharField(max_length=20, unique=True)
    accesses = models.ManyToManyField('Access', related_name='access_roles', null=False, default=None)
    symbol = models.CharField(max_length=20, unique=True, null=True)

    def __str__(self):
        return f"{self.name}"


class CustomUser(BaseModel, AbstractUser):
    phone_number = models.CharField(
        max_length=11,
        validators=[
            RegexValidator(
                regex='^09[0-9]{9}$',
                message='phone number must be digit and start with 09.........',
                code='invalid_phone_number'
            ),
        ],
        unique=True
    )
    role = models.ForeignKey(Role,
                             related_name='user_role',
                             on_delete=models.PROTECT
                             )
    email_verified = models.BooleanField(default=False)
    phone_number_verified = models.BooleanField(default=False)
    is_service_user = models.BooleanField(default=False)

    # def save(self, *args, **kwargs):
    #     try:
    #         role = Role.objects.get(symbol="user")
    #     except Role.DoesNotExist:
    #         raise Exception("Role Not Found")
    #     self.role = role
    #     super().save(*args, **kwargs)

class TokenBlacklist(BaseModel):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    token = models.CharField(max_length=255)
    refresh = models.CharField(max_length=255, default='')

    def __str__(self):
        return f'TokenBlacklist for User: {self.user.username}'
