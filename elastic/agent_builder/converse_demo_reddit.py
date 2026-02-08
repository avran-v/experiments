#!/usr/bin/env python3
import json
import os
import sys
import urllib.request
import urllib.error
from datetime import datetime, timezone


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


def build_query(car_query, subreddit):
    # Use a stricter query to reduce noise and speed up processing.
    base = f'("{car_query}" AND (RAV4 OR "RAV4 Hybrid"))'
    if subreddit:
        return base, subreddit
    return base, None


def main():
    env_path = os.environ.get("ENV_PATH", ".env")
    load_env_file(env_path)

    kibana_url = os.environ.get("KIBANA_URL")
    api_key = os.environ.get("API_KEY")
    kibana_space = os.environ.get("KIBANA_SPACE", "")

    if not kibana_url or not api_key:
        print("Missing required env vars: KIBANA_URL and API_KEY", file=sys.stderr)
        sys.exit(1)

    car_query = os.environ.get("CAR_QUERY", "Toyota RAV4 Hybrid")
    subreddit = os.environ.get("SUBREDDIT", "Toyota") or None

    tool_posts = os.environ.get("TOOL_REDDIT_POSTS", "xpoz.getredditpostsbykeywords")
    tool_comments = os.environ.get("TOOL_REDDIT_COMMENTS", "xpoz.getredditcommentsbykeywords")
    tool_check = os.environ.get("TOOL_CHECK_OP", "xpoz.checkoperationstatus")

    space_prefix = f"/s/{kibana_space}" if kibana_space else ""
    base_url = f"{kibana_url}{space_prefix}/api/agent_builder/converse"

    output_dir = os.path.join(os.path.dirname(__file__), "output")
    os.makedirs(output_dir, exist_ok=True)

    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_path = os.path.join(output_dir, f"run_reddit_{run_id}.json")

    query, subreddit_filter = build_query(car_query, subreddit)

    prompt = (
        "You are the car sourcing agent. Gather Reddit sentiment for the vehicle below using MCP tools.\n"
        f"Vehicle: {car_query}\n\n"
        "Tools to use (call exactly):\n"
        f"- Posts tool: {tool_posts}\n"
        f"- Comments tool: {tool_comments}\n"
        f"- Operation status tool: {tool_check}\n\n"
        "CRITICAL tool flow rules:\n"
        "1) Call the posts tool with the query and (optional) subreddit filter.\n"
        "2) Immediately call the operation status tool with the returned operationId to get results.\n"
        "3) If status is \"running\", poll the operation status tool up to 20 times total.\n"
        "4) Repeat the same flow for the comments tool.\n"
        "5) If dataDumpExportOperationId is present, call the operation status tool with it to get the CSV link.\n"
        "6) Use only the returned results in your analysis.\n\n"
        "IMPORTANT:\n"
        "- Use the tool IDs exactly as written above (case-sensitive). Do not rename or change casing.\n"
        "- Preserve the query string exactly, including quotes.\n\n"
        "Input parameters to use:\n"
        f"- query: {query}\n"
    )

    if subreddit_filter:
        prompt += f"- subreddit: {subreddit_filter}\n"

    prompt += (
        "- time: year\n"
        "- fields: [\"id\", \"title\", \"selftext\", \"authorUsername\", \"subredditName\", "
        "\"score\", \"commentsCount\", \"createdAtDate\"]\n"
    )

    prompt += (
        "\nOutput format (JSON only):\n"
        "{\n"
        "  \"query\": string,\n"
        "  \"posts_summary\": {\n"
        "    \"count\": number,\n"
        "    \"top_themes\": [string],\n"
        "    \"notable_quotes\": [string]\n"
        "  },\n"
        "  \"comments_summary\": {\n"
        "    \"count\": number,\n"
        "    \"top_themes\": [string],\n"
        "    \"notable_quotes\": [string]\n"
        "  },\n"
        "  \"consensus\": {\n"
        "    \"sentiment\": \"positive|mixed|negative\",\n"
        "    \"summary\": string,\n"
        "    \"risks\": [string]\n"
        "  },\n"
        "  \"sources\": {\n"
        "    \"posts\": [string],\n"
        "    \"comments\": [string]\n"
        "  }\n"
        "}\n"
    )

    resp = converse(
        base_url,
        api_key,
        "car-sourcing-agent",
        input_text=prompt,
    )

    output_payload = {
        "run_id": run_id,
        "kibana_url": kibana_url,
        "car_query": car_query,
        "subreddit": subreddit_filter,
        "tool_posts": tool_posts,
        "tool_comments": tool_comments,
        "tool_check_operation": tool_check,
        "prompt": prompt,
        "response": resp,
    }

    with open(run_path, "w", encoding="utf-8") as f:
        json.dump(output_payload, f, indent=2)

    print(json.dumps(output_payload, indent=2))
    print(f"\nSaved run output to: {run_path}")


if __name__ == "__main__":
    main()
