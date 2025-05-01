import hashlib
from datetime import timedelta, datetime, UTC

import jwt
from fastapi import Depends, HTTPException, status, Request, Cookie
from fastapi.security import OAuth2PasswordBearer, HTTPBearer, \
    HTTPAuthorizationCredentials
from jwt import ExpiredSignatureError, DecodeError
from sqlalchemy.ext.asyncio import AsyncSession

from app import schemas
from app.config import settings
from app.crud import get_user_by_email
from app.database import get_db
from app.models import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token", auto_error=False)
bearer_scheme = HTTPBearer(auto_error=False)
SECRET_KEY = settings.SECRET_KEY
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = timedelta(minutes=60)

security_schemes = {
    "OAuth2PasswordBearer": {
        "type": "oauth2",
        "flows": {
            "password": {
                "tokenUrl": "token",
                "scopes": {}
            }
        }
    },
    "BearerAuth": {
        "type": "http",
        "scheme": "bearer"
    }
}


async def get_current_user(
        request: Request,
        db: AsyncSession = Depends(get_db),
        credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
        token: str = Depends(oauth2_scheme)
) -> User:
    # Try to get token in order:
    # 1. Cookie
    # 2. Bearer
    # 3. OAuth2
    access_token = request.cookies.get("access_token")
    match (access_token, credentials, token):
        case str(), _, _:
            jwt_token = access_token.replace("Bearer ", "")
            token_source = "cookie"
        case _, HTTPAuthorizationCredentials(), _:
            jwt_token = credentials.credentials
            token_source = "bearer_header"
        case _, _, str():
            jwt_token = token
            token_source = "oauth2"
        case _:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials"
            )

    try:
        payload = jwt.decode(
            jwt_token,
            settings.SECRET_KEY,
            algorithms=["HS256"]
        )
    except (ExpiredSignatureError, DecodeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token or authentication expired, try to re-login"
        )
    email = payload.get("sub")
    if email is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )
    token_data = schemas.TokenData(email=email)

    user = await get_user_by_email(db, email=token_data.email)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User with provided credentials not found"
        )

    request.state.token_source = token_source

    return user


async def get_current_admin(
        current_user: User = Depends(get_current_user)
) -> User:
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return current_user


async def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.now(UTC) + ACCESS_TOKEN_EXPIRE_MINUTES
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def calculate_payment_signature(payment: schemas.PaymentWebhook):
    if payment.amount.is_integer():
        amount = str(int(payment.amount))
    else:
        amount = str(payment.amount)
    data_string = (f"{payment.account_id}{amount}{payment.transaction_id}"
                   f"{payment.user_id}{settings.WEBHOOK_SECRET_KEY}")
    calculated_signature = hashlib.sha256(data_string.encode()).hexdigest()
    return calculated_signature
