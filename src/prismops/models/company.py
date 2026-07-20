"""Core company and operational metric contracts."""

from pydantic import BaseModel, Field


class Facility(BaseModel):
    """An operating location belonging to a company."""

    id: str
    name: str
    type: str


class KPI(BaseModel):
    """A point-in-time key performance indicator."""

    name: str
    value: float
    unit: str


class Company(BaseModel):
    """A company available for operational analysis."""

    id: str
    name: str
    industry: str
    description: str
    headquarters: str
    employees: int = Field(ge=0)
    annual_revenue_usd: float = Field(ge=0)

