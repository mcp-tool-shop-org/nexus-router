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

イベント駆動型MCPルーター。イベント履歴による追跡と整合性保証。

---

## プラットフォームの哲学

- **ルーターこそがルール**：すべての実行フローはイベントログを経由します。
- **アダプターは市民**：契約に従うか、実行されません。
- **契約が優先**：安定性の保証はバージョン管理され、強制されます。
- **実行前にリプレイ**：すべての実行は、事後検証が可能です。
- **信頼する前に検証**：`validate_adapter()` は、アダプターが本番環境に影響を与える前に実行されます。
- **自己記述型エコシステム**：マニフェストがドキュメントを生成し、その逆ではありません。

## ブランド + ツールID

| キー | 値 |
|-----|-------|
| ブランド / リポジトリ | `nexus-router` |
| Pythonパッケージ | `nexus_router` |
| MCPツールID | `nexus-router.run` |
| 作者 | [mcp-tool-shop](https://github.com/mcp-tool-shop-org) |
| ライセンス | MIT |

## インストール

```bash
pip install nexus-router
```

開発用：

```bash
pip install -e ".[dev]"
```

## 簡単な例

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

## 永続化

デフォルトの `db_path=":memory:"` は揮発性です。永続化のためにファイルパスを指定してください。

```python
resp = run({"goal": "demo"}, db_path="nexus-router.db")
```

## 移植性 (v0.3以降)

実行結果をポータブルなバンドルとしてエクスポートし、他のデータベースにインポートできます。

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

**競合モード:**
- `reject_on_conflict` (デフォルト)：`run_id` が存在する場合、エラーになります。
- `new_run_id`：新しい `run_id` を生成し、すべての参照を再マッピングします。
- `overwrite`：既存の実行を置き換えます。

## 検査とリプレイ (v0.2以降)

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

## アダプターのディスパッチ (v0.4以降)

アダプターは、ツールの呼び出しを実行します。`run()` にアダプターを渡します。

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

この契約に従って、外部コマンドを呼び出します。

```bash
<base_cmd> call <tool> <method> --json-args-file <path>
```

外部コマンドは、以下の条件を満たす必要があります。
- `args` ファイルからJSONペイロードを読み取る：`{"tool": "...", "method": "...", "args": {...}}`
- 成功した場合、JSON結果を標準出力に出力する。
- 成功した場合はコード0で終了し、失敗した場合は0以外のコードで終了する。

エラーコード：`TIMEOUT`, `NONZERO_EXIT`, `INVALID_JSON_OUTPUT`, `COMMAND_NOT_FOUND`

### 組み込みアダプター

- `NullAdapter`：シミュレートされた出力を返します（デフォルト、`dry_run`で使用）。
- `FakeAdapter`：テスト用の設定可能な応答。

## このバージョンとは何か、そして何ではないのか

v1.1 は、完全なアダプターエコシステム（16のモジュール、346のテスト）を備えた、**プラットフォームグレード**のイベント駆動型ルーターです。

**コアルーター:**
- 単調シーケンスを持つイベントログ
- ポリシーゲート (`allow_apply`, `max_steps`)
- すべてのリクエストに対するスキーマ検証
- SHA256ダイジェストを持つプロビナンスバンドル
- 整合性検証によるエクスポート/インポート
- 不変性チェックによるリプレイ
- エラーの分類：運用エラーとバグエラー

**アダプターエコシステム:**
- 正式なアダプター契約 ([ADAPTER_SPEC.md](ADAPTER_SPEC.md))
- `validate_adapter()`：コンプライアンスLintツール
- `inspect_adapter()`：開発者向けのフロントドア
- `generate_adapter_docs()`：自動生成されたドキュメント
- 検証ゲート付きのCIテンプレート
- 2分でオンボーディングできるアダプターテンプレート

## 並行処理

1つの実行につき、単一の書き込み元。同じ `run_id` への同時書き込みはサポートされていません。

## アダプターエコシステム (v0.8以降)

カスタムアダプターを作成して、任意のバックエンドにツールの呼び出しをディスパッチします。

### 公式アダプター

| アダプター | 説明 | インストール |
|---------|-------------|---------|
| [nexus-router-adapter-http](https://github.com/mcp-tool-shop-org/nexus-router-adapter-http) | HTTP/RESTディスパッチ | `pip install nexus-router-adapter-http` |
| [nexus-router-adapter-stdout](https://github.com/mcp-tool-shop-org/nexus-router-adapter-stdout) | デバッグログ | `pip install nexus-router-adapter-stdout` |

詳細については、[ADAPTERS.generated.md](ADAPTERS.generated.md) を参照してください。

### アダプターの作成

[アダプターテンプレート](https://github.com/mcp-tool-shop-org/nexus-router-adapter-template) を使用して、2分で新しいアダプターを作成できます。

```bash
# Fork the template, then:
pip install -e ".[dev]"
pytest -v  # Validates against nexus-router spec
```

完全な契約については、[ADAPTER_SPEC.md](ADAPTER_SPEC.md) を参照してください。

### 検証ツール

```python
from nexus_router.plugins import inspect_adapter

result = inspect_adapter(
    "nexus_router_adapter_http:create_adapter",
    config={"base_url": "https://example.com"},
)
print(result.render())  # Human-readable validation report
```

## バージョン管理と安定性

### v1.x の保証事項

以下の項目は、**v1.xで安定している**（v2.0でのみ互換性のない変更があります）。

| 契約 | スコープ |
|----------|-------|
| 検証チェックID | `LOAD_OK`, `PROTOCOL_FIELDS`, `MANIFEST_*` など |
| マニフェストスキーマ | `schema_version: 1` |
| アダプターファクトリのシグネチャ | `create_adapter(*, adapter_id=None, **config)` |
| 機能セット | `dry_run`, `apply`, `timeout`, `external`（追加のみ） |
| イベントタイプ | コアイベントペイロード（追加のみ） |

### 非推奨ポリシー

- マイナーバージョンで警告とともに非推奨がアナウンスされます。
- 次のメジャーバージョンで削除されます。
- アップグレードに関する情報は、リリース変更ログに記載されています。

### アダプターの互換性

アダプターは、サポートするルーターのバージョンをマニフェストに宣言します。

```python
ADAPTER_MANIFEST = {
    "supported_router_versions": ">=1.0,<2.0",
    ...
}
```

`validate_adapter()` ツールは、互換性をチェックします。

## セキュリティとデータスコープ

Nexus-routerは**ライブラリ**です。CLI、デーモン、ネットワークリスナーはありません。

- **アクセスされるデータ:** ツール呼び出しのペイロードはアダプターを介してルーティングされ、イベントストア（SQLiteまたはインメモリ）、プロビナンスレコード（SHA256ハッシュ、追記専用）、検証用のJSONスキーマが含まれます。
- **アクセスされないデータ:** デフォルトでは、ネットワークリクエストは行われず、ユーザー認証情報も使用されず、テレメトリも収集されません。
- **ポリシーの適用:** `allow_apply: false` は破壊的な操作を防止し、`max_steps` は実行範囲を制限し、スキーマ検証は不正な入力を拒否します。
- **テレメトリなし:** 何も収集せず、何も送信しません。

## スコアカード

| カテゴリ | スコア | 備考 |
|----------|-------|-------|
| A. セキュリティ | 10/10 | SECURITY.md、ポリシー適用、追記専用のプロビナンス |
| B. エラー処理 | 10/10 | スキーマ検証、構造化された結果、正常なエラー処理 |
| C. 運用ドキュメント | 10/10 | README、CHANGELOG、アーキテクチャ、アダプター仕様、クイックスタート |
| D. リリースの品質 | 10/10 | CI（lint + mypy + 357テスト）、カバレッジ、依存関係監査、検証 |
| E. アイデンティティ | 10/10 | ロゴ、翻訳、ランディングページ |
| **Total** | **50/50** | |

---

<p align="center">
  Built by <a href="https://mcp-tool-shop.github.io/">MCP Tool Shop</a>
</p>
