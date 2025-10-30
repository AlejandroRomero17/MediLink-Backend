from pydantic import BaseModel, ConfigDict
from typing import Optional
from .usuario import UsuarioResponse


class Token(BaseModel):
    access_token: str
    token_type: str
    usuario: UsuarioResponse


class TokenData(BaseModel):
    user_id: Optional[int] = None
    email: Optional[str] = None
    tipo_usuario: Optional[str] = None
