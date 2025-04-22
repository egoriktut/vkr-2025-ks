from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()

async def get_current_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    return credentials.credentials