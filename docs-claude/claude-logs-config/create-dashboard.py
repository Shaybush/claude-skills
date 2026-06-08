#!/usr/bin/env python3
"""
Create the Claude Code - Cost & Usage Kibana dashboard.

Creates all required visualizations and a dashboard in one shot.
Run after Kibana is healthy:

    python3 create-dashboard.py

Requires: Python 3.7+, Kibana running on localhost:5601
"""
import json
import sys
import time
import urllib.request
import urllib.error

KIBANA = "http://localhost:5601"
INDEX_PATTERN_ID = "8af03307-7563-4391-95b7-c4c8e0ef495a"
INDEX_PATTERN_NAME = "claude-code-logs-*"
DASHBOARD_ID = "claude-code-cost-usage"


def kibana_api(method, path, body=None):
    """Send a request to the Kibana API."""
    url = f"{KIBANA}{path}"
    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request(
        url, data=data,
        headers={"kbn-xsrf": "true", "Content-Type": "application/json"},
        method=method,
    )
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())


def wait_for_kibana(timeout=120):
    """Wait until Kibana is available."""
    print(f"Waiting for Kibana at {KIBANA} ...")
    start = time.time()
    while time.time() - start < timeout:
        try:
            req = urllib.request.Request(f"{KIBANA}/api/status")
            with urllib.request.urlopen(req, timeout=5) as resp:
                data = json.loads(resp.read())
                if data.get("status", {}).get("overall", {}).get("level") == "available":
                    print("  Kibana is ready.")
                    return True
        except (urllib.error.URLError, OSError):
            pass
        time.sleep(3)
    print("  ERROR: Kibana did not become available within timeout.")
    sys.exit(1)


def ensure_index_pattern():
    """Create the index pattern / data view if it does not exist."""
    try:
        kibana_api("GET", f"/api/saved_objects/index-pattern/{INDEX_PATTERN_ID}")
        print(f"  Index pattern already exists: {INDEX_PATTERN_NAME}")
        return
    except urllib.error.HTTPError:
        pass

    kibana_api("POST", f"/api/saved_objects/index-pattern/{INDEX_PATTERN_ID}", {
        "attributes": {
            "title": INDEX_PATTERN_NAME,
            "timeFieldName": "@timestamp",
        }
    })
    print(f"  Created index pattern: {INDEX_PATTERN_NAME}")


def upsert_visualization(vis_id, title, description, vis_state, query=""):
    """Create or update a saved visualization."""
    search_source = json.dumps({
        "query": {"query": query, "language": "kuery"},
        "filter": [],
        "indexRefName": "kibanaSavedObjectMeta.searchSourceJSON.index",
    })
    body = {
        "attributes": {
            "title": title,
            "description": description,
            "uiStateJSON": "{}",
            "version": 1,
            "visState": json.dumps(vis_state),
            "kibanaSavedObjectMeta": {"searchSourceJSON": search_source},
        },
        "references": [{
            "id": INDEX_PATTERN_ID,
            "name": "kibanaSavedObjectMeta.searchSourceJSON.index",
            "type": "index-pattern",
        }],
    }
    result = kibana_api(
        "POST",
        f"/api/saved_objects/visualization/{vis_id}?overwrite=true",
        body,
    )
    status = "ok" if result.get("id") else "FAILED"
    print(f"  [{status}] {title}")
    return result


