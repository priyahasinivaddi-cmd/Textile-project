from app.utils.auth import create_access_token, create_refresh_token, verify_access_token, verify_refresh_token


def test_access_and_refresh_tokens_are_not_interchangeable():
    claims = {"sub": "operator@example.test", "uid": 7, "role": "operator"}
    access = create_access_token(claims)
    refresh = create_refresh_token(claims)
    assert verify_access_token(access)["uid"] == 7
    assert verify_refresh_token(refresh)["uid"] == 7
    assert verify_access_token(refresh) is None
    assert verify_refresh_token(access) is None
