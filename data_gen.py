import random
from datetime import datetime
import pandas as pd
from dateutil.relativedelta import relativedelta
from sqlalchemy.orm import sessionmaker

from models import init_db, University, Bed, MonthlyPayment, ChurnEvent, MonteCarloProjection
from dormme_monte_carlo import run_monte_carlo

def generate_historical_data(session):
    """
    Generates 24 months of synthetic historical operations data.
    """
    start_date = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0) - relativedelta(months=24)
    months = 24

    # 1. Create Initial Universities
    universities = []
    for i in range(1, 11):
        uni = University(name=f"University {i}", created_at=start_date)
        session.add(uni)
        universities.append(uni)

    session.flush() # get ids

    # 2. Baseline 500 beds
    active_beds = []
    for i in range(500):
        uni = random.choice(universities)
        bed = Bed(
            university_id=uni.id,
            status='Active',
            price=random.uniform(50, 80), # base tier pricing
            created_at=start_date
        )
        session.add(bed)
        active_beds.append(bed)

    session.flush()

    # Track historical timeline
    current_date = start_date
    for month in range(months):
        print(f"Simulating Month {month + 1} ({current_date.strftime('%Y-%m')})... Active beds: {len(active_beds)}")

        # A. Payments & Expansion
        # Ensure we have the IDs populated from previous session flushes/adds
        session.flush()

        for bed in active_beds:
            # Random chance of expansion (upsell to premium tier)
            is_expansion = False
            if random.random() < 0.05 and bed.price < 120:
                bed.price += random.uniform(20, 40)
                is_expansion = True

            payment = MonthlyPayment(
                bed_id=bed.id,
                amount=bed.price,
                payment_date=current_date,
                is_expansion=is_expansion
            )
            session.add(payment)

        session.flush() # ensure payments are created

        # B. Churn
        churn_rate = random.uniform(0.02, 0.04)
        num_churn = int(len(active_beds) * churn_rate)
        churned_this_month = random.sample(active_beds, num_churn)

        for bed in churned_this_month:
            bed.status = 'Churned'
            bed.churned_at = current_date
            reason = random.choices(['Voluntary', 'Involuntary'], weights=[0.8, 0.2])[0]
            churn_event = ChurnEvent(
                bed_id=bed.id,
                churn_date=current_date,
                reason=reason
            )
            session.add(churn_event)
            active_beds.remove(bed)

        # C. Net New ARR (Growth)
        growth_rate = random.uniform(0.04, 0.08)
        num_new = int(len(active_beds) * growth_rate)
        for _ in range(num_new):
            uni = random.choice(universities)
            bed = Bed(
                university_id=uni.id,
                status='Active',
                price=random.uniform(50, 100),
                created_at=current_date
            )
            session.add(bed)
            active_beds.append(bed)

        current_date += relativedelta(months=1)

    session.commit()

def generate_monte_carlo_projections(session):
    """
    Runs the existing Monte Carlo simulation and saves results to the database.
    """
    print("Running Monte Carlo Projections (10,000 simulations)...")
    # run_monte_carlo handles the 36-month timeline and returns a DataFrame
    df_results = run_monte_carlo(10000)

    projections = []
    for index, row in df_results.iterrows():
        proj = MonteCarloProjection(
            simulation_run=index + 1,
            y1_arr=row['Y1_ARR'],
            y2_arr=row['Y2_ARR'],
            y3_arr=row['Y3_ARR']
        )
        projections.append(proj)

    session.bulk_save_objects(projections)
    session.commit()
    print("Monte Carlo projections saved successfully.")

if __name__ == "__main__":
    engine = init_db()
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        # Clear existing data for idempotency
        session.query(MonteCarloProjection).delete()
        session.query(ChurnEvent).delete()
        session.query(MonthlyPayment).delete()
        session.query(Bed).delete()
        session.query(University).delete()
        session.commit()

        print("Starting Data Generation...")
        generate_historical_data(session)
        generate_monte_carlo_projections(session)
        print("Data Generation Complete.")
    except Exception as e:
        session.rollback()
        print(f"Error: {e}")
    finally:
        session.close()
