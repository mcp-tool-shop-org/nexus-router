<p align="center">
  <a href="README.ja.md">日本語</a> | <a href="README.zh.md">中文</a> | <a href="README.es.md">Español</a> | <a href="README.fr.md">Français</a> | <a href="README.hi.md">हिन्दी</a> | <a href="README.it.md">Italiano</a> | <a href="README.pt-BR.md">Português (BR)</a>
</p>

<p align="center">
  <img src="https://raw.githubusercontent.com/mcp-tool-shop-org/brand/main/logos/nexus-router/readme.png" width="400" />
</p>

<p align="center">
  <a href="https://github.com/mcp-tool-shop-org/nexus-router/actions/workflows/ci.yml"><img src="https://github.com/mcp-tool-shop-org/nexus-router/actions/workflows/ci.yml/badge.svg" alt="CI" /></a>
  <a href="https://pypi.org/project/nexus-router/"><img src="https://img.shields.io/pypi/v/nexus-router" alt="PyPI" /></a>
  <a href="https://codecov.io/gh/mcp-tool-shop-org/nexus-router"><img src="https://img.shields.io/codecov/c/github/mcp-tool-shop-org/nexus-router" alt="Coverage" /></a>
  <a href="https://github.com/mcp-tool-shop-org/nexus-router/blob/main/LICENSE"><img src="https://img.shields.io/github/license/mcp-tool-shop-org/nexus-router" alt="License: MIT" /></a>
  <a href="https://pypi.org/project/nexus-router/"><img src="https://img.shields.io/pypi/pyversions/nexus-router" alt="Python versions" /></a>
  <a href="https://mcp-tool-shop-org.github.io/nexus-router/"><img src="https://img.shields.io/badge/Landing_Page-live-blue" alt="Landing Page" /></a>
</p>

基于事件驱动的 MCP 路由器，具有溯源性和完整性。

---

## 平台理念

- **路由器是规则**——所有执行流程都通过事件日志进行。
- **适配器是公民**——它们必须遵守契约，否则无法运行。
- **契约优先于约定**——稳定性保证的版本化并强制执行。
- **执行前回放**——每次运行都可以在事后进行验证。
- **验证胜于信任**——`validate_adapter()` 在适配器触及生产环境之前运行。
- **自描述的生态系统**——文档由清单生成，而不是反过来。

## 品牌 + 工具 ID

