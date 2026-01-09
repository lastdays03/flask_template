# API Version Migration Guide

## v1 to v2 Migration

### Breaking Changes

1. **Response Format**
   - V1: Simple data wrapper
   - V2: Enhanced with metadata and pagination object

2. **Error Codes**
   - V2 uses more specific error codes
   - Error messages are more detailed

3. **Date Format**
   - V1: ISO 8601 basic format
   - V2: ISO 8601 with timezone

### Migrating Your Code

#### Before (v1):
```python
response = requests.get('http://api/v1/users')
data = response.json()
users = data['users']
```

#### After (v2):
```python
response = requests.get('http://api/v2/users')
data = response.json()
users = data['data']  # Changed key name
pagination = data['pagination']  # New pagination object
```

### Deprecation Timeline

- v1.0: Stable, supported until 2026-12-31
- v2.0: Current stable version
