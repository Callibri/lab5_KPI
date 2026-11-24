import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone

import jwt

from boxoffice.modules.core.application.ports import TokenService
from boxoffice.modules.core.domain.errors import AuthenticationError
from boxoffice.modules.core.domain.ports import PasswordHasher


class Pbkdf2PasswordHasher(PasswordHasher):
    def hash(self, raw_password: str) -> str:
        salt = secrets.token_bytes(16)
        digest = hashlib.pbkdf2_hmac("sha256", raw_password.encode(), salt, 100_000)
        return f"{salt.hex()}${digest.hex()}"

    def verify(self, raw_password: str, password_hash: str) -> bool:
        salt_hex, digest_hex = password_hash.split("$")
        digest = hashlib.pbkdf2_hmac("sha256", raw_password.encode(), bytes.fromhex(salt_hex), 100_000)
        return hmac.compare_digest(digest.hex(), digest_hex)


class JwtTokenService(TokenService):
    def __init__(self, secret_key: str, ttl_minutes: int = 60):
        self._secret, self._ttl = secret_key, ttl_minutes

    def issue(self, user_id: int) -> str:
        exp = datetime.now(timezone.utc) + timedelta(minutes=self._ttl)
        return jwt.encode({"sub": str(user_id), "exp": exp}, self._secret, algorithm="HS256")

    def verify(self, token: str) -> int:
        try:
            payload = jwt.decode(token, self._secret, algorithms=["HS256"])
            return int(payload["sub"])
        except (jwt.PyJWTError, KeyError, ValueError):
            raise AuthenticationError("Invalid or expired token")
