#!/usr/bin/env python3
import json
import os
import sys
import urllib.request
import urllib.error


def load_env_file(path):
    if not os.path.exists(path):
        return
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith("export "):
                line = line[len("export "):]
            if "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip("\"").strip("'")
            os.environ.setdefault(key, value)


def request_json(url, api_key, payload):
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={
            "Authorization": f"ApiKey {api_key}",
            "kbn-xsrf": "true",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req) as resp:
            return resp.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8") if e.fp else ""
        raise RuntimeError(f"HTTP {e.code}: {body}") from e


def main():
    env_path = os.environ.get("ENV_PATH", ".env")
    load_env_file(env_path)

    kibana_url = os.environ.get("KIBANA_URL")
    api_key = os.environ.get("API_KEY")
    kibana_space = os.environ.get("KIBANA_SPACE", "")

    if not kibana_url or not api_key:
        print("Missing required env vars: KIBANA_URL and API_KEY", file=sys.stderr)
        sys.exit(1)

    space_prefix = f"/s/{kibana_space}" if kibana_space else ""
    base_url = f"{kibana_url}{space_prefix}/api/agent_builder/agents"

    agents = [
        {
            "id": "family-orchestrator",
            "name": "Family Orchestrator",
            "description": "Coordinates family trip planning and resolves preferences.",
            "labels": ["family", "planning", "orchestration"],
            "avatar_color": "#BFDBFF",
            "avatar_symbol": "FO",
            "configuration": {
                "instructions": "You orchestrate trip planning. Read member preferences, reconcile conflicts, and draft a plan + itinerary.",
                "tools": [
                    {"tool_ids": [
                        "platform.core.search",
                        "platform.core.list_indices",
                        "platform.core.get_index_mapping",
                        "platform.core.get_document_by_id",
                    ]}
                ],
            },
        },
        {
            "id": "agent-parent",
            "name": "Parent Agent",
            "description": "Represents the parent family member.",
            "labels": ["family", "member", "parent"],
            "avatar_color": "#C7F9CC",
            "avatar_symbol": "PA",
            "configuration": {
                "instructions": "You represent the parent. Provide balanced preferences: budget-conscious, mix of activity and rest.",
                "tools": [
                    {"tool_ids": [
                        "platform.core.search",
                        "platform.core.get_document_by_id",
                    ]}
                ],
            },
        },
        {
            "id": "agent-teen",
            "name": "Teen Agent",
            "description": "Represents the teen family member.",
            "labels": ["family", "member", "teen"],
            "avatar_color": "#FDE68A",
            "avatar_symbol": "TE",
            "configuration": {
                "instructions": "You represent the teen. Provide preferences like nightlife, adventure, late starts. Avoid early mornings.",
                "tools": [
                    {"tool_ids": [
                        "platform.core.search",
                        "platform.core.get_document_by_id",
                    ]}
                ],
            },
        },
        {
            "id": "agent-child",
            "name": "Child Agent",
            "description": "Represents the child family member.",
            "labels": ["family", "member", "child"],
            "avatar_color": "#FCA5A5",
            "avatar_symbol": "CH",
            "configuration": {
                "instructions": "You represent the child. Prefer animals and water activities; keep things simple.",
                "tools": [
                    {"tool_ids": [
                        "platform.core.search",
                        "platform.core.get_document_by_id",
                    ]}
                ],
            },
        },
        {
            "id": "agent-grandparent",
            "name": "Grandparent Agent",
            "description": "Represents the grandparent family member.",
            "labels": ["family", "member", "grandparent"],
            "avatar_color": "#E9D5FF",
            "avatar_symbol": "GP",
            "configuration": {
                "instructions": "You represent the grandparent. Prefer accessible walking and quiet evenings.",
                "tools": [
                    {"tool_ids": [
                        "platform.core.search",
                        "platform.core.get_document_by_id",
                    ]}
                ],
            },
        },
    ]

    for payload in agents:
        response = request_json(base_url, api_key, payload)
        print(response)

    print("Done. Created agents (or received errors if they already exist).")


if __name__ == "__main__":
    main()
