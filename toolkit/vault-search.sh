#!/bin/bash
# vault-search.sh — Fast knowledge-vault search with frontmatter-aware filtering
# 3-layer pattern: search → filter → fetch
# Works over one or more Obsidian-style vaults.
#
# Configure by setting GRAVITY_VAULTS to a colon-separated list of directories
# before invoking, e.g.:
#   export GRAVITY_VAULTS="$HOME/vault:$HOME/research"
# Defaults scan "$HOME/vault" only if the env var is unset.
#
# Usage:
#   vault-search.sh search "query" [--type=TYPE] [--project=PROJECT] [--since=DAYS] [--limit=N]
#   vault-search.sh timeline "query" [--before=N] [--after=N]
#   vault-search.sh fetch ID1,ID2,ID3
#   vault-search.sh index [--stats]

set -uo pipefail

# Colon-separated vault paths; override via GRAVITY_VAULTS env var
VAULT_LIST="${GRAVITY_VAULTS:-$HOME/vault}"
IFS=':' read -ra VAULT_DIRS <<< "$VAULT_LIST"
INDEX_FILE="$HOME/.claude/vault-search-index.tsv"
INDEX_MAX_AGE=86400  # 24 hours

# --- Index Builder ---
build_index() {
  local count=0
  local id=1
  > "$INDEX_FILE"  # truncate

  for vault in "${VAULT_DIRS[@]}"; do
    [ -d "$vault" ] || continue
    while IFS= read -r file; do
      # Extract frontmatter fields
      local date="" type="" project="" tags="" title=""
      local in_frontmatter=0
      local line_num=0

      while IFS= read -r line; do
        line_num=$((line_num + 1))
        if [ "$line_num" -eq 1 ] && [ "$line" = "---" ]; then
          in_frontmatter=1
          continue
        fi
        if [ "$in_frontmatter" -eq 1 ] && [ "$line" = "---" ]; then
          break
        fi
        if [ "$in_frontmatter" -eq 1 ]; then
          case "$line" in
            date:*)    date="${line#date: }" ;;
            type:*)    type="${line#type: }" ;;
            project:*) project="${line#project: }" ;;
            tags:*)    tags="${line#tags: }" ;;
          esac
        fi
      done < "$file"

      # Extract title from first H1
      title=$(grep -m1 '^# ' "$file" 2>/dev/null | sed 's/^# //' || echo "$(basename "$file" .md)")

      # TSV: id, date, type, project, tags, title, path
      printf '%d\t%s\t%s\t%s\t%s\t%s\t%s\n' \
        "$id" "$date" "$type" "$project" "$tags" "$title" "$file" >> "$INDEX_FILE"

      id=$((id + 1))
      count=$((count + 1))
    done < <(find "$vault" -name "*.md" -not -path "*/.obsidian/*" -not -name "CLAUDE.md" | sort)
  done

  echo "Indexed $count files → $INDEX_FILE"
}

# --- Ensure Index ---
ensure_index() {
  if [ ! -f "$INDEX_FILE" ]; then
    build_index >/dev/null 2>&1
    return
  fi
  local age=$(( $(date +%s) - $(stat -f %m "$INDEX_FILE" 2>/dev/null || stat -c %Y "$INDEX_FILE" 2>/dev/null || echo 0) ))
  if [ "$age" -gt "$INDEX_MAX_AGE" ]; then
    build_index >/dev/null 2>&1
  fi
}

# --- Search ---
cmd_search() {
  ensure_index
  local query="" type_filter="" project_filter="" since_days="" limit=20

  while [ $# -gt 0 ]; do
    case "$1" in
      --type=*)    type_filter="${1#--type=}" ;;
      --project=*) project_filter="${1#--project=}" ;;
      --since=*)   since_days="${1#--since=}" ;;
      --limit=*)   limit="${1#--limit=}" ;;
      *)           query="$1" ;;
    esac
    shift
  done

  local results=""

  if [ -n "$query" ]; then
    # Convert multi-word query to regex pattern (word1.*word2 or word1|word2)
    local pattern
    if echo "$query" | grep -q ' '; then
      # Multi-word: match any word (OR)
      pattern=$(echo "$query" | sed 's/ /|/g')
    else
      pattern="$query"
    fi

    # Search both index (title/tags) and file content
    results=$(grep -iE "$pattern" "$INDEX_FILE" 2>/dev/null || true)

    # Also grep file content and merge by ID
    local content_matches=""
    content_matches=$(grep -rlE -i "$pattern" "${VAULT_DIRS[@]}" 2>/dev/null \
      | grep '\.md$' \
      | grep -v '.obsidian' \
      | grep -v 'CLAUDE.md' || true)

    if [ -n "$content_matches" ]; then
      while IFS= read -r match_file; do
        local idx_line
        idx_line=$(grep "$match_file" "$INDEX_FILE" 2>/dev/null || true)
        if [ -n "$idx_line" ] && ! echo "$results" | grep -qF "$match_file"; then
          results=$(printf '%s\n%s' "$results" "$idx_line")
        fi
      done <<< "$content_matches"
    fi
  else
    results=$(cat "$INDEX_FILE")
  fi

  # Apply filters
  if [ -n "$type_filter" ]; then
    results=$(echo "$results" | awk -F'\t' -v t="$type_filter" '$3 ~ t')
  fi
  if [ -n "$project_filter" ]; then
    results=$(echo "$results" | awk -F'\t' -v p="$project_filter" '$4 ~ p')
  fi
  if [ -n "$since_days" ]; then
    local cutoff
    cutoff=$(date -v-"${since_days}d" +%Y-%m-%d 2>/dev/null || date -d "-${since_days} days" +%Y-%m-%d 2>/dev/null)
    if [ -n "$cutoff" ]; then
      results=$(echo "$results" | awk -F'\t' -v c="$cutoff" '$2 >= c')
    fi
  fi

  # Sort by date desc, limit
  results=$(echo "$results" | grep -v '^$' | sort -t$'\t' -k2 -r | head -n "$limit")

  if [ -z "$results" ] || [ "$results" = "" ]; then
    echo "No results found."
    return
  fi

  # Format output as markdown table
  echo "| ID | Date | Type | Project | Title |"
  echo "|----|------|------|---------|-------|"
  echo "$results" | while IFS=$'\t' read -r id date type project tags title path; do
    printf '| %s | %s | %s | %s | %s |\n' "$id" "$date" "$type" "$project" "$title"
  done
}

