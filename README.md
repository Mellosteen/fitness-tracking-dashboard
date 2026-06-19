# Fitness Dashboard

A private shared Streamlit dashboard for two friends to manually track fitness and nutrition data, compare progress, and predict future body weight trajectory with a simple linear regression model.

## Features

- Supabase Auth sign-up, login, and logout
- One daily entry per user per date
- Shared visibility across both users
- Personal charts for weight, calories, protein, steps, workout streak, and weekly averages
- Friend comparison charts and shared entry table
- Linear regression prediction page for 7, 14, and 30 day weight trajectory
- Supabase Row Level Security so users can view shared entries but only edit their own rows

## Project Structure

```text
fitness-dashboard/
  app.py
  pages/
    1_Daily_Entry.py
    2_Personal_Dashboard.py
    3_Friend_Dashboard.py
    4_Prediction.py
  src/
    auth.py
    database.py
    metrics.py
    charts.py
    ml.py
  sql/
    schema.sql
  requirements.txt
  README.md
```

## Local Setup

1. Create a Supabase project.
2. Run `sql/schema.sql` in the Supabase SQL editor.
3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Create `.streamlit/secrets.toml`:

```toml
SUPABASE_URL = "https://your-project.supabase.co"
SUPABASE_ANON_KEY = "your-anon-key"
```

5. Start the app:

```bash
streamlit run app.py
```

## Streamlit Community Cloud

Set these app secrets in Streamlit Community Cloud:

```toml
SUPABASE_URL = "https://your-project.supabase.co"
SUPABASE_ANON_KEY = "your-anon-key"
```

Then deploy the repository with `app.py` as the entry point.

## Prediction Notes

The prediction page trains a `LinearRegression` model on the logged-in user's entries. It requires at least 14 entries and uses:

- `days_since_start`
- `calorie_difference`
- `protein_g`
- `carbs_g`
- `fat_g`
- `steps`
- `activity_calories`
- `workout_done`
- `sleep_hours`
- `energy_level`
- `hunger_level`
- `7_day_avg_calories`
- `7_day_avg_steps`
- `7_day_avg_protein`
- `7_day_avg_activity_calories`

The 7, 14, and 30 day projections hold the latest observed nutrition and activity values constant while advancing `days_since_start`.
