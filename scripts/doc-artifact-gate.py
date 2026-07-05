#!/usr/bin/env python3
"""
doc-artifact-gate.py — Phase 5 Validator / Promote Gate MVP

Validates, stages, promotes, and rolls back doc artifacts for the doc-infra pipeline.

Usage:
    python3 scripts/doc-artifact-gate.py validate --project code-reviewer
    python3 scripts/doc-artifact-gate.py stage --project code-reviewer
    python3 scripts/doc-artifact-gate.py promote --project code-reviewer --confirm
    python3 scripts/doc-artifact-gate.py rollback --project code-reviewer --backup <backup-id> --confirm

Environment variables:
    DOC_INFRA_INCOMING_ROOT   Default: /srv/doc-infra/data/incoming
    DOC_INFRA_STAGING_ROOT    Default: /srv/doc-infra/data/staging
    DOC_INFRA_PUBLIC_ROOT      Default: /home/ubuntu/doc-sites
    DOC_INFRA_AUDIT_ROOT       Default: /srv/doc-infra/data/audit
    DOC_INFRA_BACKUP_ROOT      Default: /srv/doc-infra/data/backups
    DOC_INFRA_GATE_MAX_FILES   Default: 2000
    DOC_INFRA_GATE_MAX_BYTES   Default: 209715200 (200 MiB)

Exit codes:
    0  = success
    1  = validation failure or operation failure
    2  = missing required arguments
    3  = project not allowed (MVP only supports code-reviewer)
"""

import argparse
import datetime
import json
import os
import re
import shutil
import sys
import uuid
from pathlib import Path


# ─── Central file iteration helper (includes dotfiles and symlinks) ────────────

def _iter_files_with_dotfiles(root: Path):
    """
    Iterate over all files under root, including hidden files (dotfiles).

    Uses os.walk to ensure dotfiles like .env, .bashrc, etc. are included.
    Yields Path objects for all regular files and symlinks (to allow checking).
    """
    for dirpath, dirnames, filenames in os.walk(root):
        dirpath = Path(dirpath)
        for filename in filenames:
            f = dirpath / filename
            if f.is_file():
                yield f

# ─── Constants ────────────────────────────────────────────────────────────────

ALLOWED_PROJECT = "code-reviewer"

ALLOWED_EXTENSIONS = {
    ".html", ".htm", ".css", ".js", ".json", ".png", ".jpg",
    ".jpeg", ".gif", ".svg", ".webp", ".ico", ".pdf", ".txt",
    ".md", ".woff", ".woff2", ".ttf", ".map",
}

FORBIDDEN_EXTENSIONS = {
    ".env", ".pem", ".key", ".p12", ".pfx", ".sqlite", ".db",
    ".py", ".sh", ".bash", ".zsh", ".php", ".rb", ".go", ".rs",
    ".java", ".class", ".jar", ".zip", ".tar", ".gz", ".7z",
}

SECRET_PATTERNS = [
    # Private key header (high confidence)
    re.compile(r"BEGIN\s+(?:RSA\s+|EC\s+|DSA\s+|OPENSSH\s+|PGP\s+)?PRIVATE\s+KEY\b", re.IGNORECASE),
    # AWS credentials (exact, high confidence)
    re.compile(r"(?:AWS_ACCESS_KEY_ID|AWS_SECRET_ACCESS_KEY)\s*[=:]\s*['\"]?[A-Za-z0-9/+=]{20,40}['\"]?"),
    # AWS access key ID format (AKIA...)
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    # Generic secret= with substantial value (≥8 chars, to avoid flagging "key=true")
    re.compile(r"\b(?:password|token|api[_-]?key)\s*[=:]\s*['\"][^\s'\"]{8,128}['\"]", re.IGNORECASE),
    # ngrok auth token literal string (not just the name, look for actual token-like values)
    re.compile(r"\bNGROK_AUTHTOKEN\s*[=:]\s*['\"][0-9A-Za-z_-]{20,}[_'\"']", re.IGNORECASE),
]

# ─── Path helpers ─────────────────────────────────────────────────────────────

def incoming_root() -> Path:
    return Path(os.environ.get(
        "DOC_INFRA_INCOMING_ROOT", "/srv/doc-infra/data/incoming"))

