from datetime import datetime

from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from project.models import BaseModel


class User(BaseModel, AbstractUser):
    """User model.

    Extend from Django's Abstract User, change the username field
    to email and add some extra fields.
    """

    email = models.EmailField(
        "email address",
        unique=True,
        error_messages={"unique": "A user with that email already exists."},
    )

    phone_regex = RegexValidator(
        regex=r"\+?1?\d{9,15}$",
        message="Phone number must be entered in the format: +999999999. Up to 15 digits allowed.",
    )
    phone_number = models.CharField(
        validators=[phone_regex], max_length=17, blank=True
    )

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    is_client = models.BooleanField(
        "client",
        default=True,
        help_text=(
            "Help easily distinguish users and perform queries. "
            "Clients are the main type of user."
        ),
    )

    is_verified = models.BooleanField(
        "verified",
        default=True,
        help_text="Set to true when the user have verified its email address.",
    )

    issued_at = models.DateTimeField(
        "issued at",
        auto_now_add=True,
        help_text="Date time after wich tokens are valid .",
    )

    class Meta:
        db_table = "users"

    def __str__(self):
        """Return username."""
        return self.username

    def get_short_name(self):
        """Return username."""
        return self.username
