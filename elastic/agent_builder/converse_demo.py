#!/usr/bin/env python3
import json
import os
import sys
import urllib.request
import urllib.error
from datetime import datetime


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
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8") if e.fp else ""
        raise RuntimeError(f"HTTP {e.code}: {body}") from e


def converse(base_url, api_key, agent_id, input_text, conversation_id=None):
    payload = {
        "agent_id": agent_id,
        "input": input_text,
    }
    if conversation_id:
        payload["conversation_id"] = conversation_id
    return request_json(base_url, api_key, payload)


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
    base_url = f"{kibana_url}{space_prefix}/api/agent_builder/converse"

    # Ensure output dir exists
    output_dir = os.path.join(os.path.dirname(__file__), "output")
    os.makedirs(output_dir, exist_ok=True)

    run_id = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    run_path = os.path.join(output_dir, f"run_{run_id}.json")

    # Step 1: Ask each member agent for preferences
    prompt = (
        "Please share your top 3 activity preferences and any hard constraints "
        "for a 5-day July trip."
    )

    member_agents = [
        "agent-parent",
        "agent-teen",
        "agent-child",
        "agent-grandparent",
    ]

    member_responses = []
    for agent_id in member_agents:
        resp = converse(
            base_url,
            api_key,
            agent_id,
            input_text=prompt,
        )
        member_responses.append({"agent_id": agent_id, "response": resp})
        print(f"\n=== {agent_id} response ===")
        print(json.dumps(resp, indent=2))

    # Step 2: Orchestrator composes a draft plan using the collected responses
    summary_lines = []
    for item in member_responses:
        summary_lines.append(f"{item['agent_id']}: {json.dumps(item['response'])}")

    orchestrator_prompt = (
        "You are the family orchestrator. Using the member responses below, "
        "draft a 5-day trip plan with a destination, constraints, and a 2-day itinerary stub.\n\n"
        + "\n".join(summary_lines)
    )

    orchestrator_resp = converse(
        base_url,
        api_key,
        "family-orchestrator",
        input_text=orchestrator_prompt,
    )

    print("\n=== family-orchestrator response ===")
    print(json.dumps(orchestrator_resp, indent=2))

    output_payload = {
        "run_id": run_id,
        "kibana_url": kibana_url,
        "agents": member_agents + ["family-orchestrator"],
        "member_prompt": prompt,
        "member_responses": member_responses,
        "orchestrator_prompt": orchestrator_prompt,
        "orchestrator_response": orchestrator_resp,
    }

    with open(run_path, "w", encoding="utf-8") as f:
        json.dump(output_payload, f, indent=2)

    print(f"\nSaved run output to: {run_path}")


if __name__ == "__main__":
    main()
