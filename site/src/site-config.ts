import type { SiteConfig } from '@mcptoolshop/site-theme';

export const config: SiteConfig = {
  title: 'nexus-router',
  description: 'Event-sourced MCP router with provenance + integrity. Every tool call is logged, every run is replayable, every result is verifiable.',
  logoBadge: 'NR',
  brandName: 'nexus-router',
  repoUrl: 'https://github.com/mcp-tool-shop-org/nexus-router',
  footerText: 'MIT Licensed — built by <a href="https://github.com/mcp-tool-shop-org" style="color:var(--color-muted);text-decoration:underline">mcp-tool-shop-org</a>',

  hero: {
    badge: 'Event-sourced',
    headline: 'Route tool calls,',
    headlineAccent: 'prove every result.',
    description: 'An event-sourced MCP router where every tool call is logged, every run is replayable, and every result ships with a SHA256 provenance bundle.',
    primaryCta: { href: '#usage', label: 'Get started' },
    secondaryCta: { href: '#features', label: 'Learn more' },
    previews: [
      { label: 'Install', code: 'pip install nexus-router' },
      { label: 'Run', code: 'resp = run({"goal": "demo", "mode": "dry_run",\n  "plan_override": []})' },
      { label: 'Replay', code: 'result = replay({"db_path": "nexus.db",\n  "run_id": "..."})\nprint(result["ok"])  # True' },
    ],
  },

  sections: [
    {
      kind: 'features',
      id: 'features',
      title: 'Features',
      subtitle: 'Platform-grade routing with built-in auditability.',
      features: [
        { title: 'Event log', desc: 'Monotonically sequenced event log — every tool call, policy decision, and result is recorded.' },
        { title: 'Provenance bundles', desc: 'Every run produces a SHA256-signed provenance bundle. Export, import, and verify across databases.' },
        { title: 'Adapter ecosystem', desc: 'Formal adapter contract with validation tools, CI templates, and auto-generated documentation.' },
      ],
    },
    {
      kind: 'code-cards',
      id: 'usage',
      title: 'Usage',
      cards: [
        {
          title: 'Basic run',
          code: 'from nexus_router.tool import run\n\nresp = run({\n  "goal": "demo",\n  "mode": "dry_run",\n  "plan_override": []\n})\n\nprint(resp["run"]["run_id"])\nprint(resp["summary"])',
        },
        {
          title: 'Export & replay',
          code: 'from nexus_router.tool import run, export, replay\n\n# Export a run as a portable bundle\nbundle = export({\n  "db_path": "source.db",\n  "run_id": run_id\n})["artifact"]\n\n# Replay and verify invariants\nresult = replay({\n  "db_path": "nexus.db",\n  "run_id": "..."\n})\nprint(result["ok"])  # True',
        },
      ],
    },
    {
      kind: 'data-table',
      id: 'adapters',
      title: 'Official Adapters',
      subtitle: 'Dispatch tool calls to any backend.',
      columns: ['Adapter', 'Description', 'Install'],
      rows: [
        ['adapter-http', 'HTTP/REST dispatch', 'pip install nexus-router-adapter-http'],
        ['adapter-stdout', 'Debug logging to stdout', 'pip install nexus-router-adapter-stdout'],
      ],
    },
    {
      kind: 'features',
      id: 'guarantees',
      title: 'v1.x Stability Guarantees',
      subtitle: 'Versioned contracts you can depend on.',
      features: [
        { title: 'Adapter contract', desc: 'Factory signatures, manifest schema, and capability sets are stable across v1.x — breaking changes only in v2.0.' },
        { title: 'Event types', desc: 'Core event payloads are additive-only. Your existing replay logic will never break within v1.x.' },
        { title: 'Validation IDs', desc: 'Check IDs like LOAD_OK, PROTOCOL_FIELDS, and MANIFEST_* are fixed — safe to match in CI gates.' },
      ],
    },
  ],
};