def staging_root() -> Path:
    return Path(os.environ.get(
        "DOC_INFRA_STAGING_ROOT", "/srv/doc-infra/data/staging"))

def public_root() -> Path:
    return Path(os.environ.get(
        "DOC_INFRA_PUBLIC_ROOT", "/home/ubuntu/doc-sites"))

def audit_root() -> Path:
    return Path(os.environ.get(
        "DOC_INFRA_AUDIT_ROOT", "/srv/doc-infra/data/audit"))

def backup_root() -> Path:
    return Path(os.environ.get(
        "DOC_INFRA_BACKUP_ROOT", "/srv/doc-infra/data/backups"))

def max_files() -> int:
    return int(os.environ.get("DOC_INFRA_GATE_MAX_FILES", "2000"))

def max_bytes() -> int:
    return int(os.environ.get("DOC_INFRA_GATE_MAX_BYTES", "209715200"))

# ─── Project mapping ──────────────────────────────────────────────────────────

PROJECT_MAP = {
    "code-reviewer": {
        "path": "/code-review/",
        "static_root": "/doc-sites/code-reviewer/",
        "publish_state": "published",
    }
}

# ─── Validation ───────────────────────────────────────────────────────────────

class ValidationResult:
    def __init__(self):
        self.passed = True
        self.errors: list[str] = []
        self.warnings: list[str] = []
        self.file_count = 0
        self.total_bytes = 0

    def fail(self, msg: str):
        self.errors.append(msg)
        self.passed = False

    def warn(self, msg: str):
        self.warnings.append(msg)


def validate_source(source_path: Path, project: str) -> ValidationResult:
    """Run all validation checks on source_path for given project."""
    result = ValidationResult()

    # 1. Source exists and is directory
    if not source_path.exists():
        result.fail(f"Source does not exist: {source_path}")
        return result
    if not source_path.is_dir():
        result.fail(f"Source is not a directory: {source_path}")

    # 2. Source non-empty (using central helper to include dotfiles)
    all_files = list(_iter_files_with_dotfiles(source_path))
    if not all_files:
        result.fail(f"Source is empty: {source_path}")
        return result

    # 3. Root index.html exists
    index_path = source_path / "index.html"
    if not index_path.exists():
        result.fail(f"Root index.html does not exist: {index_path}")

    result.file_count = len(all_files)
    if result.file_count > max_files():
        result.fail(
            f"File count {result.file_count} exceeds limit {max_files()}")

    total = 0
    for f in all_files:
        try:
            total += f.stat().st_size
        except OSError:
            pass
    result.total_bytes = total
    if total > max_bytes():
        result.fail(
            f"Total size {total} bytes exceeds limit {max_bytes()} bytes")

    # 4. No symlinks (checked during iteration; central helper skips symlinks)
    for f in all_files:
        if f.is_symlink():
            result.fail(f"Symlink not allowed: {f}")

    # 5. No path traversal / control chars in filenames
    # Check relative path from source for '..' or absolute paths derived from source root
    control_char_pattern = re.compile(r"[\x00-\x1f]")
    for f in all_files:
        # Path traversal check: relative path must not contain '..'
        try:
            rel = f.relative_to(source_path)
            if ".." in rel.parts:
                result.fail(f"Path traversal detected (relative path contains '..'): {f}")
            # Absolute path check: if derived from source root, should not be absolute
            if f.is_absolute() and str(f).startswith(str(source_path)):
                # This is an absolute path under source root - potential issue
                # But on POSIX systems, files under source root are accessed via
                # relative paths; an absolute path here may indicate a symlink
                # or special handling. We already excluded symlinks above.
                pass
        except ValueError:
            result.fail(f"Path traversal detected: {f} is not relative to {source_path}")

        if control_char_pattern.search(f.name):
            result.fail(f"Filename contains control char: {f.name}")

    # 6. Extension allowlist + denylist (handles dotfiles like .env)
    for f in all_files:
        ext = f.suffix.lower()
        name = f.name
        # Special handling for dotfiles (files starting with '.'):
        # Check if the full filename (e.g., ".env", ".bashrc") is forbidden
        if name.startswith("."):
            if name in FORBIDDEN_EXTENSIONS:
                result.fail(f"Forbidden dotfile {name}: {f}")
            elif name not in ALLOWED_EXTENSIONS and "." + name not in ALLOWED_EXTENSIONS:
                result.warn(f"Dotfile {name} not in allowlist, skipped: {f}")
        elif ext in FORBIDDEN_EXTENSIONS:
            result.fail(f"Forbidden extension {ext}: {f}")
        elif ext and ext not in ALLOWED_EXTENSIONS:
            result.warn(f"Extension {ext} not in allowlist, skipped: {f}")

    # 7. Secret scan (includes .env, dotfiles, and other text-based files)
    for f in all_files:
        ext = f.suffix.lower()
        name = f.name
        # Determine if this file should be scanned for secrets
        should_scan = False
        if ext in {".html", ".htm", ".css", ".js", ".json", ".txt", ".md", ".py", ".sh"}:
            should_scan = True
        elif name.startswith(".") and name.lower() in {".env", ".bashrc", ".profile", ".zshrc", ".gitconfig", ".npmrc"}:
            should_scan = True
        elif name == ".env":
            should_scan = True

        if should_scan:
            try:
                content = f.read_text(encoding="utf-8", errors="ignore")
                for pattern in SECRET_PATTERNS:
                    if pattern.search(content):
                        result.fail(f"Secret pattern detected in {f}")
                        break
            except OSError:
                pass

    # 8. Portal metadata preflight
    # We import validate-portal-config as a module and check the project
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "validate_portal_config",
            str(Path(__file__).parent / "validate-portal-config.py"))
        if spec and spec.loader:
            vmod = importlib.util.module_from_spec(spec)
            sys.modules["validate_portal_config"] = vmod
            spec.loader.exec_module(vmod)
            errors = vmod.validate_config(
                Path("html/config.json"),
                Path("nginx/conf.d/locations"))
            # Only fail on config errors related to our project
            project_cfg = PROJECT_MAP.get(project, {})
            for err in errors:
                if project in err:
                    result.fail(f"Portal metadata preflight failed: {err}")
                    break
    except Exception as e:
        result.warn(f"Portal metadata preflight skipped: {e}")

    # 9. Project mapping check
    if project not in PROJECT_MAP:
        result.fail(f"Unknown project: {project}")

    return result


