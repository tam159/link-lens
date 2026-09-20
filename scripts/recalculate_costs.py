"""Recalculate published-rate estimates; no model calls or receipt mutation.

Default: reads the saved ledger offline. --refresh-ledger reads application DB.
"""

import argparse
import json
from pathlib import Path
from link_lens.pricing import collect, estimate

parser = argparse.ArgumentParser()
parser.add_argument("--refresh-ledger", action="store_true")
args = parser.parse_args()
root = Path("outputs")
ledger = root / "cost-usage.json"
if args.refresh_ledger:
    ledger.write_text(json.dumps(collect(), indent=2) + "\n")
report = estimate(json.loads(ledger.read_text()))
(root / "cost-summary.json").write_text(json.dumps(report, indent=2) + "\n")
# Keep original measured receipt totals/billing fields unchanged; append named estimate.
p = root / "measurement-summary.json"
m = json.loads(p.read_text())
m["published_rate_estimate"] = {
    k: v for k, v in report.items() if k not in ["call_details", "pricing_snapshot"]
}
m["published_rate_estimate"]["pricing_verified_on"] = report["pricing_snapshot"][
    "verified_on"
]
m["published_rate_estimate"]["source_url"] = report["pricing_snapshot"]["source_url"]
p.write_text(json.dumps(m, indent=2) + "\n")
print(
    json.dumps(
        {
            k: report[k]
            for k in [
                "calls",
                "priced_calls",
                "unpriced_calls",
                "measured_subtotal_usd",
                "complete_estimated_total_usd",
            ]
        },
        indent=2,
    )
)
