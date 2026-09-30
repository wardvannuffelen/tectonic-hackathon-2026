from datetime import date

from pydantic import BaseModel, Field


class PersonaOut(BaseModel):
    name: str
    age: int
    job_title: str
    city: str


class LoginResponse(BaseModel):
    session_token: str
    customer_id: str
    persona: PersonaOut


class DevLoginRequest(BaseModel):
    customer_id: str


class TransactionOut(BaseModel):
    id: str
    date: date
    amount: float
    category: str
    description: str


class TransactionsResponse(BaseModel):
    customer_id: str
    transactions: list[TransactionOut]


class ForecastMonthOut(BaseModel):
    month_index: int
    calendar_month: int
    net_cashflow: float
    balance: float
    balance_low: float
    balance_high: float


class ForecastResponse(BaseModel):
    starting_balance: float
    months: list[ForecastMonthOut]


class ScenarioRequest(BaseModel):
    extra_savings_per_month: float = Field(ge=0, le=5000)


class ScenarioResponse(BaseModel):
    extra_savings_per_month: float
    baseline: ForecastResponse
    scenario: ForecastResponse


class GoalResultOut(BaseModel):
    goal_id: str
    name: str
    target_amount: float
    already_saved: float
    remaining_amount: float
    baseline_monthly_surplus: float
    extra_savings_per_month: float
    months_to_reach: int | None
    reach_date: date | None
    required_monthly_for_target_date: float | None
    target_date: date | None
    status: str


class GoalsResponse(BaseModel):
    goals: list[GoalResultOut]


class GoalSimulateRequest(BaseModel):
    extra_savings_per_month: float = Field(ge=0, le=5000)


class SavingsSuggestionOut(BaseModel):
    category: str
    label: str
    current_avg_monthly: float
    suggested_cut: float
    new_avg_monthly: float


class SavingsSourcesResponse(BaseModel):
    target_extra_savings: float
    suggestions: list[SavingsSuggestionOut]
    total_covered: float
    shortfall: float


class ChatMessageIn(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    message: str
    history: list[ChatMessageIn] = Field(default_factory=list)


class ChatResponse(BaseModel):
    reply: str
    used_tools: list[str]
    mode: str