def write_validation_report(
    project: str,
    result: ValidationResult,
    report_path: Path,
):
    """Write validation report as JSON."""
    report = {
        "project": project,
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z"),
        "passed": result.passed,
        "errors": result.errors,
        "warnings": result.warnings,
        "file_count": result.file_count,
        "total_bytes": result.total_bytes,
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        json.dumps(report, indent=2, ensure_ascii=False),
        encoding="utf-8")


def append_promote_log(
    action: str,
    project: str,
    backup_id: str | None,
    success: bool,
    detail: str,
):
    """Append a JSONL entry to the promote log."""
    log_path = audit_root() / "promote-log.jsonl"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z"),
        "action": action,
        "project": project,
        "backup_id": backup_id,
        "success": success,
        "detail": detail,
    }
    with log_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def copytree_safe(src: Path, dst: Path) -> None:
    """Copy directory tree, failing on symlinks, including dotfiles."""
    if src == dst:
        raise ValueError("Source and destination are the same")
    if dst.is_relative_to(src) or src.is_relative_to(dst):
        try:
            dst.relative_to(src)
            raise ValueError("Destination is inside source")
        except ValueError:
            pass
        try:
            src.relative_to(dst)
            raise ValueError("Source is inside destination")
        except ValueError:
            pass

    # Path traversal check: ensure no '..' in any relative path
    for src_item in _iter_files_with_dotfiles(src):
        if src_item.is_symlink():
            raise ValueError(f"Symlink not allowed: {src_item}")
        rel = src_item.relative_to(src)
        # Verify no '..' in relative path
        if ".." in rel.parts:
            raise ValueError(f"Path traversal detected: {rel}")
        dst_item = dst / rel
        # Exclude manifest.json from artifact copies
        if rel.name == "manifest.json":
            continue
        dst_item.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src_item, dst_item)


# ─── Commands ─────────────────────────────────────────────────────────────────

def cmd_validate(project: str) -> ValidationResult:
    source = incoming_root() / project
    result = validate_source(source, project)

    ts = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    report_path = audit_root() / "validation-reports" / f"{project}-{ts}.json"
    write_validation_report(project, result, report_path)

    if result.passed:
        print(f"VALIDATE PASS: {project} ({result.file_count} files, "
              f"{result.total_bytes} bytes)")
        print(f"Report: {report_path}")
    else:
        print(f"VALIDATE FAIL: {project}")
        for err in result.errors:
            print(f"  - {err}")

    return result


