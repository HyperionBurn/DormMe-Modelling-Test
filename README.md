# DormMe SaaS Operating System 🏢

DormMe is a B2B student housing marketplace. This repository contains a complete "SaaS Operating System" sandbox designed to model, project, and visualize the company's financial and operational performance over 36 months. It serves as a comprehensive tool for pitch decks and operational planning.

The project is built on a lightweight, portable architecture using Python, SQLAlchemy (SQLite), Streamlit, Pandas, and Plotly. It includes a 10,000-iteration Monte Carlo simulation engine, a synthetic historical data generator (24 months), a robust SaaS metrics engine, and an interactive executive dashboard.

## 🛠 Architecture & Tech Stack
The codebase is modularized into five core components:

1. **`dormme_monte_carlo.py` (The Simulation Engine):** A robust script executing 10,000 Monte Carlo iterations predicting Year 1-3 ARR variance based on randomized conversion, churn, price, and growth distributions.
2. **`models.py` (Database Architecture):** A production-ready SQLAlchemy ORM schema utilizing a local SQLite database (`dormme.db`). It maps out tables for `Universities`, `Beds`, `Monthly_Payments`, `Churn_Events`, and `Monte_Carlo_Projections`.
3. **`data_gen.py` (Synthetic Data Engine):** A script that populates the database with 24 months of synthetic "historical" data. It simulates 500 initial beds, month-over-month growth, "Expansion MRR", and randomized voluntary/involuntary churn events. It also runs the Monte Carlo simulation and seeds the projection data.
4. **`metrics.py` (SaaS Analytics Engine):** Analytical functions extracting data via Pandas and raw SQL to calculate critical 2026 B2B SaaS benchmarks, including Net Revenue Retention (NRR), Gross Revenue Retention (GRR), Customer Acquisition Cost (CAC), Lifetime Value (LTV), LTV:CAC Ratio, Payback Period, and ARPU.
5. **`app.py` (The Executive Streamlit Dashboard):** A multi-page, premium, high-contrast web application to visualize historical operations and Monte Carlo projections.

## 🚀 Getting Started

### Prerequisites
You will need Python 3.8+ installed. Install the required dependencies:

```bash
pip install pandas numpy sqlalchemy streamlit plotly matplotlib seaborn
```

### Running the System

**1. Initialize the Database & Generate Synthetic Data:**
First, generate the 24 months of historical operations and the 10,000 Monte Carlo projections. This script will automatically create the `dormme.db` file in your local directory.

```bash
python data_gen.py
```

*Note: Generating the projections may take a few moments depending on your machine.*

**2. Verify SaaS Metrics (Optional):**
You can run the analytics engine standalone to view the calculated benchmarks in your console:

```bash
python metrics.py
```

**3. Launch the Executive Dashboard:**
Run the Streamlit application to visualize the data in your browser.

```bash
streamlit run app.py
```

The application will start, typically accessible at `http://localhost:8501`.

## 📊 Dashboard Overview

* **Historical Operations (Page 1):** Displays top-level metric cards tracking Current MRR, NRR, LTV, and Payback Period against industry targets. Features a Plotly line chart illustrating MRR growth over the 24-month period and a detailed heat map for cohort churn analysis.
* **Financial Projections (Page 2):** Reads from the `Monte_Carlo_Projections` table to display the 10th (Worst Case), 50th (Base Case), and 90th (Best Case) percentile ARR targets using a high-fidelity Plotly histogram (bell curve) to visualize risk variance.

## ⚙️ Key Assumptions
- **Total Serviceable Market (TSM):** 5,200 beds (Year 1 locked pipeline).
- **Revenue Model:** Flat monthly subscription fee per active bed.
- **Monte Carlo Distributions:**
    - Pilot Conversion Rate: Normal(12%, 3%), clipped [5%, 20%]
    - Monthly Churn Rate: Uniform(2%, 6%)
    - Monthly Growth Rate: Uniform(2%, 5%)
    - Pricing: Uniform(50 AED, 150 AED)

## 📝 License
This project is proprietary and confidential.