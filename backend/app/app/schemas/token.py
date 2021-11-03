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
    member_id: int = None

    name: str = None
    class_id: int = None
    subject_id: int = None
    member_role: str = None
