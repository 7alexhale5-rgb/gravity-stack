#!/usr/bin/env bash
# Run all golden dataset evals — one config per skill
set -euo pipefail
cd "$(dirname "$0")"

echo "=== Golden Dataset Regression Tests ==="
echo ""

total_pass=0
total_fail=0
total_error=0

for config in promptfooconfig.yaml configs/*.yaml; do
  skill=$(basename "$config" .yaml)
  [ "$skill" = "promptfooconfig" ] && skill="planning-stack"
  echo "--- $skill ---"
  output=$(promptfoo eval --config "$config" 2>&1)

  # Extract results line
  passed=$(echo "$output" | grep -o '[0-9]* passed' | head -1 | grep -o '[0-9]*' || echo "0")
  failed=$(echo "$output" | grep -o '[0-9]* failed' | head -1 | grep -o '[0-9]*' || echo "0")
  errors=$(echo "$output" | grep -o '[0-9]* errors' | head -1 | grep -o '[0-9]*' || echo "0")

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
