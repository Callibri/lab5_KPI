from datetime import date

from pydantic import BaseModel


class RegisterRequest(BaseModel):
    email: str
    password: str


class LoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class CreatedResponse(BaseModel):
    id: int


class MovieRequest(BaseModel):
    title: str
    genre: str
    release_date: date
    budget_usd: int


class ReportRequest(BaseModel):
    report_date: date
    region: str
    revenue_usd: int
    tickets_sold: int


class ReportUpdateRequest(BaseModel):
    revenue_usd: int
    tickets_sold: int
