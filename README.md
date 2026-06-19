# Fitness Dashboard

A private shared Streamlit dashboard for two friends to manually track fitness and nutrition data, compare progress, and prepare for a future body weight prediction model.

## Features

- Supabase Auth sign-up, login, and logout
- One daily entry per user per date
- Shared visibility across both users
- Personal charts for weight, calories, protein, steps, workout streak, and weekly averages
- Friend comparison charts and shared entry table
- Prediction page scaffold with prepared model features and Torch implementation TODOs
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
  environment.local.yml
  requirements.txt
  README.md
```

## Local Setup

1. Create a Supabase project.
2. Run `sql/schema.sql` in the Supabase SQL editor.
3. Create and activate the Conda environment:

```bash
conda env create -f environment.local.yml
conda activate fitness-tracking-dashboard
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

If the environment already exists after dependency changes, update it with:

```bash
conda env update -f environment.local.yml --prune
```

## Streamlit Community Cloud

Set these app secrets in Streamlit Community Cloud:

```toml
SUPABASE_URL = "https://your-project.supabase.co"
SUPABASE_ANON_KEY = "your-anon-key"
```

Then deploy the repository with `app.py` as the entry point.

`requirements.txt` is used by Streamlit Community Cloud deployment. Use `environment.local.yml` for local Conda development. The Conda file is intentionally not named `environment.yml` because Streamlit Cloud prioritizes `environment.yml` over `requirements.txt`.

## Prediction Notes

The prediction page intentionally does not train a model yet. It prepares a model-ready dataset so the Torch implementation can be built later by hand. It requires at least 14 entries and prepares:

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

Suggested implementation path:

1. Add `torch` to `environment.local.yml` and `requirements.txt`.
2. Convert the prepared feature frame into `torch.float32` tensors.
3. Normalize input features and keep the training means/stds for inference.
4. Start with a single-layer `torch.nn.Linear(input_dim, 1)` model.
5. Train with MSE loss and an optimizer such as Adam or SGD.
6. Add forecast rows for 7, 14, and 30 days using the latest observed row as the base.
7. Plot actual weight against the predicted trajectory.
