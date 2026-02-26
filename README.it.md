<p align="center">
  <a href="README.ja.md">日本語</a> | <a href="README.zh.md">中文</a> | <a href="README.es.md">Español</a> | <a href="README.fr.md">Français</a> | <a href="README.hi.md">हिन्दी</a> | <a href="README.md">English</a> | <a href="README.pt-BR.md">Português (BR)</a>
</p>

<p align="center">
  <img src="https://raw.githubusercontent.com/mcp-tool-shop-org/brand/main/logos/nexus-router/readme.png" width="400" />
</p>

<p align="center">
  <a href="https://github.com/mcp-tool-shop-org/nexus-router/actions/workflows/ci.yml"><img src="https://github.com/mcp-tool-shop-org/nexus-router/actions/workflows/ci.yml/badge.svg" alt="CI" /></a>
  <a href="https://pypi.org/project/nexus-router/"><img src="https://img.shields.io/pypi/v/nexus-router" alt="PyPI" /></a>
  <a href="https://github.com/mcp-tool-shop-org/nexus-router/blob/main/LICENSE"><img src="https://img.shields.io/github/license/mcp-tool-shop-org/nexus-router" alt="License: MIT" /></a>
  <a href="https://pypi.org/project/nexus-router/"><img src="https://img.shields.io/pypi/pyversions/nexus-router" alt="Python versions" /></a>
  <a href="https://mcp-tool-shop-org.github.io/nexus-router/"><img src="https://img.shields.io/badge/Landing_Page-live-blue" alt="Landing Page" /></a>
</p>

Event-sourced MCP router con tracciabilità e integrità.

---

## Filosofia della piattaforma

- **Il router è la legge:** tutti i flussi di esecuzione passano attraverso il log degli eventi.
- **Gli adapter sono cittadini:** devono rispettare il contratto o non funzionano.
- **Contratti rispetto alle convenzioni:** le garanzie di stabilità sono versionate e applicate.
- **Riproduzione prima dell'esecuzione:** ogni esecuzione può essere verificata a posteriori.
- **Validazione prima della fiducia:** la funzione `validate_adapter()` viene eseguita prima che gli adapter interagiscano con l'ambiente di produzione.
- **Ecosistema auto-descrittivo:** i manifest generano la documentazione, non viceversa.

## Brand + Tool ID

