# Claude Code Logs — Kibana Dashboard Setup

Monitor Claude Code usage, costs, and tool activity through Elasticsearch and Kibana.

---

## What You Get

A pre-built **"Claude Code - Cost & Usage"** dashboard with 5 panels:

| Panel | Type | Description |
|-------|------|-------------|
| **Total Cost** | Metric | Single big-number showing total USD spent |
| **Model Usage** | Donut pie | API request count by model |
| **Cost by Model** | Donut pie | USD cost distribution by model |
| **Tool Usage** | Donut pie | Tool call distribution |
| **Cost per Session** | Table | Per-session breakdown of cost, API calls, and tokens |

---

## Prerequisites

- Docker Desktop (or Docker Engine + Docker Compose v2)
- Python 3.7+
- Ports free: **4317**, **4318**, **5601**, **9200**

---

## Quick Start

### 1. Start the stack

```bash
cd claude-logs-config
docker compose up -d
```

Wait ~60s for Elasticsearch to initialize. Check status:

```bash
docker compose ps
```

All 3 services should show `healthy`:
- `elasticsearch` — log storage
- `kibana` — dashboard UI
- `otel-collector` — receives telemetry from Claude Code

### 2. Configure Claude Code

Add to your `~/.claude/settings.json` (merge the `env` block into your existing settings):

```json
{
  "env": {
    "OTEL_LOGS_EXPORTER": "otlp",
    "OTEL_EXPORTER_OTLP_PROTOCOL": "grpc",
    "OTEL_EXPORTER_OTLP_ENDPOINT": "http://localhost:4317",
    "OTEL_SERVICE_NAME": "claude-code"
  }
}
```

Also add to `~/.claude/.env`:

```dotenv
OTEL_LOGS_EXPORTER=otlp
OTEL_EXPORTER_OTLP_PROTOCOL=grpc
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317
OTEL_SERVICE_NAME=claude-code
```

> **Tip:** If you hit gRPC errors, switch to HTTP:
> `OTEL_EXPORTER_OTLP_PROTOCOL=http/protobuf` and
> `OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4318`

### 3. Restart Claude Code

Close and reopen all Claude Code sessions so the new environment variables take effect.

### 4. Create the dashboard

After Kibana is healthy (the script waits automatically):

```bash
python3 create-dashboard.py
```

Output:

```
Waiting for Kibana at http://localhost:5601 ...
  Kibana is ready.

Setting up index pattern...
  Created index pattern: claude-code-logs-*

Creating visualizations...
  [ok] [Claude] Total Cost
  [ok] [Claude] Model Usage
  [ok] [Claude] Cost by Model
  [ok] [Claude] Tool Usage
  [ok] [Claude] Cost per Session

Creating dashboard...

Dashboard created: claude-code-cost-usage
  Open: http://localhost:5601/app/dashboards#/view/claude-code-cost-usage
```

### 5. Open the dashboard

Go to **http://localhost:5601/app/dashboards#/view/claude-code-cost-usage**

---

## Verify Data Flow

### Check OTel Collector is receiving data

```bash
docker compose logs otel-collector --tail=20
```

Look for lines like `Exporting items ...`

### Check Elasticsearch has logs

```bash
curl -s 'http://localhost:9200/claude-code-logs/_count' | python3 -m json.tool
```

### Browse raw logs in Discover

1. Open **http://localhost:5601**
2. Go to **Discover** (hamburger menu > Analytics > Discover)
3. Select the `claude-code-logs-*` data view
4. Set the time range to **Last 24 hours**

---

## Useful KQL Queries

Use these in the Kibana search bar or Discover:

| Goal | KQL Query |
|------|-----------|
| All API requests | `event.action: api_request` |
| Specific model | `event.action: api_request AND model: "claude-opus-4-6"` |
| Tool calls only | `event.action: tool_result` |
| Specific tool | `event.action: tool_result AND tool_name: "Bash"` |
| Failed tools | `event.action: tool_result AND success: false` |
| Errors | `severityText: "ERROR"` |
| Specific session | `session.id: "YOUR_SESSION_ID"` |
| High cost requests | `event.action: api_request AND cost_usd > 0.05` |

---

## Ports Reference

| Service | Port | URL |
|---------|------|-----|
| OTel Collector gRPC | 4317 | (receives from Claude Code) |
| OTel Collector HTTP | 4318 | (receives from Claude Code) |
| Elasticsearch | 9200 | http://localhost:9200 |
| Kibana | 5601 | http://localhost:5601 |

---

## Stopping the Stack

Stop but keep data:

```bash
docker compose down
```

Full reset (delete all data):

```bash
docker compose down -v
```

---

## Troubleshooting

### No data in Kibana

1. Verify collector is running: `docker compose logs otel-collector`
2. Check the index exists: `curl http://localhost:9200/_cat/indices?v`
3. Make sure Claude Code has the OTEL env vars set and was restarted

### Elasticsearch takes too long to start

Increase Docker Desktop memory to at least **4 GB** (Docker Desktop > Settings > Resources).

### Re-run the dashboard script

The script is idempotent — safe to re-run anytime:

```bash
python3 create-dashboard.py
```

---

## Architecture

```
Claude Code
    │
    ▼ OTLP gRPC :4317
┌───────────────────┐
│  OTel Collector    │
│  (batch + export)  │
└────────┬──────────┘
         │
         ▼
   Elasticsearch :9200
    (log storage)
         │
         ▼
     Kibana :5601
    (dashboards)
```