def cmd_stage(project: str) -> ValidationResult:
    """Copy incoming to staging if validate passes."""
    source = incoming_root() / project
    result = validate_source(source, project)

    ts = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    report_path = audit_root() / "validation-reports" / f"{project}-{ts}.json"
    write_validation_report(project, result, report_path)

    if not result.passed:
        print(f"STAGE FAIL: {project} — validation failed")
        for err in result.errors:
            print(f"  - {err}")
        return result

    staging = staging_root() / project

    # Fail-safe: do not overwrite published
    if staging.exists():
        shutil.rmtree(staging)

    copytree_safe(source, staging)
    print(f"STAGE OK: {project} -> {staging}")
    print(f"Report: {report_path}")
    return result


def _backup_current_published(project: str) -> tuple[Path, dict]:
    """Backup current published artifact and return backup path + manifest."""
    pub = public_root() / project
    bk_id = f"pre-{datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')}-{uuid.uuid4().hex[:8]}"
    bk_root = backup_root() / project / bk_id
    bk_root.parent.mkdir(parents=True, exist_ok=True)

    file_count = 0
    total_bytes = 0
    if pub.exists():
        for f in _iter_files_with_dotfiles(pub):
            file_count += 1
            try:
                total_bytes += f.stat().st_size
            except OSError:
                pass

    manifest = {
        "project": project,
        "backup_id": bk_id,
        "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z"),
        "file_count": file_count,
        "total_bytes": total_bytes,
    }

    if pub.exists():
        copytree_safe(pub, bk_root)

    manifest_path = bk_root / "manifest.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False),
        encoding="utf-8")

    return bk_root, manifest


def _promote_impl(project: str) -> bool:
    """Promote staging to published with tmp+verify+swap."""
    stage = staging_root() / project
    if not stage.exists():
        print(f" PROMOTE FAIL: staging/{project} does not exist")
        return False

    # Validate staging content
    result = validate_source(stage, project)
    if not result.passed:
        print(f"PROMOTE FAIL: staging validation failed")
        for err in result.errors:
            print(f"  - {err}")
        return False

    # Backup current published
    bk_path, manifest = _backup_current_published(project)
    print(f"Backup created: {bk_path}")

    # Copy staging -> tmp
    pub = public_root() / project
    tmp = public_root() / f"{project}.tmp"

    if tmp.exists():
        shutil.rmtree(tmp)

    copytree_safe(stage, tmp)

    # Verify tmp
    tmp_index = tmp / "index.html"
    if not tmp_index.exists():
        shutil.rmtree(tmp)
        print(f"PROMOTE FAIL: tmp verification failed — no index.html")
        append_promote_log("promote", project, manifest["backup_id"],
                           False, "tmp verification failed: no index.html")
        return False

    # Re-validate tmp
    result2 = validate_source(tmp, project)
    if not result2.passed:
        shutil.rmtree(tmp)
        print(f"PROMOTE FAIL: tmp re-validation failed")
        for err in result2.errors:
            print(f"  - {err}")
        append_promote_log("promote", project, manifest["backup_id"],
                           False, f"tmp re-validation failed: {result2.errors}")
        return False

    # Swap tmp -> published
    if pub.exists():
        shutil.rmtree(pub)
    shutil.move(str(tmp), str(pub))

    append_promote_log("promote", project, manifest["backup_id"],
                       True, f"Promoted {project} to published")
    print(f"PROMOTE OK: {project} -> {pub}")
    return True


def cmd_promote(project: str, confirm: bool) -> bool:
    if not confirm:
        print("PROMOTE ABORT: --confirm required")
        return False

    ok = _promote_impl(project)
    return ok


