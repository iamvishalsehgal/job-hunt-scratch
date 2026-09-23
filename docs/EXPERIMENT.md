# Cost experiment: run this prompt unchanged in two agents/models

## Prompt (copy verbatim)

In scale/artifacts/modified/test_dashboard.py, add one unit test that asserts
a read of /api/usage without the auth token returns 401. Do not change any
production code. Run `python3 -m py_compile scale/artifacts/modified/test_dashboard.py`
and report whether it passes, plus any import errors you hit.

## Compare across the two runs
- Tests passing (compile/run result)
- Retries needed (how many self-correct attempts before the edit was right)
- Wall time (seconds)
- Input tokens / output tokens
- Cost (USD)
- Cache-hit rate (%)

Note: the test cannot be *executed* until the jobhunt-agent source
(dashboard/, engine/, tools/, billing/) is recovered; the compile check plus a
correct 401 assertion is the pass bar for now.
