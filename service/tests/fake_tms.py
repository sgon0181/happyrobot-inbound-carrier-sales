"""TMS records for tests, shaped like live LOAD_GET replies after the protocol trims padding."""


def make_load(load_id: str = "LD09001", **overrides: str) -> dict[str, str]:
    load = {
        "LOAD_ID": load_id,
        "ORIG_CITY": "Dallas",
        "ORIG_STATE": "TX",
        "ORIG_ZIP": "75201",
        "DEST_CITY": "Atlanta",
        "DEST_STATE": "GA",
        "DEST_ZIP": "30303",
        "PICKUP_DT": "20991231080000",
        "DELIVERY_DT": "20991231200000",
        "EQTYPE": "DRY_VAN",
        "RATE": "2000",
        "WEIGHT": "42000",
        "COMMODITY": "General Freight",
        "PIECES": "24",
        "MILES": "780",
        "DIMS": "53ft x 8ft x 9ft",
        "NOTES": "",
        "STATUS": "OPEN",
        "MAX_BUY": "2300",
    }
    return load | overrides
