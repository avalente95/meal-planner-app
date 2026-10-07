from fastapi import APIRouter, HTTPException, Query, status, Depends
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.schemas import RecipeInput, RecipeOutput, RecipeIngredientInput
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
    print("lista_id"+ " "+str(lista_id))
    print("lista_recipe_ingredients"+ " "+str(list_recipe_ingredient))
    
    found=db.scalars(select(Ingredient.id).where(Ingredient.id.in_(lista_id))).all()
    print("found"+ " "+str(found))
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
    