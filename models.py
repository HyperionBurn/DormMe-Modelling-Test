from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class University(Base):
    __tablename__ = 'universities'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, index=True)
    created_at = Column(DateTime, nullable=False)

    beds = relationship("Bed", back_populates="university")

class Bed(Base):
    __tablename__ = 'beds'
    id = Column(Integer, primary_key=True)
    university_id = Column(Integer, ForeignKey('universities.id'), nullable=False, index=True)
    status = Column(String, nullable=False) # e.g., 'Active', 'Churned'
    price = Column(Float, nullable=False)
    created_at = Column(DateTime, nullable=False)
    churned_at = Column(DateTime, nullable=True)

    university = relationship("University", back_populates="beds")
    payments = relationship("MonthlyPayment", back_populates="bed")
    churn_events = relationship("ChurnEvent", back_populates="bed")

class MonthlyPayment(Base):
    __tablename__ = 'monthly_payments'
    id = Column(Integer, primary_key=True)
    bed_id = Column(Integer, ForeignKey('beds.id'), nullable=False, index=True)
    amount = Column(Float, nullable=False)
    payment_date = Column(DateTime, nullable=False, index=True)
    is_expansion = Column(Boolean, default=False)

    bed = relationship("Bed", back_populates="payments")

class ChurnEvent(Base):
    __tablename__ = 'churn_events'
    id = Column(Integer, primary_key=True)
    bed_id = Column(Integer, ForeignKey('beds.id'), nullable=False, index=True)
    churn_date = Column(DateTime, nullable=False, index=True)
    reason = Column(String, nullable=False) # e.g., 'Voluntary', 'Involuntary'

    bed = relationship("Bed", back_populates="churn_events")

class MonteCarloProjection(Base):
    __tablename__ = 'monte_carlo_projections'
    id = Column(Integer, primary_key=True)
    simulation_run = Column(Integer, nullable=False, index=True)
    y1_arr = Column(Float, nullable=False)
    y2_arr = Column(Float, nullable=False)
    y3_arr = Column(Float, nullable=False)

def init_db(db_url="sqlite:///dormme.db"):
    """Initializes the database and creates all tables."""
    engine = create_engine(db_url)
    Base.metadata.create_all(engine)
    return engine

if __name__ == "__main__":
    init_db()
    print("Database architecture initialized successfully.")
