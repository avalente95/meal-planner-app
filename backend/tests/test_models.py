"""Test manuale dei modelli ORM contro il DB reale.

Esegui da backend/ (venv attivo):   python test_models.py

Sicurezza dei dati: ogni test gira dentro un SAVEPOINT che viene sempre
annullato, e la transazione esterna viene annullata alla fine. Nel DB non
resta nulla, nemmeno se un test fallisce.

Nota: dentro una transazione now() restituisce l'istante di INIZIO della
transazione, quindi qui non si può verificare che updated_at cambi con
onupdate. Quel controllo va fatto con due richieste API separate.
"""
from decimal import Decimal
from uuid import uuid4

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db import engine
from app.models import Ingredient, Recipe, RecipeIngredient

TAG = uuid4().hex[:8]  # evita collisioni con ingredienti già presenti


class _Annulla(Exception):
    """Usata per forzare il rollback del savepoint a fine test."""


def rifiutato(session, azione):
    """True se il DB rifiuta l'operazione con IntegrityError."""
    try:
        with session.begin_nested():
            azione()
            session.flush()
    except IntegrityError:
        return True
    return False


def nuovo_ingrediente(session, nome):
    ing = Ingredient(name=f"{nome}-{TAG}")
    session.add(ing)
    session.flush()
    return ing


def nuova_ricetta(session, **override):
    campi = {"name": f"Ricetta-{TAG}", "complexity": 2, "prep_time_minutes": 20}
    campi.update(override)
    ric = Recipe(**campi)
    session.add(ric)
    session.flush()
    return ric


def collega(session, ric, ing, quantity="200", unit="g"):
    riga = RecipeIngredient(recipe_id=ric.id, ingredient_id=ing.id,
                            quantity=Decimal(quantity), unit=unit)
    session.add(riga)
    session.flush()
    return riga


def conta_righe(session, ric):
    return session.scalar(
        select(func.count()).select_from(RecipeIngredient)
        .where(RecipeIngredient.recipe_id == ric.id)
    )


# ---------------------------------------------------------------- test ----

def t_ingrediente_default(s):
    ing = nuovo_ingrediente(s, "Pasta")
    assert ing.id is not None, "id non generato dal DB"
    assert ing.created_at is not None and ing.updated_at is not None, "timestamp mancanti"
    assert ing.created_by is None and ing.last_updated_by is None, "created_by/last_updated_by dovrebbero essere NULL"


def t_ingrediente_nome_duplicato_normalizzato(s):
    nuovo_ingrediente(s, "Pomodoro")
    assert rifiutato(s, lambda: s.add(Ingredient(name=f"  POMODORO-{TAG} "))), \
        "il DB ha accettato un duplicato che differisce per maiuscole/spazi"


def t_ingrediente_nome_vuoto(s):
    assert rifiutato(s, lambda: s.add(Ingredient(name=""))), "nome vuoto accettato"


def t_ingrediente_nome_troppo_lungo(s):
    assert rifiutato(s, lambda: s.add(Ingredient(name="x" * 101))), "nome di 101 caratteri accettato"


def t_ricetta_nomi_duplicati_ammessi(s):
    nuova_ricetta(s)
    nuova_ricetta(s)  # stesso nome: deve passare (scelta di progetto)


def t_ricetta_senza_descrizione(s):
    ric = nuova_ricetta(s)
    assert ric.description is None, "description dovrebbe essere None"


def t_ricetta_vincoli_check(s):
    assert rifiutato(s, lambda: s.add(Recipe(name="a", complexity=6, prep_time_minutes=10))), "complessità 6 accettata"
    assert rifiutato(s, lambda: s.add(Recipe(name="a", complexity=0, prep_time_minutes=10))), "complessità 0 accettata"
    assert rifiutato(s, lambda: s.add(Recipe(name="a", complexity=2, prep_time_minutes=301))), "tempo 301 accettato"
    assert rifiutato(s, lambda: s.add(Recipe(name="a", complexity=2, prep_time_minutes=10, description=""))), "description vuota accettata"
    assert rifiutato(s, lambda: s.add(Recipe(name="a", complexity=2, prep_time_minutes=10, description="x" * 501))), "description di 501 caratteri accettata"


