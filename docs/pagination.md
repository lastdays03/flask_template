# API Pagination Guide

## Overview

All list endpoints support pagination using query parameters.

## Query Parameters

- `page`: Page number (default: 1)
- `per_page`: Items per page (default: 10, max: 100)

## Response Format

```json
{
  "data": [...],
  "meta": {
    "page": 1,
    "per_page": 10,
    "total": 100,
    "pages": 10,
    "has_next": true,
    "has_prev": false
  },
  "links": {
    "self": "http://api/users?page=1",
    "first": "http://api/users?page=1",
    "next": "http://api/users?page=2",
    "last": "http://api/users?page=10"
  }
}
```

## HTTP Headers

### Response Headers

- `Link`: RFC 5988 pagination links
- `X-Total-Count`: Total number of items
- `X-Page`: Current page number
- `X-Per-Page`: Items per page
- `X-Total-Pages`: Total number of pages

### Link Header Format

```
Link: <url>; rel="first", <url>; rel="prev", <url>; rel="next", <url>; rel="last"
```

## Example Usage

### cURL

```bash
curl -H "Authorization: Bearer token" \
     "http://api/users?page=2&per_page=20"
```

### Python

```python
import requests

response = requests.get(
    'http://api/users',
    params={'page': 2, 'per_page': 20},
    headers={'Authorization': 'Bearer token'}
)

data = response.json()
users = data['data']
meta = data['meta']
links = data['links']

# Get next page
if links['next']:
    next_response = requests.get(links['next'])
```
