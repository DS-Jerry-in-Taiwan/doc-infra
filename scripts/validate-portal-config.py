#!/usr/bin/env python3
"""
Portal Config Validator — Phase 3
Validates html/config.json against nginx location confs for consistency.

Usage:
    python3 scripts/validate-portal-config.py
    python3 scripts/validate-portal-config.py --config /path/to/config.json
    python3 scripts/validate-portal-config.py --locations-dir /path/to/nginx/conf.d/locations

Exit codes:
    0 = all validations passed
    1 = one or more failures
"""

import argparse
import json
import re
import sys
from pathlib import Path


VALID_CATEGORIES = {"document", "source"}
VALID_PUBLISH_STATES = {"published", "legacy"}
REQUIRED_FIELDS = {
    "name", "display_name", "category", "path",
    "static_root", "description", "publish_state"
}


def parse_nginx_alias(conf_text: str, location_path: str) -> str | None:
    """
    Extract the alias value from an nginx conf block for a given location path.
    Supports simple pattern: location <path> { alias <value>; }
    Returns None if not found.
    """
    # Normalize: remove comments, collapse whitespace
    lines = []
    for line in conf_text.splitlines():
        stripped = line.split('#')[0].strip()
        if stripped:
            lines.append(stripped)
    cleaned = ' '.join(lines)

    # Build regex for the specific location path.
    # The location path may contain regex characters, escape them.
    escaped_path = re.escape(location_path.rstrip('/'))
    pattern = rf'location\s+{escaped_path}/\s*\{{[^}}]*alias\s+([^;]+);'
    m = re.search(pattern, cleaned, re.DOTALL)
    if m:
        return m.group(1).strip()
    return None


def load_nginx_aliases(locations_dir: Path) -> dict[str, str]:
    """
    Load all location confs from locations_dir.
    Returns dict mapping normalized location path (e.g. "/code-review/")
    to alias value (e.g. "/doc-sites/code-reviewer/").
    """
    aliases = {}
    if not locations_dir.is_dir():
        return aliases

    for conf_file in sorted(locations_dir.iterdir()):
        if not conf_file.suffix == '.conf':
            continue
        text = conf_file.read_text(encoding='utf-8')

        # Find all "location /path/ {" blocks and extract alias
        # Pattern: location <path> { ... alias <value>; ... }
        location_pattern = re.compile(
            r'location\s+(/\S*?/)\s*\{',
            re.DOTALL
        )
        for loc_match in location_pattern.finditer(text):
            loc_path = loc_match.group(1)
            if not loc_path.endswith('/'):
                loc_path += '/'

            # Extract just the block after location header
            block_start = loc_match.end()
            brace_depth = 1
            block_end = block_start
            for i, ch in enumerate(text[block_start:], start=block_start):
                if ch == '{':
                    brace_depth += 1
                elif ch == '}':
                    brace_depth -= 1
                    if brace_depth == 0:
                        block_end = i
                        break
            block = text[block_start:block_end]

            # Find alias inside block
            alias_match = re.search(r'alias\s+([^;]+);', block)
            if alias_match:
                aliases[loc_path] = alias_match.group(1).strip()

    return aliases


