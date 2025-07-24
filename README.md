<img width="1919" height="909" alt="image" src="https://github.com/user-attachments/assets/7ecab6ab-9b4b-4797-b4d4-d94b8b7850f6" />

# HealthKart Influencer Marketing ROI Dashboard

This Streamlit dashboard is an open-source tool designed to track, visualize, and analyze the return on investment (ROI) of influencer marketing campaigns. It provides a comprehensive suite of tools for marketing managers and executives to make data-driven decisions.

## Features

*   **Executive Overview:** A high-level dashboard with key performance indicators (KPIs) and leaderboards for at-a-glance insights.
*   **Campaign Deep Dive:** Analyze revenue, payouts, and incremental ROAS for each campaign.
*   **Influencer Analysis:** A powerful scatter plot to evaluate influencers based on ROI, follower count, and revenue generation.
*   **Content & Engagement Insights:** Identify top-performing posts by revenue, likes, or engagement rate to understand what content resonates with your audience.
*   **Financial Review:** Analyze payout structures and use an interactive tool to identify underperforming influencers based on custom thresholds.
*   **Advanced Filtering:** Dynamically filter the entire dashboard by campaign, influencer category, and follower count.

## Analytics & Assumptions

This dashboard uses several key metrics to provide a holistic view of performance:

*   **ROAS (Return on Ad Spend):** Calculated as `Revenue / Payout`. It measures the gross revenue generated for every dollar spent.
*   **ROI (Return on Investment):** Calculated as `(Revenue - Payout) / Payout`. It measures the net profit generated for every dollar spent.
*   **Incremental ROAS (iROAS):** Calculated as `Campaign ROAS - Baseline ROAS`. The baseline is the average ROAS across all campaigns. This metric helps identify which campaigns are performing above or below the company average, providing a measure of true lift.
*   **Engagement Rate:** Calculated as `(Likes + Comments) / Reach`. This measures the percentage of people who interacted with the post after seeing it.

**Assumption:** The provided `payouts.csv` contains the *total payout* for an influencer for the entire analysis period, not per post. This is used as the cost basis for all ROI/ROAS calculations.

## Setup & Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/abhy-kumar/Healthkart-Intern.git
    cd healthkart-intern
    ```
2.  **Install dependencies:**
    ```bash
    pip install streamlit pandas numpy plotly
    ```
3.  **Place Data Files:** Ensure the following CSV files are in the root of the project directory:
    *   `influencers.csv`
    *   `posts.csv`
    *   `tracking_data.csv`
    *   `payouts.csv`
4.  **Run the Streamlit app:**
    ```bash
    streamlit run app.py
    ```

