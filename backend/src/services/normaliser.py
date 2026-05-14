from fastapi import HTTPException


def normalise_sap(raw: dict) -> dict:
    required = ["system_description", "gamp5_category", "intended_uses", "assurance_strategy"]
    _check_keys(raw, required, "SAP")
    return raw


def normalise_pra(raw: dict) -> dict:
    required = ["risk_classifications", "total_features", "high_risk_count", "not_high_risk_count"]
    _check_keys(raw, required, "PRA")
    return raw


def normalise_rtm(raw: dict) -> dict:
    _check_keys(raw, ["requirements"], "RTM")
    return raw


def normalise_stp(raw: dict) -> dict:
    _check_keys(raw, ["test_cases"], "STP")
    return raw


def normalise_utr(raw: dict) -> dict:
    _check_keys(raw, ["test_records"], "UTR")
    return raw


def normalise_asr(raw: dict) -> dict:
    _check_keys(raw, ["overall_conclusion", "coverage_summary", "system_fitness"], "ASR")
    return raw


def _check_keys(data: dict, keys: list[str], doc_name: str) -> None:
    missing = [k for k in keys if k not in data]
    if missing:
        raise HTTPException(
            status_code=500,
            detail=f"{doc_name} generation returned incomplete data. Missing fields: {', '.join(missing)}"
        )
