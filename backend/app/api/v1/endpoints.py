from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta
import yfinance as yf
from typing import List
from ...core import sentiment_analysis
# --- Local Imports ---
from ... import schemas, crud, security, models
from ...database import get_db
from ...core import forecasting, suggestion_engine, market_data

router = APIRouter()

# === AUTHENTICATION ENDPOINTS ===

@router.post("/auth/register", response_model=schemas.User, tags=["Authentication"])
def create_user_endpoint(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    return crud.create_user(db=db, user=user)

@router.post("/auth/token", response_model=schemas.Token, tags=["Authentication"])
def login_for_access_token(db: Session = Depends(get_db), form_data: OAuth2PasswordRequestForm = Depends()):
    user = crud.get_user_by_email(db, email=form_data.username)
    if not user or not security.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=security.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = security.create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/auth/forgot-password", tags=["Authentication"])
async def forgot_password(email_schema: schemas.EmailSchema, db: Session = Depends(get_db)):
    user = crud.get_user_by_email(db, email=email_schema.email)
    if not user:
        return {"message": "If an account with that email exists, a password reset link has been sent."}
    
    reset_token = security.create_access_token(
        data={"sub": user.email}, expires_delta=timedelta(minutes=15)
    )
    await security.send_password_reset_email(email=user.email, token=reset_token)
    return {"message": "Password reset email sent."}

@router.post("/auth/reset-password", tags=["Authentication"])
def reset_password(reset_schema: schemas.PasswordResetSchema, db: Session = Depends(get_db)):
    user = security.get_current_user(token=reset_schema.token, db=db)
    crud.update_password(db, user=user, new_password=reset_schema.new_password)
    return {"message": "Password updated successfully."}

# === USER PROFILE ENDPOINTS ===

@router.get("/users/me", response_model=schemas.User, tags=["Users"])
def read_users_me(current_user: models.User = Depends(security.get_current_user)):
    return current_user

@router.put("/users/me", response_model=schemas.User, tags=["Users"])
def update_user_me(user_in: schemas.UserUpdate, db: Session = Depends(get_db), current_user: models.User = Depends(security.get_current_user)):
    user = crud.update_user(db, user=current_user, user_in=user_in)
    return user

# === WATCHLIST ENDPOINTS ===

@router.get("/watchlist", response_model=List[schemas.WatchlistItem], tags=["Watchlist"])
def get_watchlist(db: Session = Depends(get_db), current_user: models.User = Depends(security.get_current_user)):
    return crud.get_watchlist_items_by_user(db=db, user_id=current_user.id)

@router.post("/watchlist/{ticker}", response_model=schemas.WatchlistItem, tags=["Watchlist"])
def add_to_watchlist(ticker: str, db: Session = Depends(get_db), current_user: models.User = Depends(security.get_current_user)):
    return crud.add_watchlist_item(db=db, ticker=ticker, user_id=current_user.id)

@router.delete("/watchlist/{ticker}", tags=["Watchlist"])
def remove_from_watchlist(ticker: str, db: Session = Depends(get_db), current_user: models.User = Depends(security.get_current_user)):
    result = crud.remove_watchlist_item(db=db, ticker=ticker, user_id=current_user.id)
    if not result:
        raise HTTPException(status_code=404, detail="Item not found in watchlist")
    return {"message": "Successfully removed from watchlist"}

# === STOCKS & REPORTS ENDPOINTS ===

@router.get("/stocks/forecast/{ticker}", response_model=schemas.ForecastResponse, tags=["Stocks"])
def get_forecast(ticker: str, horizon: int = 5, current_user: models.User = Depends(security.get_current_user)):
    result = forecasting.run_all_forecasts(ticker, horizon)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result

@router.get("/stocks/suggest", response_model=List[schemas.Suggestion], tags=["Stocks"])
def get_suggestions(db: Session = Depends(get_db), horizon: int = 5, current_user: models.User = Depends(security.get_current_user)):
    suggestions = suggestion_engine.generate_suggestions(db=db, horizon=horizon)
    if not suggestions:
        raise HTTPException(status_code=500, detail="Could not generate suggestions.")
    return suggestions

@router.get("/stocks/market-overview", response_model=schemas.MarketOverviewResponse, tags=["Stocks"])
def get_market_overview_endpoint(current_user: models.User = Depends(security.get_current_user)):
    return market_data.get_market_overview()

@router.get("/stocks/reports", response_model=schemas.ReportsResponse, tags=["Stocks"])
def get_reports(db: Session = Depends(get_db), current_user: models.User = Depends(security.get_current_user)):
    history = crud.get_suggestion_history(db)
    tickers = [item.ticker for item in history]
    if not tickers:
        return {"history": []}
        
    current_prices_data = yf.download(tickers, period="1d", progress=False)['Close']
    
    report_items = []
    for item in history:
        current_price = current_prices_data.get(item.ticker)
        if current_price is not None:
            performance = ((current_price - item.price_at_suggestion) / item.price_at_suggestion) * 100
            report_items.append({
                "date_suggested": item.date_suggested, "ticker": item.ticker,
                "price_at_suggestion": item.price_at_suggestion,
                "current_price": current_price, "performance_percent": performance
            })
    return {"history": report_items}
@router.get("/stocks/sentiment/{ticker}", response_model=schemas.SentimentResponse, tags=["Stocks"])
def get_sentiment_for_ticker(ticker: str, current_user: models.User = Depends(security.get_current_user)):
    """
    Gets the latest news sentiment for a given stock ticker.
    """
    sentiment_data = sentiment_analysis.get_news_sentiment(ticker)
    if "error" in sentiment_data:
        raise HTTPException(status_code=500, detail=f"Could not process sentiment for {ticker}")
    return sentiment_data