def carry_budget_dial(cfg: dict, ws: pathlib.Path, dry: bool = False) -> str:
    """Put the tenant's budget dial where the unattended sweep can read it, and start its ledger.

    The workspace's own dial files (notify.json / config.json - the two names the runtime already reads:
    engine/notify/apply_email.py) are what a cron run can see. The tenant config lives in the operator's
    checkout, which a customer host does not have, so a provisioned account whose dial never travelled
    would fall back to the gate's built-in default and say so on every single sweep. The ledger is
    created empty here for the same reason provisioning touches usage/<slug>.jsonl: metering starts on
    the first run rather than on the first successful write.

    Never fatal: the gate degrades to a default it can see and reports it, which beats a provisioning
    run that fails over a dial.
    """
    budget = cfg.get("budget") if isinstance(cfg.get("budget"), dict) else {}
    if dry:
        return f"budget dial: {'would be carried' if budget else 'nothing to carry (the gate defaults apply)'}"
    try:
        sys.path.insert(0, str(ROOT / "engine" / "gates"))
        import model_budget  # noqa: PLC0415

        path = (model_budget.write_budget(ws, daily_usd=budget.get("daily_usd"),
                                          on_exceed=budget.get("on_exceed"),
                                          throttle_rate=budget.get("throttle_rate"))
                if budget else None)
        ledger = model_budget.ledger_path(ws)
        ledger.parent.mkdir(parents=True, exist_ok=True)
        ledger.touch()
        return f"budget dial: {path if path else 'none in the config, the gate defaults apply'}; ledger {ledger}"
    except Exception as e:  # a dial that could not travel must not stop the account being created
        return f"WARN the budget dial could not be carried into the workspace: {e}"


