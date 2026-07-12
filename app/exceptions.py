"""Pengecualian kustom untuk framework agen."""


class ToolError(Exception):
    """Dinaikkan bila sebuah alat gagal dieksekusi."""

    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


class TokenLimitExceeded(Exception):
    """Dinaikkan bila batas token input akan terlampaui."""

    pass
