class DomainError(Exception):
    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class NotFoundError(DomainError):
    def __init__(self, resource: str = "Resource"):
        super().__init__(f"{resource} not found", status_code=404)


class UnauthorizedError(DomainError):
    def __init__(self, message: str = "Unauthorized"):
        super().__init__(message, status_code=401)


class ForbiddenError(DomainError):
    def __init__(self, message: str = "Access denied"):
        super().__init__(message, status_code=403)


class ConflictError(DomainError):
    def __init__(self, message: str = "Resource already exists"):
        super().__init__(message, status_code=409)
