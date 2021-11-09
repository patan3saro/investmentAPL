from typing import List

from pydantic import BaseModel


class ParametersBase(BaseModel):
    investors_number: int
    investors_type_array: str
    price_cpu: float
    hosting_capacity: int
    # years
    duration_cpu: int
    user_id: int


class ParametersCreate(ParametersBase):
    pass


class Parameters(ParametersBase):
    id: int

    class Config:
        orm_mode = True


class InvestmentBase(BaseModel):
    total_payoff: float
    split_payoffs: str
    split_revenues: str
    split_payments: str
    fairness: bool
    parameters_id: int

class InvestmentCreate(InvestmentBase):
    pass


class Investment(InvestmentBase):
    id: int

    class Config:
        orm_mode = True


class UserBase(BaseModel):
    email: str


class UserCreate(UserBase):
    password: str


class User(UserBase):
    id: int
    is_active: bool
    parameters: List[Parameters] = []

    class Config:
        orm_mode = True
