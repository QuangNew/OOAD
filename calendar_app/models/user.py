from dataclasses import dataclass


@dataclass
class User:
    user_id: str
    full_name: str
    username: str = ""

    def get_user_id(self) -> str:
        return self.user_id
