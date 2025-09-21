from sqlalchemy import Column, Integer, String
from .database import Base

from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from .database import Base

from sqlalchemy import Column, Integer, String
from .database import Base
from sqlalchemy import Column, Integer, String, Float, Date
from .database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, index=True, nullable=True)

    # This creates the link between a User and their WatchlistItems
    watchlist_items = relationship("WatchlistItem", back_populates="owner")

class SuggestionHistory(Base):
    __tablename__ = "suggestion_history"

    id = Column(Integer, primary_key=True, index=True)
    date_suggested = Column(Date, index=True)
    ticker = Column(String, index=True)
    price_at_suggestion = Column(Float)
    predicted_price = Column(Float)
    best_model = Column(String)
class WatchlistItem(Base):
    __tablename__ = "watchlist_items"

    id = Column(Integer, primary_key=True, index=True)
    ticker = Column(String, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))

    # This creates the link back to the User who owns the item
    owner = relationship("User", back_populates="watchlist_items")