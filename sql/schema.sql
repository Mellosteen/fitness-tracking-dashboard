CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS daily_entries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    display_name TEXT NOT NULL,

    entry_date DATE NOT NULL,

    body_weight_kg NUMERIC(5,2),

    calories_eaten INTEGER,
    calorie_goal INTEGER,

    protein_g INTEGER,
    protein_goal_g INTEGER,

    carbs_g INTEGER,
    carbs_goal_g INTEGER,

    fat_g INTEGER,
    fat_goal_g INTEGER,

    steps INTEGER,
    activity_calories INTEGER,
    activity_type TEXT,
    workout_done BOOLEAN,

    sleep_hours NUMERIC(3,1),
    energy_level INTEGER,
    hunger_level INTEGER,

    notes TEXT,

    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    UNIQUE(user_id, entry_date)
);

CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS daily_entries_set_updated_at ON daily_entries;
CREATE TRIGGER daily_entries_set_updated_at
BEFORE UPDATE ON daily_entries
FOR EACH ROW
EXECUTE FUNCTION set_updated_at();

ALTER TABLE daily_entries ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Authenticated users can view all shared entries" ON daily_entries;
CREATE POLICY "Authenticated users can view all shared entries"
ON daily_entries
FOR SELECT
TO authenticated
USING (true);

DROP POLICY IF EXISTS "Users can create their own entries" ON daily_entries;
CREATE POLICY "Users can create their own entries"
ON daily_entries
FOR INSERT
TO authenticated
WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can update their own entries" ON daily_entries;
CREATE POLICY "Users can update their own entries"
ON daily_entries
FOR UPDATE
TO authenticated
USING (auth.uid() = user_id)
WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can delete their own entries" ON daily_entries;
CREATE POLICY "Users can delete their own entries"
ON daily_entries
FOR DELETE
TO authenticated
USING (auth.uid() = user_id);
