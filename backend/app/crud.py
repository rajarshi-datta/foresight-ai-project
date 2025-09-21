from sqlalchemy.orm import Session
from . import models, schemas, security
from datetime import date

# === User CRUD Functions ===

def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()

def create_user(db: Session, user: schemas.UserCreate):
    hashed_password = security.get_password_hash(user.password)
    db_user = models.User(email=user.email, hashed_password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def update_user(db: Session, user: models.User, user_in: schemas.UserUpdate):
    if user_in.full_name is not None:
        user.full_name = user_in.full_name
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def update_password(db: Session, user: models.User, new_password: str):
    user.hashed_password = security.get_password_hash(new_password)
    db.add(user)
    db.commit()
    return user

# === Watchlist CRUD Functions ===

def get_watchlist_items_by_user(db: Session, user_id: int):
    return db.query(models.WatchlistItem).filter(models.WatchlistItem.user_id == user_id).all()

def add_watchlist_item(db: Session, ticker: str, user_id: int):
    # Check if the item already exists to prevent duplicates
    db_item = db.query(models.WatchlistItem).filter(
        models.WatchlistItem.ticker == ticker,
        models.WatchlistItem.user_id == user_id
    ).first()
    
    if db_item:
        return db_item # Already exists, just return it

    new_item = models.WatchlistItem(ticker=ticker.upper(), user_id=user_id)
    db.add(new_item)
    db.commit()
    db.refresh(new_item)
    return new_item

def remove_watchlist_item(db: Session, ticker: str, user_id: int):
    db_item = db.query(models.WatchlistItem).filter(
        models.WatchlistItem.ticker == ticker,
        models.WatchlistItem.user_id == user_id
    ).first()

    if db_item:
        db.delete(db_item)
        db.commit()
        return {"ok": True}
    return None # Item not found

# === Suggestion History CRUD Functions ===

def create_suggestion_history(db: Session, suggestion: dict):
    today = date.today()
    exists = db.query(models.SuggestionHistory).filter(
        models.SuggestionHistory.ticker == suggestion["ticker"],
        models.SuggestionHistory.date_suggested == today
    ).first()

    if not exists:
        db_suggestion = models.SuggestionHistory(
            date_suggested=today,
            ticker=suggestion["ticker"],
            price_at_suggestion=suggestion["current_price"],
            predicted_price=suggestion["forecast_details"]["predicted_price"],
            best_model=suggestion["forecast_details"]["best_model"]
        )
        db.add(db_suggestion)
        db.commit()

def get_suggestion_history(db: Session):
    return db.query(models.SuggestionHistory).order_by(models.SuggestionHistory.date_suggested.desc()).all()