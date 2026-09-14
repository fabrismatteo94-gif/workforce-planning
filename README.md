# Workforce Planning Tool — auxiell

MVP Fase 1 (roadmap sezione 9 dell'architettura): setup azienda, funzioni
settore Manifattura, calcolo FTE cascata, dashboard interattiva con undo,
storico modifiche, alert budget, export Excel.

## Struttura

```
workforce-planning-tool/
├── backend/     FastAPI + SQLAlchemy + SQLite — motore di calcolo e API
└── frontend/    React + TypeScript + Vite — dashboard brandizzata auxiell
```

## Avvio backend

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

L'API sarà su `http://localhost:8000`. Documentazione automatica (Swagger)
su `http://localhost:8000/docs` — utile per testare gli endpoint senza
frontend, o per capire rapidamente tutti i campi accettati.

Il database SQLite (`workforce_planning.db`) viene creato automaticamente
al primo avvio nella cartella `backend/`.

## Avvio frontend

```bash
cd frontend
npm install
npm run dev
```

L'app sarà su `http://localhost:5173`. Al primo accesso chiede il setup
azienda (nome, regione, anno fiscale); crea automaticamente le 3 funzioni
del template Manifattura (Produzione, QA, Manutenzione) e porta alla
dashboard.

## Cosa c'è già (Fase 1 MVP)

- ✅ Setup azienda (Step 1)
- ✅ Funzioni template Manifattura precaricate (Step 2, versione semplificata)
- ✅ Carico di lavoro editabile inline con ricalcolo cascata (Step 3 + sez. 17.2)
- ✅ Parametri organizzazione sempre visibili, editabili (Step 4)
- ✅ Motore di calcolo fedele alle formule sezione 3 (produzione, QA a
  rapporto, manutenzione derivata — con risoluzione delle dipendenze tra
  funzioni)
- ✅ Scenari dinamici Conservativo/Base/Aggressivo (slider globale, sez. 16)
- ✅ Undo (sezione 17.3) — annulla ultima modifica, ricalcola
- ✅ Storico modifiche (sezione 17.4) — timeline con vecchio/nuovo valore
- ✅ Budget alert (sezione 17.5) — badge verde/giallo/rosso in tempo reale
  nell'header (nota: la UI attuale mostra il badge ma non ancora il modal
  di conferma bloccante descritto in 17.5 — vedi "Prossimi passi")
- ✅ Export Excel (sezione 4.9, versione base: Per-Funzione + Riepilogo)
- ✅ Dashboard brandizzata auxiell (logo X ufficiale, palette nero/grigio)

## Prossimi passi (Fase 2 della roadmap)

- Modal di conferma bloccante quando si sfora il budget (opzioni: annulla /
  aumenta budget / accetta con override — schema già pronto lato backend
  in `Modifica.tipo_modifica = "Budget_Override"`, manca il collegamento UI)
- Skill & Profili (Step 5), Organigramma & JD drag-drop (Step 6)
- Template per altri settori (Servizi, Sales, Retail) — oggi il motore di
  calcolo supporta solo `REGOLE_MANIFATTURA` in `calculation_engine.py`
- Salvataggio scenari multipli con nome (oggi lo scenario è solo lo
  slider, non viene salvato come entità `SCENARIO` a sé stante)
- Migrazione a PostgreSQL quando serve concorrenza (basta cambiare
  `DATABASE_URL`, lo schema SQLAlchemy non cambia)
- Export PDF/PowerPoint (oggi solo Excel)

## Note tecniche

- Il ricalcolo cascata avviene sempre lato backend (`POST /calcolo`) in
  un'unica passata coerente su tutte le funzioni — mai calcoli parziali
  nel frontend, per evitare disallineamenti.
- Il debounce di 500ms (sezione 17.2) è implementato nel frontend
  (`Dashboard.tsx`, `scheduleRecalc`).
- Ogni modifica a parametro org o carico funzione viene loggata in
  `Modifica` prima di essere applicata — è la base sia di Undo che dello
  Storico, un'unica fonte di verità.
