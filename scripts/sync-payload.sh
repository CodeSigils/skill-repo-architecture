#!/usr/bin/env bash
# Regenerate or verify the shipped skill payload from root reference sources.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
MANIFEST="$ROOT/scripts/payload-manifest.json"
PAYLOAD_DIR="$ROOT/skills/skill-repo-architecture"
CI_MODE=false
SELF_TEST=false

[ "${1:-}" = "--ci" ] && CI_MODE=true
[ "${1:-}" = "--self-test" ] && SELF_TEST=true

[ -f "$MANIFEST" ] || { echo "FAIL: manifest not found"; exit 1; }
[ -f "$PAYLOAD_DIR/SKILL.md" ] || { echo "FAIL: payload SKILL.md not found"; exit 1; }

json_list() {
    local key="$1"
    python3 -c "import json; d=json.load(open('$MANIFEST')); print('\n'.join(str(x) for x in d.get('$key', [])))"
}

ref_mode() {
    python3 -c "import json; d=json.load(open('$MANIFEST')); r=d.get('references', ''); print(r if isinstance(r, str) else '')"
}

is_covered() {
    local rel="$1"
    case "$rel" in
        SKILL.md) return 0 ;;
    esac
    while IFS= read -r f; do
        [ -n "$f" ] || continue
        [ "$rel" = "$f" ] && return 0
    done < <(json_list files)
    while IFS= read -r s; do
        [ -n "$s" ] || continue
        [ "$rel" = "scripts/$s" ] && return 0
    done < <(json_list scripts)
    if [ "$(ref_mode)" = "*" ]; then
        case "$rel" in references/*) return 0 ;; esac
    fi
    return 1
}

check_declared_files() {
    local drift=false
    while IFS= read -r f; do
        [ -n "$f" ] || continue
        source="$ROOT/$f"
        target="$PAYLOAD_DIR/$f"
        if [ ! -f "$source" ]; then
            echo "  MISSING source: $f"
            drift=true
        elif [ ! -f "$target" ]; then
            echo "  MISSING payload: $f"
            drift=true
        elif ! diff -q "$source" "$target" >/dev/null; then
            echo "  DRIFT: $f"
            drift=true
        fi
    done < <(json_list files)
    while IFS= read -r s; do
        [ -n "$s" ] || continue
        source="$ROOT/scripts/$s"
        target="$PAYLOAD_DIR/scripts/$s"
        if [ ! -f "$source" ]; then
            echo "  MISSING source: scripts/$s"
            drift=true
        elif [ ! -f "$target" ]; then
            echo "  MISSING payload: scripts/$s"
            drift=true
        elif ! diff -q "$source" "$target" >/dev/null; then
            echo "  DRIFT: scripts/$s"
            drift=true
        fi
    done < <(json_list scripts)
    $drift && return 1
    return 0
}

check_references() {
    local drift=false
    [ "$(ref_mode)" = "*" ] || return 0
    while IFS= read -r source; do
        name="$(basename "$source")"
        target="$PAYLOAD_DIR/references/$name"
        if [ ! -f "$target" ]; then
            echo "  MISSING payload: references/$name"
            drift=true
        elif ! diff -q "$source" "$target" >/dev/null; then
            echo "  DRIFT: references/$name"
            drift=true
        fi
    done < <(find "$ROOT/references" -maxdepth 1 -type f -name '*.md' | sort)
    while IFS= read -r target; do
        name="$(basename "$target")"
        if [ ! -f "$ROOT/references/$name" ]; then
            echo "  ORPHANED: references/$name"
            drift=true
        fi
    done < <(find "$PAYLOAD_DIR/references" -maxdepth 1 -type f -name '*.md' 2>/dev/null | sort)
    $drift && return 1
    return 0
}

check_orphans() {
    local drift=false
    while IFS= read -r -d '' f; do
        rel="${f#$PAYLOAD_DIR/}"
        if ! is_covered "$rel"; then
            echo "  ORPHANED: $rel"
            drift=true
        fi
    done < <(find "$PAYLOAD_DIR" -type f -print0)
    $drift && return 1
    return 0
}

sync_payload() {
    while IFS= read -r f; do
        [ -n "$f" ] || continue
        source="$ROOT/$f"
        target="$PAYLOAD_DIR/$f"
        if [ ! -f "$source" ]; then echo "  MISSING source: $f"; return 1; fi
        mkdir -p "$(dirname "$target")"
        install -m 644 "$source" "$target"
    done < <(json_list files)
    while IFS= read -r s; do
        [ -n "$s" ] || continue
        source="$ROOT/scripts/$s"
        target="$PAYLOAD_DIR/scripts/$s"
        if [ ! -f "$source" ]; then echo "  MISSING source: scripts/$s"; return 1; fi
        mkdir -p "$(dirname "$target")"
        if [ -x "$source" ]; then install -m 755 "$source" "$target"; else install -m 644 "$source" "$target"; fi
    done < <(json_list scripts)
    if [ "$(ref_mode)" = "*" ]; then
        mkdir -p "$PAYLOAD_DIR/references"
        find "$PAYLOAD_DIR/references" -type f -delete 2>/dev/null || true
        cp "$ROOT/references/"*.md "$PAYLOAD_DIR/references/"
    fi
    while IFS= read -r -d '' f; do
        rel="${f#$PAYLOAD_DIR/}"
        if ! is_covered "$rel"; then
            echo "  ORPHANED: $rel"
            rm -f "$f"
        fi
    done < <(find "$PAYLOAD_DIR" -type f -print0)
    find "$PAYLOAD_DIR" -type d -empty -delete 2>/dev/null || true
}

if [ "$SELF_TEST" = true ]; then
    echo "Running sync-payload.sh self-tests..."
    python3 -c "import json; json.load(open('$MANIFEST'))"
    echo "  PASS  manifest is valid JSON"
    bash "$0" --ci
    echo "  PASS  payload is in sync"
    exit 0
fi

if [ "$CI_MODE" = true ]; then
    echo "Checking skill payload..."
    drift=false
    check_declared_files || drift=true
    check_references || drift=true
    check_orphans || drift=true
    if [ "$drift" = true ]; then
        echo ""
        echo "DRIFT DETECTED"
        exit 1
    fi
    echo "Payload in sync"
else
    echo "Syncing skill payload..."
    sync_payload
    echo "Payload synced"
fi
