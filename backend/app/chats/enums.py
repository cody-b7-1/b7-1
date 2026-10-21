import enum


class SenderRole(str, enum.Enum):
    USER = "USER"
    PHILOSOPHER = "PHILOSOPHER"
    SYSTEM = "SYSTEM"
