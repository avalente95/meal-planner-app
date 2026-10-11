export type Ingredient = {
  id: string;
  name: string;
  created_at: string;
  updated_at: string;
};

export type IngredientCreate = {
  name: string;
};