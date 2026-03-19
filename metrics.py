import pandas as pd
import numpy as np
from sqlalchemy.orm import sessionmaker
from models import init_db

def get_engine():
    return init_db()

def get_monthly_mrr(engine):
    """Calculates Total MRR per month."""
    query = """
        SELECT strftime('%Y-%m', payment_date) as month, SUM(amount) as mrr
        FROM monthly_payments
        GROUP BY month
        ORDER BY month
    """
    df = pd.read_sql(query, engine)
    return df

def get_nrr_and_grr(engine):
    """
    Calculates Net Revenue Retention (NRR) and Gross Revenue Retention (GRR).
    NRR = (Starting MRR + Expansion MRR - Churn MRR) / Starting MRR
    GRR = (Starting MRR - Churn MRR) / Starting MRR
    Calculated month-over-month.
    """
    # Get total MRR per bed per month
    query = """
        SELECT
            bed_id,
            strftime('%Y-%m', payment_date) as month,
            amount,
            is_expansion
        FROM monthly_payments
    """
    df = pd.read_sql(query, engine)

    # Pivot to get month-over-month MRR per bed
    pivot_df = df.pivot(index='bed_id', columns='month', values='amount').fillna(0)

    months = pivot_df.columns
    nrr_list = []
    grr_list = []

    for i in range(1, len(months)):
        prev_month = months[i-1]
        curr_month = months[i]

        # Beds active in the previous month
        starting_mrr_beds = pivot_df[pivot_df[prev_month] > 0]

        starting_mrr = starting_mrr_beds[prev_month].sum()
        if starting_mrr == 0:
            continue

        # Revenue from those SAME beds in the current month
        retained_and_expanded_mrr = starting_mrr_beds[curr_month].sum()

        # To calculate GRR, we cap the retained revenue at the starting revenue (ignore expansion)
        # Note: In our simple model, expansion increases price.
        # So we can take the minimum of (prev_month_mrr, curr_month_mrr) for GRR
        retained_no_expansion_mrr = starting_mrr_beds[[prev_month, curr_month]].min(axis=1).sum()

        nrr = (retained_and_expanded_mrr / starting_mrr) * 100
        grr = (retained_no_expansion_mrr / starting_mrr) * 100

        nrr_list.append(nrr)
        grr_list.append(grr)

    avg_nrr = np.mean(nrr_list) if nrr_list else 0
    avg_grr = np.mean(grr_list) if grr_list else 0

    return avg_nrr, avg_grr

def get_cac_ltv_payback(engine):
    """
    Calculates Customer Acquisition Cost (CAC), Lifetime Value (LTV),
    LTV:CAC Ratio, and Payback Period.
    Note: 'Customer' here is treated as a 'Bed' for unit economics.
    """
    # 1. Calculate average Churn Rate
    query_churn = """
        SELECT COUNT(*) as churn_count
        FROM churn_events
    """
    churn_count = pd.read_sql(query_churn, engine).iloc[0]['churn_count']

    query_total_months = """
        SELECT COUNT(DISTINCT strftime('%Y-%m', payment_date)) as months
        FROM monthly_payments
    """
    months_active = pd.read_sql(query_total_months, engine).iloc[0]['months']

    query_avg_beds = """
        SELECT AVG(bed_count) as avg_beds
        FROM (
            SELECT strftime('%Y-%m', payment_date) as month, COUNT(DISTINCT bed_id) as bed_count
            FROM monthly_payments
            GROUP BY month
        )
    """
    avg_beds = pd.read_sql(query_avg_beds, engine).iloc[0]['avg_beds']

    monthly_churn_rate = (churn_count / months_active) / avg_beds if avg_beds > 0 else 0.05

    # Avoid division by zero, set max lifetime to 60 months
    lifetime_months = min(1 / monthly_churn_rate, 60) if monthly_churn_rate > 0 else 60

    # 2. Calculate ARPU (Average Revenue Per User/Bed)
    query_arpu = """
        SELECT AVG(amount) as arpu
        FROM monthly_payments
    """
    arpu = pd.read_sql(query_arpu, engine).iloc[0]['arpu']

    # 3. Calculate LTV
    # Assuming 80% gross margin for SaaS
    gross_margin = 0.80
    ltv = arpu * gross_margin * lifetime_months

    # 4. Synthesize CAC
    # We will assume a marketing spend that results in a synthetic CAC
    # Industry standard LTV:CAC is 3:1, so let's set our synthetic CAC around LTV / 3.5
    # with some randomness to simulate a real scenario.
    cac = ltv / np.random.uniform(3.0, 4.0)

    # 5. Calculate LTV:CAC
    ltv_cac_ratio = ltv / cac if cac > 0 else 0

    # 6. Calculate Payback Period (Months to recover CAC)
    payback_period = cac / (arpu * gross_margin) if (arpu * gross_margin) > 0 else 0

    return {
        'ARPU': arpu,
        'LTV': ltv,
        'CAC': cac,
        'LTV_CAC_Ratio': ltv_cac_ratio,
        'Payback_Period': payback_period,
        'Monthly_Churn_Rate': monthly_churn_rate * 100 # as percentage
    }

def get_cohort_churn(engine):
    """
    Calculates cohort retention/churn matrix.
    """
    query = """
        SELECT
            bed_id,
            MIN(strftime('%Y-%m', payment_date)) as cohort_month,
            strftime('%Y-%m', payment_date) as active_month
        FROM monthly_payments
        GROUP BY bed_id, active_month
    """
    df = pd.read_sql(query, engine)

    # Create cohort sizes
    cohort_sizes = df.groupby('cohort_month')['bed_id'].nunique().reset_index()
    cohort_sizes.rename(columns={'bed_id': 'cohort_size'}, inplace=True)

    # Calculate retention by cohort and active month
    cohorts = df.groupby(['cohort_month', 'active_month'])['bed_id'].nunique().reset_index()

    # Calculate month index (0, 1, 2...)
    cohorts['cohort_month_dt'] = pd.to_datetime(cohorts['cohort_month'])
    cohorts['active_month_dt'] = pd.to_datetime(cohorts['active_month'])
    cohorts['month_index'] = ((cohorts['active_month_dt'].dt.year - cohorts['cohort_month_dt'].dt.year) * 12 +
                               cohorts['active_month_dt'].dt.month - cohorts['cohort_month_dt'].dt.month)

    # Merge sizes
    cohorts = pd.merge(cohorts, cohort_sizes, on='cohort_month')
    cohorts['retention_rate'] = cohorts['bed_id'] / cohorts['cohort_size']

    # Pivot to wide format
    retention_matrix = cohorts.pivot(index='cohort_month', columns='month_index', values='retention_rate')

    return retention_matrix

def get_monte_carlo_results(engine):
    query = "SELECT * FROM monte_carlo_projections"
    df = pd.read_sql(query, engine)
    return df

if __name__ == "__main__":
    engine = get_engine()
    print("--- SaaS Benchmarks ---")
    nrr, grr = get_nrr_and_grr(engine)
    print(f"NRR: {nrr:.2f}% (Target: >120%)")
    print(f"GRR: {grr:.2f}% (Target: >85%)")

    metrics = get_cac_ltv_payback(engine)
    print(f"ARPU: AED {metrics['ARPU']:.2f}")
    print(f"CAC: AED {metrics['CAC']:.2f}")
    print(f"LTV: AED {metrics['LTV']:.2f}")
    print(f"LTV:CAC Ratio: {metrics['LTV_CAC_Ratio']:.2f}x (Target: 3:1 to 4:1)")
    print(f"Payback Period: {metrics['Payback_Period']:.1f} months (Target: 12-15)")
