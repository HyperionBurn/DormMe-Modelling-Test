import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

def simulate_single_scenario(
    conversion_rate: float,
    churn_rate: float,
    price: float,
    growth_rate: float
) -> tuple[float, float, float]:
    """
    Simulates a 36-month revenue model for DormMe based on the given randomized variables.

    Returns:
        tuple: (Year 1 ARR, Year 2 ARR, Year 3 ARR) where ARR is defined as the
               cumulative total recurring revenue collected during that 12-month period.
    """
    # Initialize constants
    initial_beds = 5200
    months = 36

    mrr_history = []
    active_beds = 0.0

    for month in range(1, months + 1):
        if month <= 3:
            # Pilot period, no revenue
            mrr_history.append(0.0)
        elif month == 4:
            # Month 4: Conversion from pilot
            active_beds = initial_beds * conversion_rate
            mrr_history.append(active_beds * price)
        else:
            # Month 5 onwards: Apply churn and growth
            churned_beds = active_beds * churn_rate
            new_beds = active_beds * growth_rate
            active_beds = active_beds - churned_beds + new_beds
            mrr_history.append(active_beds * price)

    # Calculate Cumulative ARR for each year
    y1_arr = sum(mrr_history[0:12])
    y2_arr = sum(mrr_history[12:24])
    y3_arr = sum(mrr_history[24:36])

    return y1_arr, y2_arr, y3_arr

def run_monte_carlo(n_simulations: int = 10000) -> pd.DataFrame:
    """
    Executes a Monte Carlo simulation for DormMe's revenue model.
    """
    # Pre-generate random variables for performance
    # Conversion Rate: Normal(0.12, 0.03) clipped to [0.05, 0.20]
    conversion_rates = np.clip(np.random.normal(0.12, 0.03, n_simulations), 0.05, 0.20)

    # Churn Rate: Uniform(0.02, 0.06)
    churn_rates = np.random.uniform(0.02, 0.06, n_simulations)

    # Price (AED): Uniform(50, 150)
    prices = np.random.uniform(50, 150, n_simulations)

    # Growth Rate: Uniform(0.02, 0.05)
    growth_rates = np.random.uniform(0.02, 0.05, n_simulations)

    results = {
        'Y1_ARR': np.zeros(n_simulations),
        'Y2_ARR': np.zeros(n_simulations),
        'Y3_ARR': np.zeros(n_simulations)
    }

    for i in range(n_simulations):
        y1, y2, y3 = simulate_single_scenario(
            conversion_rates[i],
            churn_rates[i],
            prices[i],
            growth_rates[i]
        )
        results['Y1_ARR'][i] = y1
        results['Y2_ARR'][i] = y2
        results['Y3_ARR'][i] = y3

    return pd.DataFrame(results)

def generate_report_and_visualization(df: pd.DataFrame):
    """
    Prints the statistical summary report and generates the histogram for Year 1 ARR.
    """
    # --- Statistical Summary ---
    percentiles = [10, 50, 90]

    print("=" * 60)
    print("DORMME 36-MONTH REVENUE MODEL - MONTE CARLO SIMULATION")
    print(f"Number of Simulations: {len(df):,}")
    print("=" * 60)

    for year in [1, 2, 3]:
        col = f'Y{year}_ARR'
        p10 = np.percentile(df[col], 10)
        p50 = np.percentile(df[col], 50)
        p90 = np.percentile(df[col], 90)

        print(f"Year {year} ARR (Cumulative Revenue):")
        print(f"  10th Percentile (Worst Case): AED {p10:,.2f}")
        print(f"  50th Percentile (Base Case) : AED {p50:,.2f}")
        print(f"  90th Percentile (Best Case) : AED {p90:,.2f}")
        print("-" * 60)

    # --- Visualization ---
    # Configure high-contrast plot
    plt.style.use('dark_background')
    plt.figure(figsize=(10, 6))

    # Plot histogram with KDE
    ax = sns.histplot(
        df['Y1_ARR'],
        bins=50,
        kde=True,
        color='#00ffcc',
        edgecolor='black',
        alpha=0.7
    )

    # Add vertical line for median
    median_y1 = np.percentile(df['Y1_ARR'], 50)
    plt.axvline(
        median_y1,
        color='#ff00ff',
        linestyle='--',
        linewidth=2,
        label=f'50th Percentile (Median): AED {median_y1:,.0f}'
    )

    # Titles and labels
    plt.title('Probability Distribution of Year 1 ARR (Cumulative Revenue)', fontsize=14, fontweight='bold', pad=15)
    plt.xlabel('Year 1 ARR (AED)', fontsize=12, labelpad=10)
    plt.ylabel('Frequency (Number of Simulations)', fontsize=12, labelpad=10)

    # Formatting x-axis with comma separators
    ax.xaxis.set_major_formatter(plt.matplotlib.ticker.StrMethodFormatter('{x:,.0f}'))

    plt.legend()
    plt.tight_layout()

    # Save visualization
    save_path = 'dormme_y1_revenue_distribution.png'
    plt.savefig(save_path, dpi=300)
    print(f"\nVisualization saved to: {save_path}")

    # Display if possible
    try:
        plt.show()
    except Exception as e:
        print("Could not display plot interactively (this is normal in some environments).")

if __name__ == "__main__":
    # Execute Monte Carlo simulation
    df_results = run_monte_carlo(10000)

    # Generate outputs
    generate_report_and_visualization(df_results)