def create_visualizations():
    """Create all visualizations needed by this dashboard."""

    # [Claude] Total Cost — single big number
    upsert_visualization(
        "claude-total-cost",
        "[Claude] Total Cost",
        "Total cost across all API requests",
        {
            "title": "Total Cost",
            "type": "metric",
            "aggs": [{
                "id": "1", "enabled": True, "type": "sum",
                "params": {"field": "cost_usd", "customLabel": "Total Cost (USD)"},
                "schema": "metric",
            }],
            "params": {
                "addTooltip": True, "addLegend": False, "type": "metric",
                "metric": {
                    "percentageMode": False, "useRanges": False,
                    "colorSchema": "Green to Red", "metricColorMode": "None",
                    "colorsRange": [{"from": 0, "to": 10000}],
                    "labels": {"show": True}, "invertColors": False,
                    "style": {
                        "bgFill": "#000", "bgColor": False,
                        "labelColor": False, "subText": "", "fontSize": 60,
                    },
                },
            },
        },
        query="event.action: api_request",
    )

    # [Claude] Model Usage — donut pie
    upsert_visualization(
        "claude-model-usage",
        "[Claude] Model Usage",
        "API requests by model",
        {
            "title": "Model Usage",
            "type": "pie",
            "aggs": [
                {"id": "1", "enabled": True, "type": "count",
                 "params": {"customLabel": "Requests"}, "schema": "metric"},
                {"id": "2", "enabled": True, "type": "terms",
                 "params": {"field": "model", "orderBy": "1", "order": "desc", "size": 10},
                 "schema": "segment"},
            ],
            "params": {
                "type": "pie", "addTooltip": True, "addLegend": True,
                "legendPosition": "right", "isDonut": True,
                "labels": {"show": True, "values": True, "last_level": True, "truncate": 100},
            },
        },
        query="event.action: api_request",
    )

    # [Claude] Cost by Model — donut pie
    upsert_visualization(
        "claude-cost-by-model",
        "[Claude] Cost by Model",
        "Cost distribution across models",
        {
            "title": "Cost by Model",
            "type": "pie",
            "aggs": [
                {"id": "1", "enabled": True, "type": "sum",
                 "params": {"field": "cost_usd", "customLabel": "Cost USD"}, "schema": "metric"},
                {"id": "2", "enabled": True, "type": "terms",
                 "params": {"field": "model", "orderBy": "1", "order": "desc", "size": 10},
                 "schema": "segment"},
            ],
            "params": {
                "type": "pie", "addTooltip": True, "addLegend": True,
                "legendPosition": "right", "isDonut": True,
                "labels": {"show": True, "values": True, "last_level": True, "truncate": 100},
            },
        },
        query="event.action: api_request",
    )

    # [Claude] Tool Usage — donut pie
    upsert_visualization(
        "claude-tool-distribution",
        "[Claude] Tool Usage",
        "Tool call distribution",
        {
            "title": "Tool Usage",
            "type": "pie",
            "aggs": [
                {"id": "1", "enabled": True, "type": "count",
                 "params": {"customLabel": "Calls"}, "schema": "metric"},
                {"id": "2", "enabled": True, "type": "terms",
                 "params": {"field": "tool_name", "orderBy": "1", "order": "desc", "size": 15},
                 "schema": "segment"},
            ],
            "params": {
                "type": "pie", "addTooltip": True, "addLegend": True,
                "legendPosition": "right", "isDonut": True,
                "labels": {"show": True, "values": True, "last_level": True, "truncate": 100},
            },
        },
        query="event.action: tool_result",
    )

    # [Claude] Cost per Session — table
    upsert_visualization(
        "claude-cost-per-session",
        "[Claude] Cost per Session",
        "Per-session cost, tokens, and API call breakdown",
        {
            "title": "Cost per Session",
            "type": "table",
            "aggs": [
                {"id": "1", "enabled": True, "type": "sum",
                 "params": {"field": "cost_usd", "customLabel": "Cost USD"}, "schema": "metric"},
                {"id": "3", "enabled": True, "type": "count",
                 "params": {"customLabel": "API Calls"}, "schema": "metric"},
                {"id": "4", "enabled": True, "type": "sum",
                 "params": {"field": "input_tokens", "customLabel": "Input Tokens"}, "schema": "metric"},
                {"id": "5", "enabled": True, "type": "sum",
                 "params": {"field": "output_tokens", "customLabel": "Output Tokens"}, "schema": "metric"},
                {"id": "2", "enabled": True, "type": "terms",
                 "params": {"field": "session.id", "orderBy": "1", "order": "desc", "size": 20},
                 "schema": "bucket"},
            ],
            "params": {
                "perPage": 10, "showPartialRows": False,
                "showTotal": True, "totalFunc": "sum",
            },
        },
        query="event.action: api_request",
    )


def create_dashboard():
    """Create the Cost & Usage dashboard with 5 panels."""
    # Layout:
    #   Row 1: [Claude] Total Cost             (full-width metric banner)
    #   Row 2: Model Usage | Cost by Model | Tool Usage  (3 equal pie charts)
    #   Row 3: Cost per Session                (full-width table)
    panels = [
        {"type": "visualization", "panelIndex": "p1", "panelRefName": "panel_p1",
         "gridData": {"x": 0, "y": 0, "w": 48, "h": 8, "i": "p1"}},
        {"type": "visualization", "panelIndex": "p2", "panelRefName": "panel_p2",
         "gridData": {"x": 0, "y": 8, "w": 16, "h": 15, "i": "p2"}},
        {"type": "visualization", "panelIndex": "p3", "panelRefName": "panel_p3",
         "gridData": {"x": 16, "y": 8, "w": 16, "h": 15, "i": "p3"}},
        {"type": "visualization", "panelIndex": "p4", "panelRefName": "panel_p4",
         "gridData": {"x": 32, "y": 8, "w": 16, "h": 15, "i": "p4"}},
        {"type": "visualization", "panelIndex": "p5", "panelRefName": "panel_p5",
         "gridData": {"x": 0, "y": 23, "w": 48, "h": 15, "i": "p5"}},
    ]

    references = [
        {"id": "claude-total-cost",       "name": "panel_p1", "type": "visualization"},
        {"id": "claude-model-usage",      "name": "panel_p2", "type": "visualization"},
        {"id": "claude-cost-by-model",    "name": "panel_p3", "type": "visualization"},
        {"id": "claude-tool-distribution", "name": "panel_p4", "type": "visualization"},
        {"id": "claude-cost-per-session", "name": "panel_p5", "type": "visualization"},
    ]

    body = {
        "attributes": {
            "title": "Claude Code - Cost & Usage",
            "description": "Dashboard for cost, model usage, tool distribution, and per-session breakdown",
            "kibanaSavedObjectMeta": {
                "searchSourceJSON": json.dumps({
                    "query": {"query": "", "language": "kuery"}, "filter": [],
                }),
            },
            "panelsJSON": json.dumps(panels),
            "timeRestore": True,
            "timeTo": "now",
            "timeFrom": "now-24h",
            "refreshInterval": {"pause": False, "value": 30000},
        },
        "references": references,
    }

    result = kibana_api(
        "POST",
        f"/api/saved_objects/dashboard/{DASHBOARD_ID}?overwrite=true",
        body,
    )
    if result.get("id"):
        print(f"\nDashboard created: {result['id']}")
        print(f"  Open: {KIBANA}/app/dashboards#/view/{DASHBOARD_ID}")
    else:
        print(f"\nError: {json.dumps(result, indent=2)}")


def main():
    wait_for_kibana()

    print("\nSetting up index pattern...")
    ensure_index_pattern()

    print("\nCreating visualizations...")
    create_visualizations()

    print("\nCreating dashboard...")
    create_dashboard()

    print("\nDone! Your team can now open Kibana at:")
    print(f"  {KIBANA}/app/dashboards#/view/{DASHBOARD_ID}")


if __name__ == "__main__":
    main()
