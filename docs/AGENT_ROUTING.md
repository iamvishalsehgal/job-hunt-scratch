# Task routing: cheap model vs strong model

Rule: any cheap-model output must pass the verification command from AGENTS.md
before it is accepted. Strong-model areas always get a strong-model review.

## CHEAP-MODEL SAFE
Mechanical, spec-clear, no silent-failure risk.
- Add a boundary-case test to scale/artifacts/new/test_model_budget.py (e.g. spend
  exactly at the cap, dial exactly on the threshold).
- Add type hints/docstrings to scale/artifacts/modified/cost_report.py or
  tenant_config.py.
- Consolidate the duplicated model_budget.py copies (scale/model_budget.py and
  scale/artifacts/new/model_budget.py) into one import path.

## STRONG-MODEL ONLY
Architecture, cross-module, silent-failure, security, or production config.
- Change the pricing constants in tools/price_model.py (the gate asserts its
  literals equal price_model's — a mismatch silently mis-bills every account).
- Reorder the dial-read precedence in model_budget.py (notify.json -> config.json
  -> --config); a wrong order changes spend limits with no error.
- Change the /api/usage response shape in dashboard/server.py (both the dashboard
  and the operator CLI read it; a drift breaks both without a crash).
