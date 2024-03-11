from fastapi import HTTPException, status


def get_user_not_found_exception():
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="User not found",
        headers={"WWW-Authenticate": "Bearer"},
    )


def get_incorrect_credentials_exception():
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Incorrect email/login or password",
        headers={"WWW-Authenticate": "Bearer"},
    )


def get_token_validation_exception():
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )


def get_user_already_exists(detail: str = "User with this email/login already exists"):
    return HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail=detail,
    )


def get_database_error_exception():
    return HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Database operation failed",
    )