# --- Timeline ---
cmd_timeline() {
  ensure_index
  local query="" before=3 after=3

  while [ $# -gt 0 ]; do
    case "$1" in
      --before=*) before="${1#--before=}" ;;
      --after=*)  after="${1#--after=}" ;;
      *)          query="$1" ;;
    esac
    shift
  done

  if [ -z "$query" ]; then
    echo "Usage: vault-search.sh timeline \"query\" [--before=N] [--after=N]"
    return 1
  fi

  # Find anchor: first match by date desc
  local anchor_line
  anchor_line=$(grep -i "$query" "$INDEX_FILE" 2>/dev/null | sort -t$'\t' -k2 -r | head -1)

  if [ -z "$anchor_line" ]; then
    echo "No anchor found for: $query"
    return 1
  fi

  local anchor_date
  anchor_date=$(echo "$anchor_line" | cut -f2)

  # Get surrounding entries by date proximity
  local all_sorted
  all_sorted=$(sort -t$'\t' -k2 "$INDEX_FILE")

  local anchor_line_num
  anchor_line_num=$(echo "$all_sorted" | grep -n "$anchor_date" | head -1 | cut -d: -f1)

  local start=$((anchor_line_num - before))
  [ "$start" -lt 1 ] && start=1
  local end=$((anchor_line_num + after))

  local timeline
  timeline=$(echo "$all_sorted" | sed -n "${start},${end}p")

  echo "| ID | Date | Type | Project | Title |"
  echo "|----|------|------|---------|-------|"
  echo "$timeline" | while IFS=$'\t' read -r id date type project tags title path; do
    local marker=""
    if echo "$title" | grep -qi "$query"; then
      marker=" **←**"
    fi
    printf '| %s | %s | %s | %s | %s%s |\n' "$id" "$date" "$type" "$project" "$title" "$marker"
  done
}

# --- Fetch ---
cmd_fetch() {
  ensure_index
  local ids="$1"

  IFS=',' read -ra id_arr <<< "$ids"
  for id in "${id_arr[@]}"; do
    local line
    line=$(awk -F'\t' -v i="$id" '$1 == i' "$INDEX_FILE")
    if [ -z "$line" ]; then
      echo "## ID $id: Not found"
      continue
    fi
    local path
    path=$(echo "$line" | cut -f7)
    echo "## ID $id: $(basename "$path")"
    echo '```'
    cat "$path"
    echo '```'
    echo ""
  done
}

# --- Stats ---
cmd_stats() {
  ensure_index
  local total
  total=$(wc -l < "$INDEX_FILE" | tr -d ' ')
  echo "Vault Search Index Stats"
  echo "========================"
  echo "Total files: $total"
  echo "Index file: $INDEX_FILE"
  echo "Index age: $(( ($(date +%s) - $(stat -f %m "$INDEX_FILE" 2>/dev/null || stat -c %Y "$INDEX_FILE" 2>/dev/null || echo 0)) / 60 )) minutes"
  echo ""
  echo "By type:"
  cut -f3 "$INDEX_FILE" | sort | uniq -c | sort -rn
  echo ""
  echo "By project:"
  cut -f4 "$INDEX_FILE" | sort | uniq -c | sort -rn | head -15
}

# --- Main ---
case "${1:-help}" in
  search)   shift; cmd_search "$@" ;;
  timeline) shift; cmd_timeline "$@" ;;
  fetch)    shift; cmd_fetch "$@" ;;
  index)    shift; build_index; [ "${1:-}" = "--stats" ] && cmd_stats ;;
  stats)    cmd_stats ;;
  help|*)
    echo "vault-search — Memory vault search with 3-layer pattern"
    echo ""
    echo "Usage:"
    echo "  vault-search search \"query\" [--type=TYPE] [--project=PROJECT] [--since=DAYS] [--limit=N]"
    echo "  vault-search timeline \"query\" [--before=N] [--after=N]"
    echo "  vault-search fetch ID1,ID2,ID3"
    echo "  vault-search index [--stats]"
    echo "  vault-search stats"
    ;;
esac
