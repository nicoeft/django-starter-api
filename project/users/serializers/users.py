from datetime import datetime

import jwt
from django.conf import settings
from django.contrib.auth import password_validation, authenticate
from django.core.validators import RegexValidator
from rest_framework import serializers
from rest_framework.validators import UniqueValidator
from rest_framework_jwt.settings import api_settings
from project.users.models import User, Profile
from project.users.models.deniedtokens import DeniedToken
from project.users.serializers.profiles import ProfileModelSerializer

jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER
jwt_decode_handler = api_settings.JWT_DECODE_HANDLER


class UserModelSerializer(serializers.ModelSerializer):
    profile = ProfileModelSerializer(read_only=True)

    class Meta:
        model = User
        fields = (
            "id",
            "username",
            "first_name",
            "last_name",
            "email",
            "phone_number",
            "profile",
        )


class UserSignUpSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    email = serializers.EmailField(
        validators=[UniqueValidator(queryset=User.objects.all())]
    )
    username = serializers.CharField(
        validators=[UniqueValidator(queryset=User.objects.all())]
    )

    phone_regex = RegexValidator(
        regex=r"\+?1?\d{9,15}$",
        message="Phone number must be entered in the format: +999999999. Up to 15 digits allowed.",
    )
    phone_number = serializers.CharField(
        validators=[phone_regex], required=False
    )
    password = serializers.CharField(min_length=8, max_length=64)
    password_confirmation = serializers.CharField(min_length=8, max_length=64)
    first_name = serializers.CharField(
        min_length=2, max_length=30, required=False
    )
    last_name = serializers.CharField(
        min_length=2, max_length=30, required=False
    )

    def validate(self, data):
        """Verify passwords match."""
        passwd = data["password"]
        passwd_conf = data["password_confirmation"]
        if passwd != passwd_conf:
            raise serializers.ValidationError("Passwords don't match.")
        password_validation.validate_password(passwd)
        return data

    def create(self, data):
        """Handle user and profile creation."""
        data.pop("password_confirmation")
        user = User.objects.create_user(
            **data, is_verified=False, is_client=True
        )
        Profile.objects.create(user=user)
        return user


class UserLoginSerializer(serializers.Serializer):
    """User login serializer.

    Handle the login request data.
    """

    email = serializers.EmailField()
    password = serializers.CharField(min_length=8, max_length=64)

    def validate(self, data):
        """Check credentials."""
        user = authenticate(email=data["email"], password=data["password"])

        if not user:
            raise serializers.ValidationError(
                "Unable to log in with provided credentials."
            )

        if not user.is_active:
            raise serializers.ValidationError("User account is disabled.")

        self.context["user"] = user

        return data

    def create(self, data):
        """Handle user and profile creation."""
        user = self.context["user"]
        payload = jwt_payload_handler(user)
        return jwt_encode_handler(payload)


class TokenSerialiser(serializers.Serializer):
    token = serializers.CharField()

    def validate_token(self, data):
        try:
            payload = jwt_decode_handler(data)
        except jwt.ExpiredSignatureError:
            raise serializers.ValidationError("Verification link has expired.")
        except jwt.PyJWTError:
            raise serializers.ValidationError("Invalid token")
        self.validate_refresh(payload)
        self.context["payload"] = payload
        self.context["token"] = data
        return data

    def validate_refresh(self, payload):
        is_refresh_token = self.context.get("is_refresh_token", False)
        if api_settings.JWT_ALLOW_REFRESH and is_refresh_token:
            orig_iat_dt = datetime.utcfromtimestamp(payload.get('orig_iat'))
            refresh_expiry_dt = orig_iat_dt + api_settings.JWT_REFRESH_EXPIRATION_DELTA
            if refresh_expiry_dt <= datetime.utcnow():
                raise serializers.ValidationError("Refresh token expired")

    def save(self):
        payload = self.context["payload"]
        user = User.objects.get(email=payload["email"])
        return jwt_encode_handler(jwt_payload_handler(user, payload.get('orig_iat')))

    def deny(self):
        payload = self.context["payload"]
        token = self.context["token"]
        denied_token, _ = DeniedToken.objects.get_or_create(user_id=payload["id"], token=token)
        return denied_token.token
