# Elastic Family Agents POC

This folder contains Elasticsearch mappings, sample data, and conversation stubs for the family trip planning demo.

## Files
- `mappings/` index mappings for each core index
- `data/bulk_seed.ndjson` bulk dataset to load
- `data/example_documents.json` readable examples
- `queries/sample_queries.md` useful DSL snippets
- `conversation/` conversation stub and payload templates

## Load order (serverless)
1. Create indices with the provided mappings
2. Bulk load data
3. Run sample queries

## Example commands (replace placeholders)
```bash
# Create indices
curl -X PUT "$ES_ENDPOINT/family_profiles" -H "Authorization: ApiKey $ES_API_KEY" -H "Content-Type: application/json" -d @mappings/family_profiles.json
curl -X PUT "$ES_ENDPOINT/member_profiles" -H "Authorization: ApiKey $ES_API_KEY" -H "Content-Type: application/json" -d @mappings/member_profiles.json
curl -X PUT "$ES_ENDPOINT/member_preferences" -H "Authorization: ApiKey $ES_API_KEY" -H "Content-Type: application/json" -d @mappings/member_preferences.json
curl -X PUT "$ES_ENDPOINT/trip_plans" -H "Authorization: ApiKey $ES_API_KEY" -H "Content-Type: application/json" -d @mappings/trip_plans.json
curl -X PUT "$ES_ENDPOINT/trip_itineraries" -H "Authorization: ApiKey $ES_API_KEY" -H "Content-Type: application/json" -d @mappings/trip_itineraries.json
curl -X PUT "$ES_ENDPOINT/agent_memory" -H "Authorization: ApiKey $ES_API_KEY" -H "Content-Type: application/json" -d @mappings/agent_memory.json

# Bulk load dataset
curl -X POST "$ES_ENDPOINT/_bulk" -H "Authorization: ApiKey $ES_API_KEY" -H "Content-Type: application/x-ndjson" --data-binary @data/bulk_seed.ndjson
```