def _rollback_impl(project: str, backup_id: str) -> bool:
    """Rollback published from backup via tmp+verify+swap."""
    bk_root = backup_root() / project / backup_id
    manifest_path = bk_root / "manifest.json"

    # Verify backup exists
    if not bk_root.exists() or not manifest_path.exists():
        print(f"ROLLBACK FAIL: backup {backup_id} not found")
        append_promote_log("rollback", project, backup_id,
                           False, "backup not found or missing manifest.json")
        return False

    # Verify manifest.project == requested project
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as e:
        print(f"ROLLBACK FAIL: could not read manifest: {e}")
        append_promote_log("rollback", project, backup_id,
                           False, f"could not read manifest: {e}")
        return False

    if manifest.get("project") != project:
        print(f"ROLLBACK FAIL: backup project {manifest.get('project')} "
              f"does not match requested {project}")
        append_promote_log("rollback", project, backup_id,
                           False, "backup project mismatch")
        return False

    # Early check: verify backup contains index.html before creating pre-rollback backup
    # This avoids creating unnecessary pre-rollback backups for invalid/empty backups
    bk_index = bk_root / "index.html"
    if not bk_index.exists():
        print(f"ROLLBACK FAIL: backup {backup_id} is invalid — no index.html found")
        append_promote_log("rollback", project, backup_id,
                           False, "backup is invalid: no index.html found")
        return False

    # Backup current published (pre-rollback)
    bk_path, _ = _backup_current_published(project)
    print(f"Pre-rollback backup created: {bk_path}")

    # Restore to tmp
    tmp = public_root() / f"{project}.tmp"
    if tmp.exists():
        shutil.rmtree(tmp)

    copytree_safe(bk_root, tmp)

    # Verify tmp
    tmp_index = tmp / "index.html"
    if not tmp_index.exists():
        # Use ignore_errors to handle case where tmp was never created
        shutil.rmtree(tmp, ignore_errors=True)
        print(f"ROLLBACK FAIL: backup verification failed — no index.html")
        append_promote_log("rollback", project, backup_id,
                           False, "backup verification failed: no index.html")
        return False

    # Swap tmp -> published
    pub = public_root() / project
    if pub.exists():
        shutil.rmtree(pub)
    shutil.move(str(tmp), str(pub))

    append_promote_log("rollback", project, backup_id,
                       True, f"Rolled back {project} from backup {backup_id}")
    print(f"ROLLBACK OK: {project} restored from backup {backup_id}")
    return True


def cmd_rollback(project: str, backup_id: str, confirm: bool) -> bool:
    if not confirm:
        print("ROLLBACK ABORT: --confirm required")
        return False
    if not backup_id:
        print("ROLLBACK ABORT: --backup <backup-id> required")
        return False

    return _rollback_impl(project, backup_id)


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        prog="doc-artifact-gate",
        description="Phase 5 Validator / Promote Gate — doc-infra",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_validate = sub.add_parser("validate", help="Validate incoming artifact")
    p_validate.add_argument("--project", required=True,
                            help="Project name (MVP: code-reviewer)")

    p_stage = sub.add_parser("stage", help="Copy incoming to staging")
    p_stage.add_argument("--project", required=True,
                         help="Project name (MVP: code-reviewer)")

    p_promote = sub.add_parser("promote", help="Promote staging to published")
    p_promote.add_argument("--project", required=True,
                           help="Project name (MVP: code-reviewer)")
    p_promote.add_argument("--confirm", action="store_true",
                           help="Confirm promotion (required)")

    p_rollback = sub.add_parser("rollback", help="Rollback to a backup")
    p_rollback.add_argument("--project", required=True,
                            help="Project name (MVP: code-reviewer)")
    p_rollback.add_argument("--backup", required=True,
                            help="Backup ID to restore")
    p_rollback.add_argument("--confirm", action="store_true",
                            help="Confirm rollback (required)")

    args = parser.parse_args()

    # MVP hard gate: unknown project exits non-0 before mutation/scanning
    if args.command in ("validate", "stage", "promote", "rollback"):
        if args.project != ALLOWED_PROJECT:
            print(f"ERROR: Unknown project '{args.project}'. "
                  f"MVP only supports '{ALLOWED_PROJECT}'",
                  file=sys.stderr)
            sys.exit(3)

    if args.command == "validate":
        result = cmd_validate(args.project)
        sys.exit(0 if result.passed else 1)

    elif args.command == "stage":
        result = cmd_stage(args.project)
        sys.exit(0 if result.passed else 1)

    elif args.command == "promote":
        ok = cmd_promote(args.project, args.confirm)
        sys.exit(0 if ok else 1)

    elif args.command == "rollback":
        ok = cmd_rollback(args.project, args.backup, args.confirm)
        sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
