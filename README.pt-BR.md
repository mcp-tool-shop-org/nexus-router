<p align="center">
  <a href="README.ja.md">日本語</a> | <a href="README.zh.md">中文</a> | <a href="README.es.md">Español</a> | <a href="README.fr.md">Français</a> | <a href="README.hi.md">हिन्दी</a> | <a href="README.it.md">Italiano</a> | <a href="README.md">English</a>
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

Roteador MCP baseado em eventos, com rastreabilidade e integridade.

---

## Filosofia da Plataforma

- **O roteador é a lei** — todo o fluxo de execução passa pelo registro de eventos.
- **Adaptadores são cidadãos** — eles seguem o contrato ou não são executados.
- **Contratos sobre convenções** — as garantias de estabilidade são versionadas e aplicadas.
- **Reprodução antes da execução** — cada execução pode ser verificada posteriormente.
- **Validação antes da confiança** — a função `validate_adapter()` é executada antes que os adaptadores acessem o ambiente de produção.
- **Ecossistema autoexplicativo** — os manifestos geram a documentação, não o contrário.

## Marca + ID da Ferramenta

| Chave | Valor |
| ----- | ------- |
| Marca / repositório | `nexus-router` |
| Pacote Python | `nexus_router` |
| ID da ferramenta MCP | `nexus-router.run` |
| Autor | [mcp-tool-shop](https://github.com/mcp-tool-shop-org) |
| Licença | MIT |

## Instalação

```bash
pip install nexus-router
```

Para desenvolvimento:

```bash
pip install -e ".[dev]"
```

## Exemplo Rápido

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

## Persistência

O caminho padrão `db_path=":memory:"` é efêmero. Passe um caminho de arquivo para persistir as execuções:

```python
resp = run({"goal": "demo"}, db_path="nexus-router.db")
```

## Portabilidade (v0.3+)

Exporte as execuções como pacotes portáteis e importe-as para outros bancos de dados:

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

**Modos de conflito:**
- `reject_on_conflict` (padrão): Falha se o `run_id` já existir.
- `new_run_id`: Gera um novo `run_id`, remapeando todas as referências.
- `overwrite`: Substitui a execução existente.

## Inspeção e Reprodução (v0.2+)

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

## Disparo de Adaptadores (v0.4+)

Os adaptadores executam chamadas de ferramentas. Passe um adaptador para a função `run()`:

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

Chama comandos externos com este contrato:

```bash
<base_cmd> call <tool> <method> --json-args-file <path>
```

O comando externo deve:
- Ler o payload JSON do arquivo de argumentos: `{"tool": "...", "method": "...", "args": {...}}`.
- Imprimir o resultado JSON no stdout em caso de sucesso.
- Sair com código 0 em caso de sucesso e com um código diferente de zero em caso de falha.

Códigos de erro: `TIMEOUT`, `NONZERO_EXIT`, `INVALID_JSON_OUTPUT`, `COMMAND_NOT_FOUND`.

### Adaptadores Integrados

- `NullAdapter`: Retorna uma saída simulada (padrão, usado em `dry_run`).
- `FakeAdapter`: Respostas configuráveis para testes.

## O que esta versão é (e não é)

v1.1 é um roteador baseado em eventos de nível de plataforma, com um ecossistema completo de adaptadores (16 módulos, 346 testes):

**Roteador Principal:**
- Registro de eventos com sequenciamento monotônico.
- Controle de políticas (`allow_apply`, `max_steps`).
- Validação de esquema em todas as solicitações.
- Pacote de rastreabilidade com digest SHA256.
- Exportação/importação com verificação de integridade.
- Reprodução com verificação de invariantes.
- Taxonomia de erros: erros operacionais vs. erros de bug.

**Ecossistema de Adaptadores:**
- Contrato formal de adaptador ([ADAPTER_SPEC.md](ADAPTER_SPEC.md)).
- `validate_adapter()` — ferramenta de lint de conformidade.
- `inspect_adapter()` — porta de entrada para a experiência do desenvolvedor.
- `generate_adapter_docs()` — documentação gerada automaticamente.
- Modelo de CI com porta de validação.
- Modelo de adaptador para integração em 2 minutos.

## Concorrência

Um único escritor por execução. Escritores concorrentes para o mesmo `run_id` não são suportados.

## Ecossistema de Adaptadores (v0.8+)

Crie adaptadores personalizados para direcionar chamadas de ferramentas para qualquer backend.

### Adaptadores Oficiais

| Adaptador | Descrição | Instalação |
| --------- | ------------- | --------- |
| [nexus-router-adapter-http](https://github.com/mcp-tool-shop-org/nexus-router-adapter-http) | Disparo HTTP/REST | `pip install nexus-router-adapter-http` |
| [nexus-router-adapter-stdout](https://github.com/mcp-tool-shop-org/nexus-router-adapter-stdout) | Registro de depuração | `pip install nexus-router-adapter-stdout` |

Consulte [ADAPTERS.generated.md](ADAPTERS.generated.md) para obter a documentação completa.

### Criação de Adaptadores

Use o [modelo de adaptador](https://github.com/mcp-tool-shop-org/nexus-router-adapter-template) para criar novos adaptadores em 2 minutos:

```bash
# Fork the template, then:
pip install -e ".[dev]"
pytest -v  # Validates against nexus-router spec
```

Consulte [ADAPTER_SPEC.md](ADAPTER_SPEC.md) para obter o contrato completo.

### Ferramentas de Validação

```python
from nexus_router.plugins import inspect_adapter

result = inspect_adapter(
    "nexus_router_adapter_http:create_adapter",
    config={"base_url": "https://example.com"},
)
print(result.render())  # Human-readable validation report
```

## Versionamento e Estabilidade

### Garantias da versão 1.x

Os seguintes itens são **estáveis na versão 1.x** (alterações incompatíveis apenas na versão 2.0):

| Contrato | Escopo |
| ---------- | ------- |
| IDs de verificação de validação | `LOAD_OK`, `PROTOCOL_FIELDS`, `MANIFEST_*`, etc. |
| Esquema do manifesto | `schema_version: 1` |
| Assinatura da fábrica de adaptadores | `create_adapter(*, adapter_id=None, **config)` |
| Conjunto de capacidades | `dry_run`, `apply`, `timeout`, `external` (apenas opcionais) |
| Tipos de eventos | Cargas úteis de eventos principais (apenas opcionais) |

### Política de Descontinuação

- Descontinuações anunciadas em versões menores com avisos.
- Removidas na próxima versão principal.
- Notas de atualização fornecidas no changelog da versão.

### Compatibilidade de Adaptadores

Os adaptadores declaram as versões de roteador suportadas em seu manifesto:

```python
ADAPTER_MANIFEST = {
    "supported_router_versions": ">=1.0,<2.0",
    ...
}
```

A ferramenta `validate_adapter()` verifica a compatibilidade.

---

<p align="center">
  Built by <a href="https://mcp-tool-shop.github.io/">MCP Tool Shop</a>
</p>
