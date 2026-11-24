from abc import ABC, abstractmethod


class TokenService(ABC):
    @abstractmethod
    def issue(self, user_id: int) -> str: ...

    @abstractmethod
    def verify(self, token: str) -> int:
        pass
