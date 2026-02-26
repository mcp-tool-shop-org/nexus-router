<p align="center">
  <a href="README.ja.md">日本語</a> | <a href="README.zh.md">中文</a> | <a href="README.es.md">Español</a> | <a href="README.fr.md">Français</a> | <a href="README.md">English</a> | <a href="README.it.md">Italiano</a> | <a href="README.pt-BR.md">Português (BR)</a>
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

इवेंट-आधारित एमसीपी राउटर, जिसमें उत्पत्ति और अखंडता शामिल है।

---

## प्लेटफ़ॉर्म दर्शन

- **राउटर ही नियम है** — सभी निष्पादन प्रवाह इवेंट लॉग के माध्यम से होता है।
- **एडाप्टर नागरिक हैं** — वे अनुबंध का पालन करते हैं या वे नहीं चलेंगे।
- **अनुबंध परंपराओं से बेहतर** — स्थिरता की गारंटी संस्करणित और लागू की जाती है।
- **निष्पादन से पहले पुनः चलाएं** — प्रत्येक रन को निष्पादन के बाद सत्यापित किया जा सकता है।
- **विश्वास करने से पहले सत्यापन** — `validate_adapter()` फ़ंक्शन उत्पादन में एडाप्टर के उपयोग से पहले चलता है।
- **स्व-वर्णनात्मक पारिस्थितिकी तंत्र** — मैनिफेस्ट दस्तावेज़ उत्पन्न करते हैं, इसके विपरीत नहीं।

## ब्रांड + टूल आईडी

