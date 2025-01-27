import jwt
import uuid

from django.contrib.auth import get_user_model

from calendar import timegm
from datetime import datetime

from jwt import InvalidTokenError
from rest_framework_jwt.compat import get_username
from rest_framework_jwt.compat import get_username_field
from rest_framework_jwt.settings import api_settings

from project.users.models.deniedtokens import DeniedToken


def jwt_get_secret_key(payload=None):
    """
    For enhanced security you may want to use a secret key based on user.

    This way you have an option to logout only this user if:
        - token is compromised
        - password is changed
        - etc.
    """
    if api_settings.JWT_GET_USER_SECRET_KEY:
        User = get_user_model()  # noqa: N806
        user = User.objects.get(pk=payload.get("id"))
        key = str(api_settings.JWT_GET_USER_SECRET_KEY(user))
        return key
    return api_settings.JWT_SECRET_KEY


def jwt_payload_handler(user, orig_iat=None):
    username_field = get_username_field()
    username = get_username(user)

    payload = {
        "id": user.pk,
        "username": username,
        "exp": datetime.utcnow() + api_settings.JWT_EXPIRATION_DELTA,
    }
    if hasattr(user, "email"):
        payload["email"] = user.email
    if isinstance(user.pk, uuid.UUID):
        payload["id"] = str(user.pk)

    payload[username_field] = username

    # Include original issued at time for a brand new token,
    # to allow token refresh
    if api_settings.JWT_ALLOW_REFRESH:
        payload["orig_iat"] = orig_iat or timegm(datetime.utcnow().utctimetuple())

    if api_settings.JWT_AUDIENCE is not None:
        payload["aud"] = api_settings.JWT_AUDIENCE

    if api_settings.JWT_ISSUER is not None:
        payload["iss"] = api_settings.JWT_ISSUER

    return payload


def jwt_get_user_id_from_payload_handler(payload):
    """
    Override this function if user_id is formatted differently in payload
    """
    return payload.get("id")


def jwt_encode_handler(payload):
    key = api_settings.JWT_PRIVATE_KEY or jwt_get_secret_key(payload)
    return jwt.encode(payload, key, api_settings.JWT_ALGORITHM).decode("utf-8")


def jwt_decode_handler(token):
    options = {"verify_exp": api_settings.JWT_VERIFY_EXPIRATION}
    # get user from token, BEFORE verification, to get user secret key
    unverified_payload = jwt.decode(token, None, False)
    secret_key = jwt_get_secret_key(unverified_payload)
    verified_payload = jwt.decode(
        token,
        api_settings.JWT_PUBLIC_KEY or secret_key,
        api_settings.JWT_VERIFY,
        options=options,
        leeway=api_settings.JWT_LEEWAY,
        audience=api_settings.JWT_AUDIENCE,
        issuer=api_settings.JWT_ISSUER,
        algorithms=[api_settings.JWT_ALGORITHM],
    )
    User = get_user_model()  # noqa: N806
    user = User.objects.get(pk=verified_payload.get("id"))
    user_issued_at = timegm(user.issued_at.utctimetuple())
    if verified_payload.get('orig_iat') < user_issued_at:
        raise InvalidTokenError()
    try:
        if isinstance(token, bytes):
            token = token.decode()
        token_denied = user.denied_tokens.get(token=token)
        if token_denied:
            raise InvalidTokenError()
    except DeniedToken.DoesNotExist:
        return verified_payload




def jwt_response_payload_handler(token, user=None, request=None):
    """
    Returns the response data for both the login and refresh views.
    Override to return a custom response such as including the
    serialized representation of the User.
    """
    return {"token": token}
