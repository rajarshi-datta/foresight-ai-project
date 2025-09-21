from pydantic import BaseModel, EmailStr
from typing import List, Dict, Any, Optional
from datetime import date # IMPORT THIS

# --- User & Auth Schemas ---
class UserBase(BaseModel):
    email: EmailStr

class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    full_name: Optional[str] = None

class User(UserBase):
    id: int
    full_name: Optional[str] = None
    class Config:
        orm_mode = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None

class EmailSchema(BaseModel):
    email: EmailStr

class PasswordResetSchema(BaseModel):
    token: str
    new_password: str


# --- Stock Schemas ---
class ModelResult(BaseModel):
    status: str = "success"
    rmse: Optional[float] = None
    last_pred: Optional[float] = None
    error_message: Optional[str] = None
    predictions: Optional[List[float]] = None

class ForecastResponse(BaseModel):
    ticker: str
    horizon: int
    results: Dict[str, ModelResult]
    best_model: Optional[str] = None
    current_price: Optional[float] = None

class SuggestionMetrics(BaseModel):
    predicted_growth_percent: float
    suggestion_score: float

class ForecastDetails(BaseModel):
    predicted_price: float
    horizon_days: int
    best_model: str
    confidence_metric_rmse: Optional[float] = None

class Suggestion(BaseModel):
    rank: int
    ticker: str
    current_price: float
    forecast_details: ForecastDetails
    suggestion_metrics: SuggestionMetrics


# --- Market Data Schemas ---
class IndexData(BaseModel):
    name: str
    price: float
    change: float
    percent_change: float

class MoverData(BaseModel):
    ticker: str
    price: float
    percent_change: float

class Movers(BaseModel):
    gainers: list[MoverData]
    losers: list[MoverData]

class MarketOverviewResponse(BaseModel):
    indices: list[IndexData]
    movers: Movers


# --- Reports Schemas ---
class SuggestionHistoryItem(BaseModel):
    date_suggested: date
    ticker: str
    price_at_suggestion: float
    current_price: float
    performance_percent: float

class ReportsResponse(BaseModel):
    history: list[SuggestionHistoryItem]
class WatchlistItemBase(BaseModel):
    ticker: str
class WatchlistItemCreate(WatchlistItemBase):
    pass
class WatchlistItem(WatchlistItemBase):
    id: int
    user_id: int

    class Config:
        orm_mode = True
class Headline(BaseModel):
    title: str
    sentiment: str

class SentimentResponse(BaseModel):
    overall_sentiment: str
    score: float
    headlines: list[Headline]