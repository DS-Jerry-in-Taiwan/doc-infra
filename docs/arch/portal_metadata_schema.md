# Portal Metadata Schema — Phase 3

## Overview

`html/config.json` serves as the **Portal Metadata Manifest** for doc-infra.
This document defines the schema contract for the config, so that the validator,
portal homepage renderer, and future publish pipeline share a common data contract.

> **Phase 3 Scope:** Standardize metadata, add validator, and mark legacy routes.
> Phase 3 does NOT migrate any routes, services, or project locations.

---

## Top-Level Config Contract

```json
{
  "projects": [ ... ],
  "last_updated": "YYYY-MM-DD",
  "mode": "static"
}
```

| Field | Type | Required | Description |
|---|---|---|---|
| `projects` | `Array<Project>` | Yes | List of project metadata entries |
| `last_updated` | `string` (YYYY-MM-DD) | Yes | ISO date of last config edit |
| `mode` | `string` | Yes | Must be `"static"` |

---

## Project Object

```json
{
  "name": "example-project",
  "display_name": "Example Project",
  "category": "document",
  "path": "/example/",
  "static_root": "/doc-sites/example-project/",
  "description": "Brief description shown on portal homepage",
  "publish_state": "published"
}
```

| Field | Type | Required | Rules |
|---|---|---|---|
| `name` | `string` | Yes | Unique, non-empty |
| `display_name` | `string` | Yes | Non-empty |
| `category` | `string` | Yes | One of: `document`, `source` |
| `path` | `string` | Yes | Unique, starts with `/`, ends with `/` |
| `static_root` | `string` | Yes | See prefix rule below |
| `description` | `string` | Yes | Non-empty |
| `publish_state` | `string` | Yes | One of: `published`, `legacy` |

---

## `publish_state` Enum

| Value | Meaning |
|---|---|
| `published` | Project artifact is in `/doc-sites/` and actively maintained |
| `legacy` | Project artifact is still served from `/projects/` source tree |

### `static_root` Prefix Rule

| `publish_state` | Required `static_root` prefix |
|---|---|
| `published` | `/doc-sites/` |
| `legacy` | `/projects/` |

Example:
- `publish_state: "published"` → `"static_root": "/doc-sites/code-reviewer/"`
- `publish_state: "legacy"` → `"static_root": "/projects/company-profile-optimizer/docs/public/"`

> **Note:** `legacy` does NOT mean "recommended." It is a Phase 3 status marker for
> projects that have not yet been migrated to `/doc-sites/`. Future phases will
> handle controlled migration.

---

## Phase 3 Project Manifest

| name | path | static_root | publish_state |
|---|---|---|---|
| `optimize-search-pipeline` | `/pipeline/` | `/doc-sites/optimize-search-pipeline/` | `published` |
| `bcas_quant` | `/bcas/` | `/doc-sites/bcas_quant/` | `published` |
| `OrganBriefOptimization` | `/organic/` | `/doc-sites/OrganBriefOptimization/` | `published` |
| `trade-data` | `/trade-data/` | `/doc-sites/trade-data/` | `published` |
| `company-profile-optimizer` | `/company-profile/` | `/projects/company-profile-optimizer/docs/public/` | `legacy` |
| `code-reviewer` | `/code-review/` | `/doc-sites/code-reviewer/` | `published` |
| `litellm` | `/litellm/` | `/doc-sites/litellm/` | `published` |

---

## nginx Alias Consistency Rule

Each project's `static_root` in `config.json` must match the `alias` directive
in the corresponding nginx location conf at `nginx/conf.d/locations/{name}.conf`.

Validator reads `nginx/conf.d/locations/*.conf` and checks:
```
location <project.path> {
    alias <project.static_root>;
    ...
}
```

Example matching pair:
```json
// config.json
"path": "/code-review/",
"static_root": "/doc-sites/code-reviewer/"
```
```nginx
# nginx/conf.d/locations/code-review.conf
location /code-review/ {
    alias /doc-sites/code-reviewer/;
    ...
}
```

### Redirect-only routes (not in config.json)

Routes such as `/litellm-mvp/` and `/litellm-aws/` exist in nginx conf but are
redirect-only or serve different source paths. They are **not** in the portal
metadata manifest and are out of Phase 3 scope.

---

## Validator Usage

```bash
# Default: check html/config.json against nginx/conf.d/locations/*.conf
python3 scripts/validate-portal-config.py

# Custom config path
python3 scripts/validate-portal-config.py --config /path/to/config.json

# Custom nginx locations directory
python3 scripts/validate-portal-config.py --locations-dir /path/to/nginx/conf.d/locations
```

### Exit Codes

| Code | Meaning |
|---|---|
| 0 | All validations passed |
| 1 | One or more validation failures |

### Output Format

- **PASS:** `VALIDATION PASS: <summary>`
- **FAIL:** `VALIDATION FAIL` followed by one line per error, each including the project name

---

## Adding or Modifying a Project

When adding a new project or modifying an existing one, follow this checklist:

1. [ ] Add/update nginx location conf at `nginx/conf.d/locations/{name}.conf`
2. [ ] Ensure `nginx -t` passes: `docker exec doc-infra-nginx nginx -t`
3. [ ] Add/update project entry in `html/config.json` with all required fields
4. [ ] Set `publish_state`:
   - Artifact in `/doc-sites/` → `"published"`
   - Artifact still in `/projects/` source tree → `"legacy"`
5. [ ] Run validator: `python3 scripts/validate-portal-config.py`
6. [ ] Reload nginx: `docker exec doc-infra-nginx nginx -s reload`
7. [ ] Verify route: `curl -s -o /dev/null -w "%{http_code}" http://localhost:8081/{path}`

---

## Schema Limitations

- The validator uses simple regex/text scanning to parse nginx confs.
  It supports the common pattern:
  ```
  location /path/ {
      alias /some/path/;
  }
  ```
  Complex nginx configurations (nested locations, maps, regex locations) may not
  be handled correctly.
- Only the portal homepage renderer (`html/script.js`) uses the config;
  additional fields are ignored by the renderer but accepted by the validator
  for forward compatibility.

---

## Phase 3 Boundaries (What Phase 3 Does NOT Do)

| Out of Scope | Reason |
|---|---|
| Migrating `company-profile` to `/doc-sites/` | Phase 4/5 territory |
| Migrating `litellm-mvp` | Redirect-only; separate tracking |
| Modifying `scripts/publish-local-artifact.sh` | Phase 2 pilot script; not multi-project |
| Adding SFTPGo, builder, validator service, Pagefind | Not needed for Phase 3 |
| Modifying Docker ports/services | No infrastructure change |
| Re-enabling `/files/` | Security violation |
| Adding public `/projects/` route | Security violation |
| Modifying `html/script.js` or `html/style.css` | Backwards compatible as-is |
