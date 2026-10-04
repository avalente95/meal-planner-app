CREATE TABLE IF NOT EXISTS ingredients (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    created_by UUID,
    last_updated_by UUID,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    name TEXT CHECK (char_length(name) BETWEEN 1 AND 100) NOT NULL
);
CREATE UNIQUE INDEX IF NOT EXISTS ingredients_name_unique_idx
    ON ingredients (lower(trim(name)));

CREATE TABLE IF NOT EXISTS recipes (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    created_by UUID,
    last_updated_by UUID,
    name TEXT CHECK (char_length(name) BETWEEN 1 AND 100) NOT NULL,
    description TEXT CHECK (char_length(description) BETWEEN 1 AND 500),
    complexity INTEGER CHECK (complexity >= 1 AND complexity <= 5),
    prep_time_minutes INTEGER CHECK (prep_time_minutes >= 0 AND prep_time_minutes <= 300)
);

CREATE TABLE IF NOT EXISTS recipe_ingredients (
    recipe_id UUID REFERENCES recipes(id) ON DELETE CASCADE,
    ingredient_id UUID REFERENCES ingredients(id) ON DELETE RESTRICT,
    unit VARCHAR(10) CHECK (unit IN ('g', 'ml', 'pcs')) NOT NULL,
    quantity NUMERIC(10, 2) CHECK (quantity > 0) NOT NULL,
    PRIMARY KEY (recipe_id, ingredient_id)
);

ALTER TABLE ingredients ENABLE ROW LEVEL SECURITY;
ALTER TABLE recipes ENABLE ROW LEVEL SECURITY;
ALTER TABLE recipe_ingredients ENABLE ROW LEVEL SECURITY;