from datetime import datetime, timedelta

import pytest
import json
import jwt
from django.conf import settings
from django.test import Client
from django.urls import reverse
from rest_framework import status
from project.users.models.users import User
from constants import PASSWORD, EMAIL, USERNAME, FIRST_NAME, LAST_NAME
import time


@pytest.mark.django_db
def test_user_login(create_user):
    c = Client()

    response = c.post(
        reverse("users-login"),
        content_type="application/json",
        data=json.dumps({"email": EMAIL, "password": PASSWORD}),
    )

    assert response.status_code == status.HTTP_200_OK
    assert "token" in response.json()


@pytest.mark.django_db
def test_user_login__invalid_credentials(create_user):
    c = Client()

    response = c.post(
        reverse("users-login"),
        content_type="application/json",
        data=json.dumps({"email": EMAIL, "password": "wrongpassword123"}),
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_user_login__check_token(login_user):
    token = login_user
    decoded_token = jwt.decode(
        token, settings.JWT_AUTH["JWT_SECRET_KEY"], algorithms=["HS256"]
    )
    assert decoded_token["email"] == EMAIL
    assert decoded_token["id"] == str(User.objects.get(email=EMAIL).id)


@pytest.mark.django_db
def test_user_retrieve(create_user, login_user):
    token = "JWT " + login_user
    user_id = create_user["id"]

    c = Client(HTTP_AUTHORIZATION=token)

    response = c.get(
        reverse("users-detail", kwargs={"pk": user_id}),
        content_type="application/json",
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["id"] == user_id
    assert response.json()["email"] == EMAIL


@pytest.mark.django_db
def test_user_retrieve__unauthorised(create_user):
    user_id = create_user["id"]

    c = Client()

    response = c.get(
        reverse("users-detail", kwargs={"pk": user_id}),
        content_type="application/json",
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
def test_user_update(create_user, login_user):
    token = "JWT " + login_user
    c = Client(HTTP_AUTHORIZATION=token)

    response = c.patch(
        reverse("users-detail", kwargs={"pk": create_user["id"]}),
        content_type="application/json",
        data=json.dumps({"email": "new_email@marcosaguayo.com"}),
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["email"] == "new_email@marcosaguayo.com"


@pytest.mark.django_db
def test_user_update__unauthorised(create_user):
    c = Client()
    response = c.patch(
        reverse("users-detail", kwargs={"pk": create_user["id"]}),
        content_type="application/json",
        data=json.dumps({"email": "new_email@marcosaguayo.com"}),
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
def test_profile_user_update(create_user, login_user):
    token = "JWT " + login_user
    c = Client(HTTP_AUTHORIZATION=token)
    biography = "Hello World!"

    response = c.patch(
        reverse("users-profile", kwargs={"pk": create_user["id"]}),
        content_type="application/json",
        data=json.dumps({"biography": biography}),
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["profile"]["biography"] == biography


@pytest.mark.django_db
def test_profile_user_update__unauthorised(create_user):
    c = Client()
    response = c.patch(
        reverse("users-profile", kwargs={"pk": create_user["id"]}),
        content_type="application/json",
        data=json.dumps({"biography": "Hello World!"}),
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
def test_user_token__check(create_user):
    c = Client()
    response = c.post(
        reverse("users-login"),
        content_type="application/json",
        data=json.dumps({"email": EMAIL, "password": PASSWORD}),
    )
    token = response.json()["token"]

    response = c.post(
        reverse("users-token-verify"),
        content_type="application/json",
        data=json.dumps({"token": token}),
    )

    assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
def test_user_token__check__invalid(create_user):
    invalid_token = (
        "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmF"
        "tZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJ"
        "f36POk6yJV_adQssw5c"
    )

    c = Client()
    response = c.post(
        reverse("users-token-verify"),
        content_type="application/json",
        data=json.dumps({"token": invalid_token}),
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_user_token__refresh(create_user):
    c = Client()
    response = c.post(
        reverse("users-login"),
        content_type="application/json",
        data=json.dumps({"email": EMAIL, "password": PASSWORD}),
    )
    token = response.json()["token"]

    response = c.post(
        reverse("users-token-refresh"),
        content_type="application/json",
        data=json.dumps({"token": token}),
    )

    assert response.status_code == status.HTTP_200_OK


# TODO: improve test, monkeypatch datetime
@pytest.mark.django_db
def test_user_token__expiry_refresh__invalid(create_user):
    c = Client()
    response = c.post(
        reverse("users-login"),
        content_type="application/json",
        data=json.dumps({"email": EMAIL, "password": PASSWORD}),
    )
    token = response.json()["token"]

    time.sleep(5)
    response = c.post(
        reverse("users-token-refresh"),
        content_type="application/json",
        data=json.dumps({"token": token}),
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST


# TODO: improve test, monkeypatch datetime
@pytest.mark.django_db
def test_user_token__infinite_refresh__invalid(create_user):
    c = Client()
    response = c.post(
        reverse("users-login"),
        content_type="application/json",
        data=json.dumps({"email": EMAIL, "password": PASSWORD}),
    )
    token = response.json()["token"]
    for _ in range(3):
        time.sleep(2)
        response = c.post(
            reverse("users-token-refresh"),
            content_type="application/json",
            data=json.dumps({"token": token}),
        )
        token = response.json()["token"]
    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_user_token__issued_at_revoke__invalid(create_user, login_user):
    token = "JWT " + login_user
    c = Client(HTTP_AUTHORIZATION=token)

    jwt_revocation_dt = datetime.utcnow() + timedelta(days=1)
    _ = c.patch(
        reverse("users-detail", kwargs={"pk": create_user["id"]}),
        content_type="application/json",
        data=json.dumps({"issued_at": jwt_revocation_dt.strftime('%Y-%m-%d %H:%M:%S%z')}),
    )

    response = c.post(
        reverse("users-token-verify"),
        content_type="application/json",
        data=json.dumps({"token": token}),
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_user_token__deny(create_user, login_user):
    c = Client(HTTP_AUTHORIZATION="JWT " + login_user)

    response = c.post(
        reverse("users-token-deny"),
        content_type="application/json",
        data=json.dumps({"token": login_user}),
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.json()['denied_token'] == login_user


@pytest.mark.django_db
def test_user_token__deny(create_user, login_user):
    c = Client(HTTP_AUTHORIZATION="JWT " + login_user)

    response = c.post(
        reverse("users-token-deny"),
        content_type="application/json",
        data=json.dumps({"token": login_user}),
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.json()['denied_token'] == login_user


@pytest.mark.django_db
def test_user_retrieve__denied_token__unauthorized(create_user, login_user, deny_token):
    c = Client(HTTP_AUTHORIZATION=deny_token)

    response = c.get(
        reverse("users-detail", kwargs={"pk": create_user["id"]}),
        content_type="application/json",
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
