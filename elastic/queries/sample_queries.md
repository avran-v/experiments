**Sample Queries (Elasticsearch DSL)**

1. Get all preferences for a family
```json
GET member_preferences/_search
{
  "query": {
    "term": { "family_id": "fam_001" }
  },
  "sort": [
    { "priority": "desc" },
    { "last_updated": "desc" }
  ]
}
```

2. Aggregate top activity preferences for the family
```json
GET member_preferences/_search
{
  "size": 0,
  "query": {
    "bool": {
      "filter": [
        { "term": { "family_id": "fam_001" } },
        { "term": { "preference_type": "activities" } }
      ]
    }
  },
  "aggs": {
    "top_activity_values": {
      "terms": { "field": "value", "size": 10 }
    }
  }
}
```

3. Find current draft trip plan for a family
```json
GET trip_plans/_search
{
  "query": {
    "bool": {
      "filter": [
        { "term": { "family_id": "fam_001" } },
        { "term": { "status": "draft" } }
      ]
    }
  }
}
```

4. Find itineraries with accessible-friendly activities
```json
GET trip_itineraries/_search
{
  "query": {
    "nested": {
      "path": "activities",
      "query": {
        "match": { "activities.notes": "accessible" }
      }
    }
  }
}
```

5. Pull agent memory for recent decisions
```json
GET agent_memory/_search
{
  "query": {
    "bool": {
      "filter": [
        { "term": { "family_id": "fam_001" } },
        { "term": { "memory_type": "decision" } }
      ]
    }
  },
  "sort": [
    { "created_at": "desc" }
  ]
}
```

6. Show destination candidates for a trip
```json
GET trip_plans/_search
{
  "query": { "term": { "trip_id": "trip_2026_07_sd" } },
  "_source": ["destination_candidates", "final_destination", "budget_estimate"]
}
```
