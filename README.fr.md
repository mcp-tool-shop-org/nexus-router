<p align="center">
  <a href="README.ja.md">日本語</a> | <a href="README.zh.md">中文</a> | <a href="README.es.md">Español</a> | <a href="README.md">English</a> | <a href="README.hi.md">हिन्दी</a> | <a href="README.it.md">Italiano</a> | <a href="README.pt-BR.md">Português (BR)</a>
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

Event-sourced MCP router avec traçabilité et intégrité.

---

## Philosophie de la plateforme

- **Le routeur est la loi** : tous les flux d'exécution passent par le journal des événements.
- **Les adaptateurs sont des citoyens** : ils respectent le contrat ou ils ne fonctionnent pas.
- **Contrats plutôt que conventions** : la stabilité est garantie par des versions et est appliquée.
- **Rejouer avant l'exécution** : chaque exécution peut être vérifiée a posteriori.
- **Validation avant confiance** : `validate_adapter()` s'exécute avant que les adaptateurs n'accèdent à la production.
- **Écosystème auto-descriptif** : les manifestes génèrent la documentation, et non l'inverse.

## Marque + ID de l'outil

| Clé | Valeur |
| ----- | ------- |
| Marque / dépôt | `nexus-router` |
| Package Python | `nexus_router` |
| ID de l'outil MCP | `nexus-router.run` |
| Auteur | [mcp-tool-shop](https://github.com/mcp-tool-shop-org) |
| Licence | MIT |

## Installation

```bash
pip install nexus-router
```

Pour le développement :

```bash
pip install -e ".[dev]"
```

## Exemple rapide

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

## Persistance

Par défaut, `db_path=":memory:"` est éphémère. Pour persister les exécutions, spécifiez un chemin de fichier :

```python
resp = run({"goal": "demo"}, db_path="nexus-router.db")
```

## Portabilité (v0.3+)

Exportez les exécutions sous forme de paquets portables et importez-les dans d'autres bases de données :

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

**Modes de résolution des conflits :**
- `reject_on_conflict` (par défaut) : échoue si `run_id` existe.
- `new_run_id` : génère un nouveau `run_id`, remet en correspondance toutes les références.
- `overwrite` : remplace l'exécution existante.

## Inspection et relecture (v0.2+)

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

## Dispatch d'adaptateurs (v0.4+)

Les adaptateurs exécutent les appels d'outils. Passez un adaptateur à `run()` :

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

Exécute des commandes externes selon ce contrat :

```bash
<base_cmd> call <tool> <method> --json-args-file <path>
```

La commande externe doit :
- Lire une charge utile JSON à partir du fichier d'arguments : `{"tool": "...", "method": "...", "args": {...}}`
- Imprimer le résultat JSON sur la sortie standard en cas de succès.
- Quitter avec le code 0 en cas de succès, et un code non nul en cas d'échec.

Codes d'erreur : `TIMEOUT`, `NONZERO_EXIT`, `INVALID_JSON_OUTPUT`, `COMMAND_NOT_FOUND`.

### Adaptateurs intégrés

- `NullAdapter` : renvoie une sortie simulée (par défaut, utilisé dans `dry_run`).
- `FakeAdapter` : réponses configurables pour les tests.

## Ce que cette version est (et n'est pas)

v1.1 est un routeur événementiel de qualité plateforme avec un écosystème d'adaptateurs complet (16 modules, 346 tests) :

**Routeur principal :**
- Journal des événements avec séquencement monotone.
- Contrôle des politiques (`allow_apply`, `max_steps`).
- Validation du schéma pour toutes les requêtes.
- Paquet de traçabilité avec digest SHA256.
- Exportation/importation avec vérification de l'intégrité.
- Relecture avec vérification des invariants.
- Taxonomie des erreurs : erreurs opérationnelles vs erreurs de bug.

**Écosystème d'adaptateurs :**
- Contrat formel pour les adaptateurs ([ADAPTER_SPEC.md](ADAPTER_SPEC.md)).
- `validate_adapter()` : outil de contrôle de conformité.
- `inspect_adapter()` : interface pour les développeurs.
- `generate_adapter_docs()` : documentation générée automatiquement.
- Modèle CI avec contrôle de validation.
- Modèle d'adaptateur pour une intégration en 2 minutes.

## Concurrence

Un seul écrivain par exécution. Les écrivains concurrents vers le même `run_id` ne sont pas pris en charge.

## Écosystème d'adaptateurs (v0.8+)

Créez des adaptateurs personnalisés pour dispatcher les appels d'outils vers n'importe quel backend.

### Adaptateurs officiels

| Adaptateur | Description | Installation |
| --------- | ------------- | --------- |
| [nexus-router-adapter-http](https://github.com/mcp-tool-shop-org/nexus-router-adapter-http) | Dispatch HTTP/REST | `pip install nexus-router-adapter-http` |
| [nexus-router-adapter-stdout](https://github.com/mcp-tool-shop-org/nexus-router-adapter-stdout) | Journalisation de débogage | `pip install nexus-router-adapter-stdout` |

Consultez [ADAPTERS.generated.md](ADAPTERS.generated.md) pour une documentation complète.

### Création d'adaptateurs

Utilisez le [modèle d'adaptateur](https://github.com/mcp-tool-shop-org/nexus-router-adapter-template) pour créer de nouveaux adaptateurs en 2 minutes :

```bash
# Fork the template, then:
pip install -e ".[dev]"
pytest -v  # Validates against nexus-router spec
```

Consultez [ADAPTER_SPEC.md](ADAPTER_SPEC.md) pour le contrat complet.

### Outils de validation

```python
from nexus_router.plugins import inspect_adapter

result = inspect_adapter(
    "nexus_router_adapter_http:create_adapter",
    config={"base_url": "https://example.com"},
)
print(result.render())  # Human-readable validation report
```

## Gestion des versions et stabilité

### Garanties pour la version 1.x

Les éléments suivants sont **stables dans la version 1.x** (modifications majeures uniquement dans la version 2.0) :

| Contrat | Champ d'application |
| ---------- | ------- |
| Identifiants des vérifications de validation | `LOAD_OK`, `PROTOCOL_FIELDS`, `MANIFEST_*`, etc. |
| Schéma du manifeste | `schema_version: 1` |
| Signature de l'usine d'adaptateurs | `create_adapter(*, adapter_id=None, **config)` |
| Ensemble de fonctionnalités | `dry_run`, `apply`, `timeout`, `external` (ajout uniquement) |
| Types d'événements | Charges utiles des événements principaux (ajout uniquement) |

### Politique de dépréciation

- Les dépréciations sont annoncées dans les versions mineures avec des avertissements.
- Elles sont supprimées dans la version majeure suivante.
- Des notes de mise à niveau sont fournies dans le journal des modifications de la version.

### Compatibilité des adaptateurs

Les adaptateurs déclarent les versions de routeur prises en charge dans leur manifeste :

```python
ADAPTER_MANIFEST = {
    "supported_router_versions": ">=1.0,<2.0",
    ...
}
```

L'outil `validate_adapter()` vérifie la compatibilité.

---

<p align="center">
  Built by <a href="https://mcp-tool-shop.github.io/">MCP Tool Shop</a>
</p>
