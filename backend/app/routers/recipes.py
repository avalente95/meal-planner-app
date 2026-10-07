from fastapi import APIRouter, HTTPException, Query, status, Depends
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from uuid import UUID
from app.schemas import RecipeInput, RecipeOutput, RecipeOutputLight
from app.db import get_db
from app.models import Recipe, Ingredient, RecipeIngredient

router = APIRouter(prefix="/recipes", tags=["recipes"])

@router.post("", response_model=RecipeOutput, status_code=status.HTTP_201_CREATED)
def create_recipe(data: RecipeInput, db: Session = Depends(get_db)):
    lista_id = []
    list_recipe_ingredient=[]
    for i in data.ingredients:
        lista_id.append(i.ingredient_id)
        list_recipe_ingredient.append(RecipeIngredient(ingredient_id=i.ingredient_id, quantity=i.quantity, unit=i.unit))
    found=db.scalars(select(Ingredient.id).where(Ingredient.id.in_(lista_id))).all()
    if (len(found) != len(lista_id)): 
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="One or more ingredients do not exist")
    new_recipe =  Recipe(name=data.name, description=data.description, complexity=data.complexity, prep_time_minutes=data.prep_time_minutes, 
                         ingredients=list_recipe_ingredient)    
    try:
        db.add(new_recipe)
        db.commit()
        db.refresh(new_recipe)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="One or more ingredients do not exist")
    return new_recipe


@router.get("", response_model=list[RecipeOutputLight])
def list_recipes(limit: int = Query(50, ge=1, le=100),
                     offset: int = Query(0, ge=0),
                     db: Session = Depends(get_db)):
    return db.scalars(select(Recipe).order_by(Recipe.name).offset(offset).limit(limit)).all()

@router.get("/{recipe_id}", response_model=RecipeOutput)
def get_recipe(recipe_id: UUID, db: Session = Depends(get_db)):
    recipe = db.get(Recipe, recipe_id)
    if not recipe:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recipe not found")
    return recipe


@router.put("/{recipe_id}", response_model=RecipeOutput)
def update_recipe(recipe_id: UUID, data:RecipeInput, db: Session = Depends(get_db)):
    recipe = db.get(Recipe, recipe_id)
    if not recipe:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recipe not found")
    new_ingredients=[]
    id_list=[]
    for i in data.ingredients:
        id_list.append(i.ingredient_id)
        new_ingredients.append(RecipeIngredient(ingredient_id=i.ingredient_id, quantity=i.quantity, unit=i.unit))
    found=db.scalars(select(Ingredient.id).where(Ingredient.id.in_(id_list))).all()
    if len(found) != len(id_list):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="One or more ingredients do not exist")
    recipe.ingredients=new_ingredients
    recipe.name=data.name
    recipe.description=data.description
    recipe.complexity=data.complexity
    recipe.prep_time_minutes=data.prep_time_minutes
    recipe.updated_at = func.now()
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="One or more ingredients do not exist")
    db.refresh(recipe)
    return recipe


@router.delete("/{recipe_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_recipe(recipe_id: UUID, db: Session = Depends(get_db)):
    recipe = db.get(Recipe, recipe_id)
    if not recipe:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recipe not found")
    try:
        db.delete(recipe)
        db.commit()
    except:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recipe not found")
    return recipe