| 键 | 值 |
|-----|-------|
| 品牌/仓库 | `nexus-router` |
| Python 包 | `nexus_router` |
| MCP 工具 ID | `nexus-router.run` |
| 作者 | [mcp-tool-shop](https://github.com/mcp-tool-shop-org) |
| 许可证 | MIT |

## 安装

```bash
pip install nexus-router
```

用于开发：

```bash
pip install -e ".[dev]"
```

## 快速示例

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

## 持久化

默认的 `db_path=":memory:"` 是临时存储。要持久化运行结果，请指定文件路径：

```python
resp = run({"goal": "demo"}, db_path="nexus-router.db")
```

## 可移植性 (v0.3+)

将运行结果导出为可移植的包，并导入到其他数据库：

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

**冲突模式：**
- `reject_on_conflict` (默认)：如果 `run_id` 已经存在，则失败。
- `new_run_id`：生成新的 `run_id`，并重映射所有引用。
- `overwrite`：替换现有的运行记录。

## 检查与回放 (v0.2+)

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

## 分发适配器 (v0.4+)

适配器执行工具调用。将适配器传递给 `run()` 函数：

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

### 子进程适配器

使用以下契约调用外部命令：

```bash
<base_cmd> call <tool> <method> --json-args-file <path>
```

外部命令必须：
- 从 `args` 文件读取 JSON 负载：`{"tool": "...", "method": "...", "args": {...}}`
- 在成功时将 JSON 结果打印到标准输出。
- 在成功时返回代码 0，在失败时返回非零代码。

错误代码：`TIMEOUT`，`NONZERO_EXIT`，`INVALID_JSON_OUTPUT`，`COMMAND_NOT_FOUND`

### 内置适配器

- `NullAdapter`：返回模拟输出（默认，用于 `dry_run`）。
- `FakeAdapter`：用于测试的可配置响应。

## 此版本的特点（以及不具备的特点）

v1.1 是一个**平台级**的、基于事件驱动的路由器，拥有完整的适配器生态系统（16 个模块，346 个测试）：

**核心路由器：**
- 具有单调递增序列的事件日志。
- 策略控制（`allow_apply`，`max_steps`）。
- 对所有请求进行模式验证。
- 包含 SHA256 摘要的溯源包。
- 具有完整性验证的导出/导入功能。
- 具有不变性检查的回放功能。
- 错误分类：操作错误与程序错误。

**适配器生态系统：**
- 具有正式适配器契约的文档 ([ADAPTER_SPEC.md](ADAPTER_SPEC.md))。
- `validate_adapter()`：合规性检查工具。
- `inspect_adapter()`：开发者体验入口。
- `generate_adapter_docs()`：自动生成的文档。
- 带有验证网关的 CI 模板。
- 2 分钟即可上手的适配器模板。

## 并发

每个运行只有一个写入器。不支持对相同 `run_id` 进行并发写入。

## 适配器生态系统 (v0.8+)

创建自定义适配器，将工具调用分发到任何后端。

### 官方适配器

| 适配器 | 描述 | 安装 |
|---------|-------------|---------|
| [nexus-router-adapter-http](https://github.com/mcp-tool-shop-org/nexus-router-adapter-http) | HTTP/REST 分发 | `pip install nexus-router-adapter-http` |
| [nexus-router-adapter-stdout](https://github.com/mcp-tool-shop-org/nexus-router-adapter-stdout) | 调试日志 | `pip install nexus-router-adapter-stdout` |

请参阅 [ADAPTERS.generated.md](ADAPTERS.generated.md) 以获取完整文档。

### 创建适配器

使用 [适配器模板](https://github.com/mcp-tool-shop-org/nexus-router-adapter-template)，可以在 2 分钟内创建新的适配器：

```bash
# Fork the template, then:
pip install -e ".[dev]"
pytest -v  # Validates against nexus-router spec
```

请参阅 [ADAPTER_SPEC.md](ADAPTER_SPEC.md) 以获取完整的契约。

### 验证工具

```python
from nexus_router.plugins import inspect_adapter

result = inspect_adapter(
    "nexus_router_adapter_http:create_adapter",
    config={"base_url": "https://example.com"},
)
print(result.render())  # Human-readable validation report
```

## 版本控制与稳定性

### v1.x 保证

以下内容在 v1.x 版本中是稳定的（v2.0 版本中仅有破坏性更改）：

| 接口 | 范围 |
|----------|-------|
| 验证检查 ID | `LOAD_OK`, `PROTOCOL_FIELDS`, `MANIFEST_*` 等。 |
| 清单模式 | `schema_version: 1` |
| 适配器工厂签名 | `create_adapter(*, adapter_id=None, **config)` |
| 能力集合 | `dry_run`（试运行）, `apply`（应用）, `timeout`（超时）, `external`（外部，仅为新增） |
| 事件类型 | 核心事件负载（仅为新增） |

### 弃用策略

- 在次版本中发布弃用通知，并附带警告。
- 在下一个主要版本中移除。
- 升级说明将在发布变更日志中提供。

### 适配器兼容性

适配器在它们的清单中声明支持的路由器版本：

```python
ADAPTER_MANIFEST = {
    "supported_router_versions": ">=1.0,<2.0",
    ...
}
```

`validate_adapter()` 工具用于检查兼容性。

## 安全性和数据范围

Nexus-router 是一个 **库**，它没有命令行界面，没有守护进程，也没有网络监听器。

- **涉及的数据：** 工具调用负载通过适配器路由，事件存储（SQLite 或内存），溯源记录（SHA256 摘要，仅追加），用于验证的 JSON 模式。
- **未涉及的数据：** 默认情况下，没有网络请求，没有用户凭据，没有遥测数据。
- **策略执行：** `allow_apply: false` 阻止破坏性操作，`max_steps` 限制执行范围，模式验证拒绝格式错误的输入。
- **无遥测：** 不收集任何数据，也不发送任何数据。

## 评估表

| 类别 | 分数 | 备注 |
|----------|-------|-------|
| A. 安全性 | 10/10 | SECURITY.md，策略执行，仅追加的溯源记录 |
| B. 错误处理 | 10/10 | 模式验证，结构化结果，优雅降级 |
| C. 运维文档 | 10/10 | README，CHANGELOG，**架构**，ADAPTER_SPEC，QUICKSTART |
| D. 发布质量 | 10/10 | CI（lint + mypy + 357 个测试），覆盖率，依赖项审计，验证 |
| E. 标识 | 10/10 | Logo，翻译，着陆页 |
| **Total** | **50/50** | |

---

<p align="center">
  Built by <a href="https://mcp-tool-shop.github.io/">MCP Tool Shop</a>
</p>
