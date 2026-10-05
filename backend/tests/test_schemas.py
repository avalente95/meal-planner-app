"""Test manuale degli schemi Pydantic (input).

Esegui da backend/:   python test_schemas.py
Ogni caso dichiara se deve passare (OK) o essere rifiutato (KO).
"""
from uuid import uuid4

from pydantic import ValidationError

from app.schemas import IngredientInput, RecipeInput

ID_A, ID_B = str(uuid4()), str(uuid4())


def riga(ingredient_id=ID_A, quantity="200", unit="g"):
    return {"ingredient_id": ingredient_id, "quantity": quantity, "unit": unit}


def ricetta(**override):
    """Ricetta valida di base: i singoli test cambiano solo un campo."""
    base = {
        "name": "Pasta al pomodoro",
        "description": "Semplice",
        "ingredients": [riga()],
        "complexity": 2,
        "prep_time_minutes": 20,
    }
    base.update(override)
    return base


# (descrizione, classe, dati, atteso: "OK" = accettato, "KO" = rifiutato)
CASI = [
    # --- IngredientInput ---
    ("ingrediente valido", IngredientInput, {"name": "Pasta"}, "OK"),
    ("ingrediente: nome solo spazi", IngredientInput, {"name": "   "}, "KO"),
    ("ingrediente: nome vuoto", IngredientInput, {"name": ""}, "KO"),
    ("ingrediente: nome di 101 caratteri", IngredientInput, {"name": "x" * 101}, "KO"),
    ("ingrediente: campo id non ammesso", IngredientInput, {"name": "Pasta", "id": "abc"}, "KO"),
    ("ingrediente: campo created_by non ammesso", IngredientInput, {"name": "Pasta", "created_by": ID_A}, "KO"),
    # --- RecipeInput ---
    ("ricetta valida", RecipeInput, ricetta(), "OK"),
    ("ricetta valida senza description", RecipeInput, {k: v for k, v in ricetta().items() if k != "description"}, "OK"),
    ("ricetta: quantità decimale (0.5 pcs)", RecipeInput, ricetta(ingredients=[riga(quantity="0.5", unit="pcs")]), "OK"),
    ("ricetta: lista ingredienti vuota", RecipeInput, ricetta(ingredients=[]), "KO"),
    ("ricetta: ingredient_id ripetuto", RecipeInput, ricetta(ingredients=[riga(ID_A), riga(ID_A, "50")]), "KO"),
    ("ricetta: due ingredienti diversi", RecipeInput, ricetta(ingredients=[riga(ID_A), riga(ID_B, "50")]), "OK"),
    ("ricetta: più di 20 ingredienti", RecipeInput, ricetta(ingredients=[riga(str(uuid4())) for _ in range(21)]), "KO"),
    ("ricetta: unit non ammessa (kg)", RecipeInput, ricetta(ingredients=[riga(unit="kg")]), "KO"),
    ("ricetta: quantity = 0 (il DB richiede > 0)", RecipeInput, ricetta(ingredients=[riga(quantity="0")]), "KO"),
    ("ricetta: quantity negativa", RecipeInput, ricetta(ingredients=[riga(quantity="-1")]), "KO"),
    ("ricetta: quantity con 3 decimali", RecipeInput, ricetta(ingredients=[riga(quantity="1.234")]), "KO"),
    ("ricetta: quantity oltre il massimo", RecipeInput, ricetta(ingredients=[riga(quantity="2001")]), "KO"),
    ("ricetta: ingredient_id non è un UUID", RecipeInput, ricetta(ingredients=[riga(ingredient_id="123")]), "KO"),
    ("ricetta: description di 501 caratteri", RecipeInput, ricetta(description="x" * 501), "KO"),
    ("ricetta: description stringa vuota (il DB la rifiuta)", RecipeInput, ricetta(description=""), "KO"),
    ("ricetta: complessità 0", RecipeInput, ricetta(complexity=0), "KO"),
    ("ricetta: complessità 6", RecipeInput, ricetta(complexity=6), "KO"),
    ("ricetta: tempo 301", RecipeInput, ricetta(prep_time_minutes=301), "KO"),
    ("ricetta: campo id non ammesso", RecipeInput, ricetta(id=ID_A), "KO"),
    ("ricetta: campo created_by non ammesso", RecipeInput, ricetta(created_by=ID_A), "KO"),
    ("ricetta: campo extra dentro una riga", RecipeInput, ricetta(ingredients=[{**riga(), "extra": 1}]), "KO"),
]


def main():
    fallimenti = 0
    for descrizione, classe, dati, atteso in CASI:
        try:
            classe(**dati)
            esito = "OK"
        except ValidationError:
            esito = "KO"
        passato = esito == atteso
        fallimenti += not passato
        stato = "PASS" if passato else "FAIL"
        extra = "" if passato else f"   <-- atteso {atteso}, ottenuto {esito}"
        print(f"[{stato}] {descrizione}{extra}")
    print(f"\n{len(CASI) - fallimenti}/{len(CASI)} casi superati")
    raise SystemExit(1 if fallimenti else 0)


if __name__ == "__main__":
    main()