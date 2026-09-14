if python3 -B tests/structure/remarp_eval_test.py; then
  pass "Remarp eval confines setup and requires fresh compiled slide output"
else
  fail "Remarp eval confines setup and requires fresh compiled slide output"
fi
