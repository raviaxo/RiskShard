# Data Pack Releases

Named data-pack release artifacts belong here when a governed source, evidence,
extraction, calibration, taxonomy, threat-library, or schema snapshot is ready
to pin for review.

Create a release artifact with:

```bash
python scripts/data_pack_manifest.py --release 2026.06.15
```

The release JSON includes the data-pack fingerprint and the governed file
manifest. It does not include raw source downloads from `sources/raw/`.
