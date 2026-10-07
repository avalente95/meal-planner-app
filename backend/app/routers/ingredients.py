from fastapi import APIRouter, HTTPException, Query, status, Depends
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from app.schemas import IngredientInput, IngredientOutput
from app.db import get_db
from app.models import Ingredient
from uuid import UUID

router = APIRouter(prefix="/ingredients", tags=["ingredients"])

@router.post("", response_model=IngredientOutput, status_code=status.HTTP_201_CREATED)
def create_ingredient(data: IngredientInput, db: Session = Depends(get_db)):
    new_ingredient = Ingredient(name=data.name)
    try:
        db.add(new_ingredient)
        db.commit()
        db.refresh(new_ingredient)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Ingredient already exists")
    return new_ingredient

@router.get("", response_model=list[IngredientOutput])
def list_ingredients(limit: int = Query(50, ge=1, le=100),
                     offset: int = Query(0, ge=0),
                     db: Session = Depends(get_db)):
    return db.scalars(select(Ingredient).order_by(Ingredient.name).offset(offset).limit(limit)).all()

@router.get("/{ingredient_id}", response_model=IngredientOutput)
def get_ingredient(ingredient_id: UUID, db: Session = Depends(get_db)):
    ingredient = db.get(Ingredient, ingredient_id)
    if not ingredient:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ingredient not found")
    return ingredient

@router.put("/{ingredient_id}", response_model=IngredientOutput)
def update_ingredient(ingredient_id: UUID, data: IngredientInput, db: Session = Depends(get_db)):
    ingredient = db.get(Ingredient, ingredient_id)
    if not ingredient:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ingredient not found")
    ingredient.name = data.name
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Ingredient already exists")
    db.refresh(ingredient)
    return ingredient

@router.delete("/{ingredient_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_ingredient(ingredient_id: UUID, db: Session = Depends(get_db)):
    ingredient = db.get(Ingredient, ingredient_id)
    if not ingredient:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ingredient not found")
    try:
        db.delete(ingredient)
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Ingredient is used in a recipe and cannot be deleted")
