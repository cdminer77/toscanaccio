from sqlmodel import Session
from .models import MenuItem, Category

def seed_menu(session: Session):
    if session.exec(select(MenuItem)).first():
        return  # già popolato

    items = [
        # GASTRONOMIA
        MenuItem(name="Pappa al Pomodoro", description="Classica toscana con crostini", price=9.90, category=Category.GASTRONOMIA),
        MenuItem(name="Ribollita Toscana", description="Zuppa di pane e verdure", price=10.50, category=Category.GASTRONOMIA),
        MenuItem(name="Pappardelle al Sugo di Cinghiale", description="Hero product", price=13.90, category=Category.GASTRONOMIA),
        MenuItem(name="Lasagne alla Toscana", description="Comfort food", price=12.90, category=Category.GASTRONOMIA),
        MenuItem(name="Cacciucco Livornese", description="Zuppa di pesce", price=14.90, category=Category.GASTRONOMIA),
        # PROSCIUTTERIA
        MenuItem(name="Toscano Classico", description="Salame, Finocchiona, Pecorino", price=18.0, category=Category.PROSCIUTTERIA),
        MenuItem(name="Cinta Senese Experience", description="Prosciutto DOP + salumi", price=28.0, category=Category.PROSCIUTTERIA),
        MenuItem(name="Pecorino Tour", description="3 pecorini + confetture", price=25.0, category=Category.PROSCIUTTERIA),
    ]
    for item in items:
        session.add(item)
    session.commit()
    print("✅ Menu Toscanaccio caricato!")