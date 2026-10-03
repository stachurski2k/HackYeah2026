# AI Proxy API

Minimalny backend FastAPI z bazą SQLite do zarządzania tokenami, użytkownikami,
grupami, modelami, uprawnieniami, akcjami, budżetami i narzędziami walidacji.

## Uruchomienie

```bash
uv sync
uv run asbest
```

Dokumentacja OpenAPI: <http://127.0.0.1:8000/docs>

Ustawienia aplikacji znajdują się w `config.toml` i są wczytywane jako zwykły
słownik Pythona.

## Struktura

```text
app/
└── server.py              # uruchomienie aplikacji
api/
├── application.py         # FastAPI i rejestracja routerów
├── config.py              # config.get("sekcja.klucz", wartość_domyślna)
├── endpoints/
│   ├── chat.py            # endpoint chat
│   └── database.py        # endpointy administrujące danymi
├── schemas/               # osobne schematy dla każdej domeny
└── db/
    ├── models.py          # modele SQLAlchemy
    ├── session.py         # silnik i sesje
    └── seed.py            # dane referencyjne
```

## Pierwszy przepływ

```bash
# Wygenerowanie tokena
curl -X POST http://127.0.0.1:8000/tokens

# Utworzenie użytkownika (token można pominąć, wtedy powstanie automatycznie)
curl -X POST http://127.0.0.1:8000/users \
  -H 'Content-Type: application/json' \
  -d '{"name":"Ala","token":"TOKEN","groups":["user"]}'

# Pierwszy etap chat: weryfikacja tokena
curl -X POST http://127.0.0.1:8000/chat \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer TOKEN' \
  -d '{"message":"Cześć"}'
```

Przy starcie tworzone są grupy `admin`, `office`, `user` oraz uprawnienia
`ALLOW`, `DENIED`, `ALLOW_WITH_ACTION`.

## Endpointy

- `POST /tokens` – generowanie tokena,
- `POST|GET|PATCH|DELETE /users` – użytkownicy i ich grupy,
- `POST|GET /groups` – grupy,
- `GET /permissions` – dostępne uprawnienia,
- `POST|GET|PATCH|DELETE /models` – rejestr modeli i ich adresów API,
- `PUT /models/{id}/policies` – uprawnienie grupy do modelu,
- `POST|GET|PATCH|DELETE /actions` – akcje z promptem,
- `PUT /actions/{id}/policies` – uprawnienie grupy do akcji,
- `PUT /budgets/{user_id}` – utworzenie lub zmiana budżetu,
- `POST|GET /validation-tools` – narzędzia walidacji,
- `POST /chat` – obecnie weryfikacja tokena Bearer.

## Testy

```bash
uv run pytest
uv run ruff check .
uv run ruff format --check .
uv run mypy
```
