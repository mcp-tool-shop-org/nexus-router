<p align="center">
  <a href="README.ja.md">日本語</a> | <a href="README.zh.md">中文</a> | <a href="README.md">English</a> | <a href="README.fr.md">Français</a> | <a href="README.hi.md">हिन्दी</a> | <a href="README.it.md">Italiano</a> | <a href="README.pt-BR.md">Português (BR)</a>
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

Enrutador MCP basado en eventos, con trazabilidad e integridad.

---

## Filosofía de la plataforma

- **El enrutador es la ley:** todo el flujo de ejecución pasa por el registro de eventos.
- **Los adaptadores son ciudadanos:** deben cumplir con el contrato o no se ejecutan.
- **Contratos sobre convenciones:** las garantías de estabilidad están versionadas y se aplican.
- **Reproducción antes de la ejecución:** cada ejecución puede verificarse a posteriori.
- **Validación antes de la confianza:** `validate_adapter()` se ejecuta antes de que los adaptadores interactúen con el entorno de producción.
- **Ecosistema auto-descriptivo:** los manifiestos generan la documentación, no al revés.

## Marca + ID de la herramienta

| Clave | Valor |
| ----- | ------- |
| Marca / repositorio | `nexus-router` |
| Paquete de Python | `nexus_router` |
| ID de la herramienta MCP | `nexus-router.run` |
| Autor | [mcp-tool-shop](https://github.com/mcp-tool-shop-org) |
| Licencia | MIT |

## Instalación

```bash
pip install nexus-router
```

Para desarrollo:

```bash
pip install -e ".[dev]"
```

## Ejemplo rápido

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

## Persistencia

La ruta predeterminada `db_path=":memory:"` es efímera.  Para persistir las ejecuciones, especifique una ruta de archivo:

```python
resp = run({"goal": "demo"}, db_path="nexus-router.db")
```

## Portabilidad (v0.3+)

Exporte las ejecuciones como paquetes portátiles e impórtelas a otras bases de datos:

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

**Modos de conflicto:**
- `reject_on_conflict` (predeterminado): Falla si `run_id` ya existe.
- `new_run_id`: Genera un nuevo `run_id` y remapea todas las referencias.
- `overwrite`: Reemplaza la ejecución existente.

## Inspección y reproducción (v0.2+)

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

## Despacho de adaptadores (v0.4+)

Los adaptadores ejecutan llamadas a la herramienta. Pase un adaptador a `run()`:

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

Llama a comandos externos con este contrato:

```bash
<base_cmd> call <tool> <method> --json-args-file <path>
```

El comando externo debe:
- Leer el payload JSON del archivo de argumentos: `{"tool": "...", "method": "...", "args": {...}}`
- Imprimir el resultado JSON en la salida estándar en caso de éxito.
- Salir con código 0 en caso de éxito y con un código distinto de cero en caso de fallo.

Códigos de error: `TIMEOUT`, `NONZERO_EXIT`, `INVALID_JSON_OUTPUT`, `COMMAND_NOT_FOUND`

### Adaptadores integrados

- `NullAdapter`: Devuelve una salida simulada (predeterminado, utilizado en `dry_run`).
- `FakeAdapter`: Respuestas configurables para pruebas.

## ¿Qué es y qué no es esta versión?

v1.1 es un enrutador basado en eventos de **calidad de plataforma** con un ecosistema de adaptadores completo (16 módulos, 346 pruebas):

**Enrutador central:**
- Registro de eventos con secuenciación monótona.
- Control de políticas (`allow_apply`, `max_steps`).
- Validación de esquema en todas las solicitudes.
- Paquete de trazabilidad con digest SHA256.
- Exportación/importación con verificación de integridad.
- Reproducción con verificación de invariantes.
- Taxonomía de errores: errores operativos vs. errores de programación.

**Ecosistema de adaptadores:**
- Contrato formal de adaptador ([ADAPTER_SPEC.md](ADAPTER_SPEC.md)).
- `validate_adapter()`: herramienta de linting de cumplimiento.
- `inspect_adapter()`: puerta de entrada para la experiencia del desarrollador.
- `generate_adapter_docs()`: documentación generada automáticamente.
- Plantilla de CI con puerta de validación.
- Plantilla de adaptador para una incorporación en 2 minutos.

## Concurrencia

Un solo escritor por ejecución. No se admiten escritores concurrentes para el mismo `run_id`.

## Ecosistema de adaptadores (v0.8+)

Cree adaptadores personalizados para enviar llamadas a herramientas a cualquier backend.

### Adaptadores oficiales

| Adaptador | Descripción | Instalación |
| --------- | ------------- | --------- |
| [nexus-router-adapter-http](https://github.com/mcp-tool-shop-org/nexus-router-adapter-http) | Despacho HTTP/REST | `pip install nexus-router-adapter-http` |
| [nexus-router-adapter-stdout](https://github.com/mcp-tool-shop-org/nexus-router-adapter-stdout) | Registro de depuración | `pip install nexus-router-adapter-stdout` |

Consulte [ADAPTERS.generated.md](ADAPTERS.generated.md) para obtener la documentación completa.

### Creación de adaptadores

Utilice la [plantilla de adaptador](https://github.com/mcp-tool-shop-org/nexus-router-adapter-template) para crear nuevos adaptadores en 2 minutos:

```bash
# Fork the template, then:
pip install -e ".[dev]"
pytest -v  # Validates against nexus-router spec
```

Consulte [ADAPTER_SPEC.md](ADAPTER_SPEC.md) para obtener el contrato completo.

### Herramientas de validación

```python
from nexus_router.plugins import inspect_adapter

result = inspect_adapter(
    "nexus_router_adapter_http:create_adapter",
    config={"base_url": "https://example.com"},
)
print(result.render())  # Human-readable validation report
```

## Control de versiones y estabilidad

### Garantías de la versión 1.x

Los siguientes elementos son **estables en la versión 1.x** (solo se realizan cambios importantes en la versión 2.0):

| Contrato | Alcance |
| ---------- | ------- |
| Identificadores de verificación de validación | `LOAD_OK`, `PROTOCOL_FIELDS`, `MANIFEST_*`, etc. |
| Esquema del manifiesto | `schema_version: 1` |
| Firma de la fábrica de adaptadores | `create_adapter(*, adapter_id=None, **config)` |
| Conjunto de capacidades | `dry_run`, `apply`, `timeout`, `external` (solo se agregan) |
| Tipos de eventos | Cargas útiles de eventos principales (solo se agregan) |

### Política de obsolescencia

- Las funcionalidades obsoletas se anuncian en versiones menores con advertencias.
- Se eliminan en la siguiente versión principal.
- Se proporcionan notas de actualización en el registro de cambios de la versión.

### Compatibilidad de adaptadores

Los adaptadores declaran las versiones de router compatibles en su manifiesto:

```python
ADAPTER_MANIFEST = {
    "supported_router_versions": ">=1.0,<2.0",
    ...
}
```

La herramienta `validate_adapter()` verifica la compatibilidad.

---

<p align="center">
  Built by <a href="https://mcp-tool-shop.github.io/">MCP Tool Shop</a>
</p>