| कुंजी | मान |
| ----- | ------- |
| ब्रांड / रिपॉजिटरी | `nexus-router` |
| पायथन पैकेज | `nexus_router` |
| एमसीपी टूल आईडी | `nexus-router.run` |
| लेखक | [mcp-tool-shop](https://github.com/mcp-tool-shop-org) |
| लाइसेंस | एमआईटी |

## इंस्टॉल करें

```bash
pip install nexus-router
```

विकास के लिए:

```bash
pip install -e ".[dev]"
```

## त्वरित उदाहरण

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

## स्थायित्व

डिफ़ॉल्ट `db_path=":memory:"` अस्थायी है। रन को स्थायी करने के लिए एक फ़ाइल पथ निर्दिष्ट करें:

```python
resp = run({"goal": "demo"}, db_path="nexus-router.db")
```

## पोर्टेबिलिटी (v0.3+)

पोर्टेबल बंडलों के रूप में रन निर्यात करें और उन्हें अन्य डेटाबेस में आयात करें:

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

**संघर्ष मोड:**
- `reject_on_conflict` (डिफ़ॉल्ट): यदि `run_id` मौजूद है तो विफल हो जाएं।
- `new_run_id`: एक नया `run_id` उत्पन्न करें, सभी संदर्भों को पुनः मैप करें।
- `overwrite`: मौजूदा रन को बदलें।

## निरीक्षण और पुनः चलाना (v0.2+)

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

## एडाप्टर निष्पादित करें (v0.4+)

एडाप्टर टूल कॉल निष्पादित करते हैं। `run()` फ़ंक्शन में एक एडाप्टर पास करें:

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

### सबप्रोसेसएडाप्टर

यह अनुबंध के साथ बाहरी कमांड को कॉल करता है:

```bash
<base_cmd> call <tool> <method> --json-args-file <path>
```

बाहरी कमांड को:
- `args` फ़ाइल से JSON पेलोड पढ़ना चाहिए: `{"tool": "...", "method": "...", "args": {...}}`
- सफलता पर stdout पर JSON परिणाम प्रिंट करना चाहिए।
- सफलता पर कोड 0 के साथ बाहर निकलें, विफलता पर गैर-शून्य।

त्रुटि कोड: `TIMEOUT`, `NONZERO_EXIT`, `INVALID_JSON_OUTPUT`, `COMMAND_NOT_FOUND`

### अंतर्निहित एडाप्टर

- `NullAdapter`: सिमुलेटेड आउटपुट लौटाता है (डिफ़ॉल्ट, `dry_run` में उपयोग किया जाता है)।
- `FakeAdapter`: परीक्षण के लिए कॉन्फ़िगर करने योग्य प्रतिक्रियाएं।

## यह संस्करण क्या है (और क्या नहीं)

v1.1 एक **प्लेटफ़ॉर्म-ग्रेड** इवेंट-आधारित राउटर है जिसमें एक पूर्ण एडाप्टर पारिस्थितिकी तंत्र है (16 मॉड्यूल, 346 परीक्षण):

**कोर राउटर:**
- मोनोटोनिक अनुक्रमण के साथ इवेंट लॉग।
- नीति गेटिंग (`allow_apply`, `max_steps`)।
- सभी अनुरोधों पर स्कीमा सत्यापन।
- SHA256 डाइजेस्ट के साथ उत्पत्ति बंडल।
- अखंडता सत्यापन के साथ निर्यात/आयात।
- अपरिवर्तनीय जांच के साथ पुनः चलाना।
- त्रुटि वर्गीकरण: परिचालन त्रुटियां बनाम बग त्रुटियां।

**एडाप्टर पारिस्थितिकी तंत्र:**
- औपचारिक एडाप्टर अनुबंध ([ADAPTER_SPEC.md](ADAPTER_SPEC.md))।
- `validate_adapter()` — अनुपालन लिंट टूल।
- `inspect_adapter()` — डेवलपर अनुभव का प्रवेश द्वार।
- `generate_adapter_docs()` — स्वचालित रूप से उत्पन्न दस्तावेज़।
- सत्यापन गेट के साथ CI टेम्पलेट।
- 2 मिनट में ऑनबोर्डिंग के लिए एडाप्टर टेम्पलेट।

## समवर्ती

प्रत्येक रन के लिए एकल लेखक। समान `run_id` के लिए समवर्ती लेखक समर्थित नहीं हैं।

## एडाप्टर पारिस्थितिकी तंत्र (v0.8+)

किसी भी बैकएंड पर टूल कॉल भेजने के लिए कस्टम एडाप्टर बनाएं।

### आधिकारिक एडाप्टर

| एडाप्टर | विवरण | इंस्टॉल करें |
| --------- | ------------- | --------- |
| [nexus-router-adapter-http](https://github.com/mcp-tool-shop-org/nexus-router-adapter-http) | HTTP/REST डिस्पैच | `pip install nexus-router-adapter-http` |
| [nexus-router-adapter-stdout](https://github.com/mcp-tool-shop-org/nexus-router-adapter-stdout) | डीबग लॉगिंग | `pip install nexus-router-adapter-stdout` |

पूर्ण दस्तावेज़ के लिए [ADAPTERS.generated.md](ADAPTERS.generated.md) देखें।

### एडाप्टर बनाना

नए एडाप्टर बनाने के लिए [एडाप्टर टेम्पलेट](https://github.com/mcp-tool-shop-org/nexus-router-adapter-template) का उपयोग करें:

```bash
# Fork the template, then:
pip install -e ".[dev]"
pytest -v  # Validates against nexus-router spec
```

पूर्ण अनुबंध के लिए [ADAPTER_SPEC.md](ADAPTER_SPEC.md) देखें।

### सत्यापन उपकरण

```python
from nexus_router.plugins import inspect_adapter

result = inspect_adapter(
    "nexus_router_adapter_http:create_adapter",
    config={"base_url": "https://example.com"},
)
print(result.render())  # Human-readable validation report
```

## संस्करण और स्थिरता

### v1.x की गारंटी

निम्नलिखित चीजें v1.x में **स्थिर हैं** (v2.0 में केवल महत्वपूर्ण बदलाव):

| अनुबंध | दायरा |
| ---------- | ------- |
| सत्यापन जांच आईडी | `LOAD_OK`, `PROTOCOL_FIELDS`, `MANIFEST_*`, आदि। |
| मैनिफेस्ट स्कीमा | `schema_version: 1` |
| एडाप्टर फैक्ट्री सिग्नेचर | `create_adapter(*, adapter_id=None, **config)` |
| क्षमता सेट | `dry_run`, `apply`, `timeout`, `external` (केवल अतिरिक्त) |
| घटना प्रकार | मुख्य घटना डेटा (केवल अतिरिक्त) |

### अवरुद्ध करने की नीति

- छोटे संस्करणों में चेतावनियों के साथ अप्रचलित घोषणाएं
- अगले प्रमुख संस्करण में हटा दिया गया
- रिलीज़ परिवर्तन लॉग में अपग्रेड नोट्स प्रदान किए गए

### एडाप्टर अनुकूलता

एडाप्टर अपने मैनिफेस्ट में समर्थित राउटर संस्करणों को घोषित करते हैं:

```python
ADAPTER_MANIFEST = {
    "supported_router_versions": ">=1.0,<2.0",
    ...
}
```

`validate_adapter()` टूल अनुकूलता की जांच करता है।

---

<p align="center">
  Built by <a href="https://mcp-tool-shop.github.io/">MCP Tool Shop</a>
</p>