| Chiave | Valore |
| ----- | ------- |
| Brand / repository | `nexus-router` |
| Pacchetto Python | `nexus_router` |
| ID strumento MCP | `nexus-router.run` |
| Autore | [mcp-tool-shop](https://github.com/mcp-tool-shop-org) |
| Licenza | MIT |

## Installazione

```bash
pip install nexus-router
```

Per lo sviluppo:

```bash
pip install -e ".[dev]"
```

## Esempio rapido

```python
from nexus_router.tool import run

resp = run({
  "goal": "demo",
  "mode": "dry_run",
  "plan_override": []
})

print(resp["run"]["run_id"])
print(resp["summary"])
```

## Persistenza

Il percorso predefinito `db_path=":memory:"` è volatile. Per rendere persistenti le esecuzioni, specificare un percorso di file:

```python
resp = run({"goal": "demo"}, db_path="nexus-router.db")
```

## Portabilità (v0.3+)

Esportare le esecuzioni come pacchetti portabili e importarli in altri database:

```python
from nexus_router.tool import run, export, import_bundle, replay

# Create a run
resp = run({"goal": "demo", "mode": "dry_run", "plan_override": []}, db_path="source.db")
run_id = resp["run"]["run_id"]

# Export to bundle
bundle = export({"db_path": "source.db", "run_id": run_id})["artifact"]

# Import into another database
result = import_bundle({"db_path": "target.db", "bundle": bundle})
print(result["imported_run_id"])  # same run_id
print(result["replay_ok"])        # True (auto-verified)
```

**Modalità di conflitto:**
- `reject_on_conflict` (predefinito): fallisce se `run_id` esiste già.
- `new_run_id`: genera un nuovo `run_id` e rimappa tutti i riferimenti.
- `overwrite`: sovrascrive l'esecuzione esistente.

## Ispezione e riproduzione (v0.2+)

```python
from nexus_router.tool import inspect, replay

# List runs in a database
info = inspect({"db_path": "nexus.db"})
print(info["counts"])  # {"total": 5, "completed": 4, "failed": 1, "running": 0}

# Replay and check invariants
result = replay({"db_path": "nexus.db", "run_id": "..."})
print(result["ok"])          # True if no violations
print(result["violations"])  # [] or list of issues
```

## Dispatch di adapter (v0.4+)

Gli adapter eseguono chiamate di strumenti. Passare un adapter alla funzione `run()`:

```python
from nexus_router.tool import run
from nexus_router.dispatch import SubprocessAdapter

# Create adapter for external command
adapter = SubprocessAdapter(
    ["python", "-m", "my_tool_cli"],
    timeout_s=30.0,
)

resp = run({
    "goal": "execute real tool",
    "mode": "apply",
    "policy": {"allow_apply": True},
    "plan_override": [
        {"step_id": "s1", "intent": "do something", "call": {"tool": "my-tool", "method": "action", "args": {"x": 1}}}
    ]
}, adapter=adapter)
```

### SubprocessAdapter

Esegue comandi esterni con il seguente contratto:

```bash
<base_cmd> call <tool> <method> --json-args-file <path>
```

Il comando esterno deve:
- Leggere il payload JSON dal file degli argomenti: `{"tool": "...", "method": "...", "args": {...}}`
- Stampare il risultato JSON su stdout in caso di successo.
- Uscire con codice 0 in caso di successo, con un codice diverso da zero in caso di errore.

Codici di errore: `TIMEOUT`, `NONZERO_EXIT`, `INVALID_JSON_OUTPUT`, `COMMAND_NOT_FOUND`

### Adapter integrati

- `NullAdapter`: restituisce un output simulato (predefinito, utilizzato in `dry_run`).
- `FakeAdapter`: risposte configurabili per i test.

## Cosa è (e cosa non è) questa versione

La versione v1.1 è un router event-sourced di livello piattaforma con un ecosistema di adapter completo (16 moduli, 346 test):

**Router principale:**
- Log degli eventi con sequenziamento monotono.
- Policy gating (`allow_apply`, `max_steps`).
- Validazione dello schema per tutte le richieste.
- Bundle di provenienza con digest SHA256.
- Esportazione/importazione con verifica dell'integrità.
- Riproduzione con controllo delle invarianti.
- Tassonomia degli errori: errori operativi vs. errori di bug.

**Ecosistema di adapter:**
- Contratto formale per gli adapter ([ADAPTER_SPEC.md](ADAPTER_SPEC.md)).
- `validate_adapter()`: strumento di linting per la conformità.
- `inspect_adapter()`: interfaccia per gli sviluppatori.
- `generate_adapter_docs()`: documentazione generata automaticamente.
- Template CI con gate di validazione.
- Template per adapter per l'onboarding in 2 minuti.

## Concurrency

Un solo writer per esecuzione. Gli writer concorrenti sullo stesso `run_id` non sono supportati.

## Ecosistema di adapter (v0.8+)

Creare adapter personalizzati per dispatchare chiamate di strumenti a qualsiasi backend.

### Adapter ufficiali

| Adapter | Descrizione | Installazione |
| --------- | ------------- | --------- |
| [nexus-router-adapter-http](https://github.com/mcp-tool-shop-org/nexus-router-adapter-http) | Dispatch HTTP/REST | `pip install nexus-router-adapter-http` |
| [nexus-router-adapter-stdout](https://github.com/mcp-tool-shop-org/nexus-router-adapter-stdout) | Debug logging | `pip install nexus-router-adapter-stdout` |

Consultare [ADAPTERS.generated.md](ADAPTERS.generated.md) per la documentazione completa.

### Creazione di adapter

Utilizzare il [template per adapter](https://github.com/mcp-tool-shop-org/nexus-router-adapter-template) per creare nuovi adapter in 2 minuti:

```bash
# Fork the template, then:
pip install -e ".[dev]"
pytest -v  # Validates against nexus-router spec
```

Consultare [ADAPTER_SPEC.md](ADAPTER_SPEC.md) per il contratto completo.

### Strumenti di validazione

```python
from nexus_router.plugins import inspect_adapter

result = inspect_adapter(
    "nexus_router_adapter_http:create_adapter",
    config={"base_url": "https://example.com"},
)
print(result.render())  # Human-readable validation report
```

## Versioni e stabilità

### Garanzie per la versione 1.x

I seguenti elementi sono **stabili nella versione 1.x** (modifiche incompatibili solo nella versione 2.0):

| Contratto | Ambito |
| ---------- | ------- |
| ID dei controlli di validazione | `LOAD_OK`, `PROTOCOL_FIELDS`, `MANIFEST_*`, ecc. |
| Schema del manifest | `schema_version: 1` |
| Firma della factory dell'adattatore | `create_adapter(*, adapter_id=None, **config)` |
| Insieme di funzionalità | `dry_run`, `apply`, `timeout`, `external` (solo aggiunte) |
| Tipi di eventi | Payload degli eventi principali (solo aggiunte) |

### Politica di obsolescenza

- Le obsolescenze vengono annunciate nelle versioni minori con avvisi.
- Vengono rimosse nella versione principale successiva.
- Le note di aggiornamento sono fornite nel changelog della release.

### Compatibilità degli adattatori

Gli adattatori dichiarano le versioni del router supportate nel loro manifest:

```python
ADAPTER_MANIFEST = {
    "supported_router_versions": ">=1.0,<2.0",
    ...
}
```

Lo strumento `validate_adapter()` verifica la compatibilità.

---

<p align="center">
  Built by <a href="https://mcp-tool-shop.github.io/">MCP Tool Shop</a>
</p>
