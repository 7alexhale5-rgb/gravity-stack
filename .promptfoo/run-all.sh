#!/usr/bin/env bash
# Run all golden dataset evals — one config per skill
set -euo pipefail
cd "$(dirname "$0")"

echo "=== Golden Dataset Regression Tests ==="
echo ""

total_pass=0
total_fail=0
total_error=0
run_error=0
results_dir=$(mktemp -d)
trap 'rm -rf "$results_dir"' EXIT

for config in promptfooconfig.yaml configs/*.yaml; do
  skill=$(basename "$config" .yaml)
  [ "$skill" = "promptfooconfig" ] && skill="planning-stack"
  echo "--- $skill ---"
  result="$results_dir/$skill.json"
  cli_status=0
  # Keep complete provider output private; the summary never prints credentials.
  promptfoo eval --config "$config" --output "$result" > "$results_dir/$skill.log" 2>&1 || cli_status=$?
  counts=$(python3 - "$result" <<'PY'
import json, sys
try:
    with open(sys.argv[1]) as file:
        stats = json.load(file)['results']['stats']
    counts = [stats[key] for key in ('successes', 'failures', 'errors')]
    if any(type(value) is not int or value < 0 for value in counts) or sum(counts) == 0:
        raise ValueError('invalid or empty counts')
except (OSError, ValueError, KeyError, TypeError):
    sys.exit(1)
print(*counts)
PY
  ) || { echo "  FAIL invalid, missing or empty evaluation result"; run_error=$((run_error+1)); continue; }
  read -r passed failed errors <<< "$counts"
  if [[ $cli_status -ne 0 ]]; then
    echo "  FAIL evaluation CLI exited $cli_status"
    run_error=$((run_error+1))
  fi

  total_pass=$((total_pass + passed))
  total_fail=$((total_fail + failed))
  total_error=$((total_error + errors))

  if [ "$failed" = "0" ] && [ "$errors" = "0" ]; then
    echo "  ✓ $passed passed"
  else
    echo "  ✗ $passed passed, $failed failed, $errors errors"
  fi
done

echo ""
echo "=== Summary ==="
total=$((total_pass + total_fail + total_error))
echo "  $total_pass/$total passed ($(( total_pass * 100 / (total > 0 ? total : 1) ))%)"
echo "  $total_fail failed, $total_error errors"
echo "  $run_error runner errors"
[[ $total -gt 0 && $total_fail -eq 0 && $total_error -eq 0 && $run_error -eq 0 ]]
