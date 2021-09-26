from pydantic import BaseModel


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenPayload(BaseModel):
    iss: str
    aud: str
    sub: str
    flag: str
    sub_sign: str
    class_id: int = None
    member_id: int = None
    member_role: str = None
    member_is_delete: int = None
