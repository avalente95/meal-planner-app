from datetime import datetime
from decimal import Decimal
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, field_validator
from uuid import UUID

class IngredientInput(BaseModel):
    """Ingredient input model"""
    model_config = ConfigDict(extra = "forbid", str_strip_whitespace=True)
    name: str = Field(min_length=1, max_length=100)


class IngredientOutput(BaseModel):
    """Ingredient output model"""
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    name: str
    created_at: datetime
    updated_at: datetime

class RecipeIngredientInput(BaseModel):
    model_config = ConfigDict(extra = "forbid", str_strip_whitespace=True)
    ingredient_id: UUID
    quantity: Decimal = Field(gt=0, le=2000, max_digits=6, decimal_places=2)
    unit: Literal["g", "pcs", "ml"]

class RecipeIngredientOutput(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    ingredient_id: UUID
    name: str
    quantity: Decimal
    unit: Literal["g", "pcs", "ml"]

class RecipeInput(BaseModel):
    """Recipe input model"""
    model_config = ConfigDict(extra = "forbid", str_strip_whitespace=True)
    name: str = Field(min_length=1, max_length=100)
    description: str | None = Field(default=None, min_length=1, max_length=500)
    ingredients: list[RecipeIngredientInput] = Field(min_length=1, max_length=20)
    complexity: int = Field(ge=1, le=5)
    prep_time_minutes: int = Field(ge=1, le=300)  # in minutes
    @field_validator("ingredients")
    @classmethod
    def validate_ingredients(cls, ingredients):
        ingredient_ids = [ingredient.ingredient_id for ingredient in ingredients]
        if len(ingredient_ids) != len(set(ingredient_ids)):
            raise ValueError("Duplicate ingredients are not allowed.")
        return ingredients

class RecipeOutput(BaseModel):
    """Recipe output model"""
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    name: str
    description: str | None
    ingredients: list[RecipeIngredientOutput]
    complexity: int
    prep_time_minutes: int  # in minutes
    created_at: datetime
    updated_at: datetime

class RecipeOutputLight(BaseModel):
    """Recipe output model without ingredients"""
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    name: str
    description: str | None
    complexity: int
    prep_time_minutes: int  # in minutes
    created_at: datetime
    updated_at: datetime
