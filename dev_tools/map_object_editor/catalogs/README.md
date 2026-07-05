Map object palette catalogs live here.

Each `*.json` file contains a list of entries with this shape:

```json
{
  "label": "Enemy: Beetle",
  "object": {
    "type": "enemy_beetle",
    "name": "Beetle",
    "x": 0,
    "y": 0,
    "width": 1,
    "height": 1,
    "properties": {}
  }
}
```

The editor loads every JSON file from this directory and builds palette tabs from those entries.
