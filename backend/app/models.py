from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from datetime import datetime
from decimal import Decimal
from uuid import UUID
from sqlalchemy import ForeignKey, Integer, Numeric, TIMESTAMP, Text, func

class Base(DeclarativeBase):
    """Base model for all database models"""
    pass

class Ingredient(Base):
    """Ingredient model"""
    __tablename__ = "ingredients"

    id: Mapped[UUID] = mapped_column(primary_key=True, server_default=func.gen_random_uuid())
    name: Mapped[str] = mapped_column(Text, nullable=False)
    created_by: Mapped[UUID | None]
    last_updated_by: Mapped[UUID | None]
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

class Recipe(Base):
    """Recipe model"""
    __tablename__ = "recipes"

    id: Mapped[UUID] = mapped_column(primary_key=True, server_default=func.gen_random_uuid())
    name: Mapped[str] = mapped_column(Text, nullable=False)
    created_by: Mapped[UUID | None]
    last_updated_by: Mapped[UUID | None]
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())
    description: Mapped[str | None] = mapped_column(Text)
    complexity: Mapped[int] = mapped_column(Integer, nullable=False)
    prep_time_minutes: Mapped[int] = mapped_column(Integer, nullable=False)  # in minutes
    ingredients: Mapped[list["RecipeIngredient"]] = relationship(back_populates="recipe", cascade="all, delete-orphan", passive_deletes=True)

class RecipeIngredient(Base):
    """RecipeIngredient model"""
    __tablename__ = "recipe_ingredients"

    recipe_id: Mapped[UUID] = mapped_column(ForeignKey("recipes.id", ondelete="CASCADE"), primary_key=True)
    ingredient_id: Mapped[UUID] = mapped_column(ForeignKey("ingredients.id", ondelete="RESTRICT"), primary_key=True)
    quantity: Mapped[Decimal] = mapped_column(Numeric(10,2), nullable=False)
    unit: Mapped[str] = mapped_column(Text, nullable=False)
    recipe: Mapped["Recipe"] = relationship(back_populates="ingredients")
    ingredient: Mapped["Ingredient"] = relationship()
    @property
    def name(self) -> str:
        return self.ingredient.name