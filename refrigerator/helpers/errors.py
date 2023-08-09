from revolt.ext.commands import CheckError

class InsufficientBotPermissionsError(CheckError):
    """Raised when the bot does not have the required permissions to run a command

    Attributes
    -----------
    permissions: :class:`list[str]`
        The permissions which the bot did not have
    """

    def __init__(self, permissions: list[str]):
        self.permissions = permissions

class NotStaffError(CheckError):
    """Raised when the user is not staff"""
    pass

class NotBotManagerError(CheckError):
    """Raised when the user is not a bot manager"""
    pass
