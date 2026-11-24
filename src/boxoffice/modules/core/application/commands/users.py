from dataclasses import dataclass

from boxoffice.modules.core.contract.events import UserRegistered
from boxoffice.modules.core.application.side_effects import SideEffects
from boxoffice.modules.core.domain.factories import UserFactory
from boxoffice.modules.core.domain.repositories import UserRepository


@dataclass(frozen=True)
class RegisterUserCommand:
    email: str
    password: str


class RegisterUserHandler:
    def __init__(self, factory: UserFactory, users: UserRepository, effects: SideEffects | None = None):
        self._factory, self._users = factory, users
        self._effects = effects or SideEffects()

    def handle(self, cmd: RegisterUserCommand) -> int:
        user = self._users.add(self._factory.create(cmd.email, cmd.password))
        self._effects.emit(UserRegistered(user_id=user.id, email=user.email.value))
        return user.id
