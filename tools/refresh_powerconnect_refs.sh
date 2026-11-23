#!/bin/sh
# Rebuild powerconnect/reference/*.md (all except data-model.md) from the live
# documentation at docs.rhondos.com. Run from the repository root.
set -eu
WORK="${1:-$(mktemp -d)}"
mkdir -p "$WORK/docs"
curl -fsSL -A "docs-reader" -o "$WORK/llms.txt" https://docs.rhondos.com/llms.txt
for slug in summary-of-extractors-and-event_type-s list-of-event-types \
            list-of-dashboards-dynatrace list-of-alerts-dynatrace \
            list-of-correlation-searches; do
  curl -fsSL -A "docs-reader" \
    -o "$WORK/docs/powerconnect-for-sap-solutions__$slug.md" \
    "https://docs.rhondos.com/powerconnect-for-sap-solutions/$slug.md"
done
python3 -I tools/build_powerconnect_refs.py "$WORK/docs" powerconnect/reference
echo "References rebuilt from $WORK"
