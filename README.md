# 🍽️ KupKo REST API

Preprosta REST API aplikacija, zgrajena s Flask, za upravljanje jedi in generiranje naključnih jedilnikov. Podpira filtriranje glede na alergene, čas priprave, ceno in tip jedi.

## Funkcionalnosti

- CRUD operacije za jedi - Ustvari, preberi, posodobi in izbriši jedi
- Generiranje naključnega jedilnika - Naključen izbor jedi za določeno število dni
- Napredno filtriranje - Filtriraj glede na alergene, čas priprave, ceno in tip
- Web vmesnik - Preprost HTML vmesnik za upravljanje podatkov
- SQLite podatkovna baza - Lahka lokalna shramba podatkov

## Zahteve

- Python 3.7+
- Naslednji Python paketi (glej requirements.txt):
  - Flask
  - Flask-SQLAlchemy
  - Flask-Marshmallow
  - marshmallow-sqlalchemy

## 🚀 Namestitev (lokalno)

1. Kloniraj repozitorij:
git clone <url-repozitorija>
cd <ime-mape>

2. Ustvari virtualno okolje (priporočljivo):
python -m venv venv
# Za Windows:
venv\Scripts\activate
# Za macOS/Linux:
source venv/bin/activate

3. Namesti zahteve:
pip install -r requirements.txt

4. Zaženi aplikacijo:
python app.py

Aplikacija bo dostopna na http://localhost:5000.

## Podatkovni model - Meal

| Polje | Tip | Opis |
|-------|-----|------|
| id | Integer | Primarni ključ (samodejno) |
| name | String(100) | Ime jedi (enolično) |
| price | Float | Cena jedi |
| meal_type | String(100) | Tip jedi (npr. "regular", "vegan", "vegetarian") |
| time_of_day | String(100) | Čas dneva (breakfast, lunch, dinner) |
| prep_time | Integer | Čas priprave v minutah |
| allergies | String(255) | Alergeni, ločeni z vejicami |

## API endpointi

### Osnovne operacije

#### Ustvari novo jed
POST /meal
Content-Type: application/json

{
    "name": "Špageti Bolognese",
    "price": 8.50,
    "meal_type": "regular",
    "time_of_day": "dinner",
    "prep_time": 45,
    "allergies": "gluten"
}

#### Pridobi vse jedi
GET /meal

#### Pridobi posamezno jed
GET /meal/{id}

#### Posodobi jed
PUT /meal/{id}
Content-Type: application/json

#### Izbriši jed
GET /delete/{id}

### Generiranje jedilnika

#### Naključni jedilnik
GET /random_menu

Parametri:
- n - število dni (privzeto: 7)
- time_of_day - časi dneva, ločeni z vejicami (privzeto: "breakfast,lunch,dinner")
- time - maksimalni čas priprave (minute)
- max_price - maksimalna cena
- meal_type - tip jedi
- allergies - alergeni, ločeni z vejicami

Primer:
GET /random_menu?n=5&time_of_day=lunch,dinner&max_price=10&time=30&allergies=gluten,dairy

## Web vmesnik

Aplikacija vključuje preprost web vmesnik:

- / - Seznam vseh jedi
- /add_meal - Dodajanje nove jedi preko obrazca

## Konfiguracija

- Podatkovna baza: SQLite (data.sqlite)
- Debug način: Omogočen (za produkcijo nastavi debug=False)
- Port: 5000

## Odpravljanje težav

### Pogoste težave:

1. "Port already in use"
   # Najdi proces, ki uporablja port 5000
   lsof -i :5000
   # Ali za Windows:
   netstat -ano | findstr :5000

2. Manjkajoči paketi
   pip install --upgrade -r requirements.txt

3. Težave z bazo
   # Izbriši obstoječo bazo in zaženi znova
   rm data.sqlite
   python app.py

## Varnostne opombe

- Za produkcijo: Onemogoči debug način (debug=False)
- Validacija: Implementiraj boljšo validacijo vnosov
- Avtentikacija: Dodaj avtentikacijo za zaščito API-ja

## Prispevanje

1. Fork repozitorija
2. Ustvari feature branch (git checkout -b feature/novost)
3. Commit spremembe (git commit -am 'Dodaj novo funkcionalnost')
4. Push na branch (git push origin feature/novost)
5. Ustvari Pull Request

## Licenca

Ta projekt je licenciran pod MIT licenco.

## Avtor
Blaž Turk