def t_relazioni_e_nome(s):
    ing = nuovo_ingrediente(s, "Farina")
    ric = nuova_ricetta(s)
    collega(s, ric, ing, "0.50", "pcs")
    s.expire_all()  # forza la rilettura dal DB
    ric = s.get(Recipe, ric.id)
    assert len(ric.ingredients) == 1, "la ricetta dovrebbe avere 1 ingrediente"
    riga = ric.ingredients[0]
    assert riga.quantity == Decimal("0.50"), f"quantità inattesa: {riga.quantity}"
    assert riga.unit == "pcs", "unità inattesa"
    assert riga.ingredient.id == ing.id, "relazione RecipeIngredient.ingredient errata"
    assert riga.recipe.id == ric.id, "relazione RecipeIngredient.recipe errata"
    assert riga.name == ing.name, "la proprietà name della riga non restituisce il nome dell'ingrediente"


def t_riga_unita_non_ammessa(s):
    ing, ric = nuovo_ingrediente(s, "Sale"), nuova_ricetta(s)
    assert rifiutato(s, lambda: collega(s, ric, ing, "10", "kg")), "unit 'kg' accettata"


def t_riga_quantita_non_positiva(s):
    ing, ric = nuovo_ingrediente(s, "Olio"), nuova_ricetta(s)
    assert rifiutato(s, lambda: collega(s, ric, ing, "0")), "quantity 0 accettata"
    assert rifiutato(s, lambda: collega(s, ric, ing, "-5")), "quantity negativa accettata"


def t_riga_ingrediente_ripetuto(s):
    ing, ric = nuovo_ingrediente(s, "Basilico"), nuova_ricetta(s)
    collega(s, ric, ing)
    assert rifiutato(s, lambda: collega(s, ric, ing, "50")), "stesso ingrediente due volte nella stessa ricetta accettato"


def t_cancella_ingrediente_usato_bloccato(s):
    ing, ric = nuovo_ingrediente(s, "Aglio"), nuova_ricetta(s)
    collega(s, ric, ing)
    assert rifiutato(s, lambda: s.delete(ing)), "ingrediente usato cancellato (RESTRICT non attivo)"


def t_cancella_ingrediente_libero(s):
    ing = nuovo_ingrediente(s, "Origano")
    s.delete(ing)
    s.flush()  # nessuna eccezione attesa


def t_cancella_ricetta_a_cascata(s):
    ing, ric = nuovo_ingrediente(s, "Riso"), nuova_ricetta(s)
    collega(s, ric, ing)
    ric_id, ing_id = ric.id, ing.id
    s.delete(ric)
    s.flush()
    s.expire_all()
    righe = s.scalar(select(func.count()).select_from(RecipeIngredient)
                     .where(RecipeIngredient.recipe_id == ric_id))
    assert righe == 0, "le righe ponte sono rimaste dopo la cancellazione della ricetta"
    assert s.get(Ingredient, ing_id) is not None, "l'ingrediente è sparito insieme alla ricetta"


def t_sostituzione_lista_ingredienti(s):
    a, b = nuovo_ingrediente(s, "Latte"), nuovo_ingrediente(s, "Uova")
    ric = nuova_ricetta(s)
    collega(s, ric, a)
    collega(s, ric, b, "2", "pcs")
    s.expire_all()
    ric = s.get(Recipe, ric.id)
    ric.ingredients = [r for r in ric.ingredients if r.ingredient_id == b.id]  # rimuove la riga di 'a'
    s.flush()
    assert conta_righe(s, ric) == 1, "delete-orphan non ha rimosso la riga tolta dalla lista"


TESTS = [v for k, v in sorted(globals().items()) if k.startswith("t_")]


def main():
    fallimenti = 0
    with engine.connect() as conn:
        trans = conn.begin()
        try:
            with Session(bind=conn) as session:
                for test in TESTS:
                    nome = test.__name__[2:].replace("_", " ")
                    try:
                        with session.begin_nested():
                            test(session)
                            raise _Annulla
                    except _Annulla:
                        print(f"[PASS] {nome}")
                    except AssertionError as e:
                        fallimenti += 1
                        print(f"[FAIL] {nome}   <-- {e}")
                    except Exception as e:  # errore imprevisto: mostra solo il tipo
                        fallimenti += 1
                        print(f"[FAIL] {nome}   <-- errore imprevisto: {type(e).__name__}")
        finally:
            trans.rollback()  # niente resta nel DB
    print(f"\n{len(TESTS) - fallimenti}/{len(TESTS)} test superati")
    raise SystemExit(1 if fallimenti else 0)


if __name__ == "__main__":
    main()