import { request } from "./client";
import type { Ingredient, IngredientCreate } from "../types";

export const listIngredients = () =>
  request<Ingredient[]>("/api/v1/ingredients");

export const createIngredient = (data: IngredientCreate) =>
  request<Ingredient>("/api/v1/ingredients", { method: "POST", body: data });