def validate_config(config_path: Path, locations_dir: Path) -> list[str]:
    """
    Validate the portal config.
    Returns list of error messages (empty if all pass).
    """
    errors = []

    # 1. Parse JSON
    try:
        raw = config_path.read_text(encoding='utf-8')
        cfg = json.loads(raw)
    except json.JSONDecodeError as e:
        errors.append(f"JSON parse error: {e}")
        return errors

    # 2. Top-level checks
    if not isinstance(cfg.get('projects'), list):
        errors.append("top-level 'projects' must be a list")

    if 'last_updated' not in cfg:
        errors.append("top-level 'last_updated' is required")
    else:
        date_val = cfg['last_updated']
        if not re.match(r'^\d{4}-\d{2}-\d{2}$', date_val):
            errors.append(f"invalid last_updated format '{date_val}' (expected YYYY-MM-DD)")
        else:
            try:
                from datetime import datetime
                datetime.strptime(date_val, '%Y-%m-%d')
            except ValueError:
                errors.append(f"last_updated '{date_val}' is not a valid date")

    if cfg.get('mode') != 'static':
        errors.append(f"top-level 'mode' must be 'static', got '{cfg.get('mode')}'")

    projects = cfg.get('projects', [])

    # 3. Per-project checks
    names_seen = {}
    paths_seen = {}

    for idx, proj in enumerate(projects):
        if not isinstance(proj, dict):
            errors.append(f"projects[{idx}] is not an object")
            continue

        proj_name = proj.get('name', f'(unnamed at index {idx})')

        # Required fields
        for field in REQUIRED_FIELDS:
            if field not in proj or not proj[field]:
                errors.append(f"[{proj_name}] missing or empty required field '{field}'")

        # name uniqueness
        if proj.get('name'):
            if proj['name'] in names_seen:
                errors.append(f"[{proj_name}] duplicate name (first seen at {names_seen[proj['name']]})")
            else:
                names_seen[proj['name']] = proj_name

        # path uniqueness and format
        path_val = proj.get('path', '')
        if path_val:
            if path_val in paths_seen:
                errors.append(f"[{proj_name}] duplicate path '{path_val}' (first seen at {paths_seen[path_val]})")
            else:
                paths_seen[path_val] = proj_name

            if not (path_val.startswith('/') and path_val.endswith('/')):
                errors.append(f"[{proj_name}] path '{path_val}' must start and end with '/'")

        # category
        cat = proj.get('category', '')
        if cat and cat not in VALID_CATEGORIES:
            errors.append(f"[{proj_name}] category '{cat}' must be one of {sorted(VALID_CATEGORIES)}")

        # publish_state
        ps = proj.get('publish_state', '')
        if ps and ps not in VALID_PUBLISH_STATES:
            errors.append(f"[{proj_name}] publish_state '{ps}' must be one of {sorted(VALID_PUBLISH_STATES)}")

        # static_root vs publish_state prefix rule
        sr = proj.get('static_root', '')
        if sr and ps:
            if ps == 'published' and not sr.startswith('/doc-sites/'):
                errors.append(f"[{proj_name}] publish_state='published' but static_root '{sr}' does not start with '/doc-sites/'")
            elif ps == 'legacy' and not sr.startswith('/projects/'):
                errors.append(f"[{proj_name}] publish_state='legacy' but static_root '{sr}' does not start with '/projects/'")

    # 4. nginx alias consistency check
    if not errors:  # Only check nginx consistency if basic structure is valid
        nginx_aliases = load_nginx_aliases(locations_dir)

        for proj in projects:
            proj_name = proj.get('name', '')
            path_val = proj.get('path', '')
            static_root = proj.get('static_root', '')

            if not path_val or not static_root:
                continue  # Already reported above

            # Normalize path to match nginx location key
            nginx_path = path_val
            if not nginx_path.endswith('/'):
                nginx_path += '/'

            if nginx_path not in nginx_aliases:
                errors.append(f"[{proj_name}] no nginx location conf found for path '{path_val}'")
            else:
                nginx_alias = nginx_aliases[nginx_path]
                if nginx_alias != static_root:
                    errors.append(
                        f"[{proj_name}] static_root '{static_root}' does not match "
                        f"nginx alias '{nginx_alias}' for path '{path_val}'"
                    )

    return errors


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Validate portal metadata config against nginx location confs."
    )
    parser.add_argument(
        '--config',
        default='html/config.json',
        help='Path to portal config.json (default: html/config.json)'
    )
    parser.add_argument(
        '--locations-dir',
        default='nginx/conf.d/locations',
        help='Path to nginx locations directory (default: nginx/conf.d/locations)'
    )
    args = parser.parse_args()

    config_path = Path(args.config)
    locations_dir = Path(args.locations_dir)

    errors = validate_config(config_path, locations_dir)

    if errors:
        print("VALIDATION FAIL")
        for err in errors:
            print(f"  - {err}")
        sys.exit(1)
    else:
        # Count projects for summary
        try:
            cfg = json.loads(config_path.read_text(encoding='utf-8'))
            project_count = len(cfg.get('projects', []))
            print(f"VALIDATION PASS: {project_count} projects, all checks passed")
        except Exception:
            print("VALIDATION PASS")
        sys.exit(0)


if __name__ == '__main__':
    main()
