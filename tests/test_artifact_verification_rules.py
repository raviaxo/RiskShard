"""ADR-0026's two fields are checked, and the checks say what they mean.

A declared property is only worth declaring if something rejects a malformed
one and something notices when it goes stale. The split matters and is the whole
design:

  **Malformed is an error.** One field without the other, a hash that is not a
  hash, a date that is not a date — those are typos, and a typo in a provenance
  field is worse than no field because it reads as assurance.

  **Stale is a warning.** The publisher reissued the file. Our reading was
  honest when it was made and is now a reading of a document we no longer hold.
  That is the mechanism working, not a defect, and failing the build on it would
  punish the maintainer for someone else's release schedule.

  **Absent is silence.** Most records have never been checked. Saying so on every
  run would drown the finding in a count of things nobody claimed.
"""
import unittest

from engine.evidence_quality import validate_artifact_verification

SHA = "c579c711f3004db660c547e4c73be6b0e4997cb5b76fffacabebacf928f99eae"
OTHER_SHA = "f" * 64


def codes(issues):
    return {i["code"] for i in issues}


def severities(issues):
    return {i["severity"] for i in issues}


class ArtifactVerificationRuleTests(unittest.TestCase):
    def record(self, **kwargs):
        base = {"id": "a_record"}
        base.update(kwargs)
        return base

    def test_a_record_claiming_nothing_is_not_nagged(self):
        """Absence means nobody has checked, and that is not an issue to report."""
        issues = validate_artifact_verification(self.record(), {"sha256": SHA})
        self.assertEqual(issues, [])

    def test_a_matching_hash_passes_clean(self):
        issues = validate_artifact_verification(
            self.record(artifact_verified_at="2026-11-20", artifact_verified_sha256=SHA),
            {"sha256": SHA},
        )
        self.assertEqual(issues, [])

    def test_a_date_without_a_hash_is_an_error(self):
        """A verification that cannot expire is the thing ADR-0026 rejected."""
        issues = validate_artifact_verification(
            self.record(artifact_verified_at="2026-11-20"), {"sha256": SHA}
        )
        self.assertIn("artifact_verification_incomplete", codes(issues))
        self.assertEqual(severities(issues), {"error"})

    def test_a_hash_without_a_date_is_an_error(self):
        issues = validate_artifact_verification(
            self.record(artifact_verified_sha256=SHA), {"sha256": SHA}
        )
        self.assertIn("artifact_verification_incomplete", codes(issues))

    def test_a_malformed_hash_is_an_error_not_a_mismatch(self):
        """Reporting a typo as "the publisher reissued it" would send someone reading."""
        issues = validate_artifact_verification(
            self.record(artifact_verified_at="2026-11-20", artifact_verified_sha256="nope"),
            {"sha256": SHA},
        )
        self.assertIn("artifact_verified_sha256_malformed", codes(issues))
        self.assertNotIn("artifact_verification_stale", codes(issues))

    def test_an_uppercase_hash_is_rejected_rather_than_silently_lowered(self):
        """Comparison is on the stored string; two spellings would read as two files."""
        issues = validate_artifact_verification(
            self.record(
                artifact_verified_at="2026-11-20", artifact_verified_sha256=SHA.upper()
            ),
            {"sha256": SHA},
        )
        self.assertIn("artifact_verified_sha256_malformed", codes(issues))

    def test_a_malformed_date_is_an_error(self):
        issues = validate_artifact_verification(
            self.record(artifact_verified_at="last tuesday", artifact_verified_sha256=SHA),
            {"sha256": SHA},
        )
        self.assertIn("artifact_verified_at_malformed", codes(issues))

    def test_a_reissued_file_warns_rather_than_fails(self):
        issues = validate_artifact_verification(
            self.record(artifact_verified_at="2026-11-20", artifact_verified_sha256=SHA),
            {"sha256": OTHER_SHA},
        )
        self.assertEqual(codes(issues), {"artifact_verification_stale"})
        self.assertEqual(severities(issues), {"warning"})

    def test_the_stale_message_names_the_date_it_was_verified(self):
        """"Needs re-reading" is unactionable without saying how old the reading is."""
        issues = validate_artifact_verification(
            self.record(artifact_verified_at="2026-11-20", artifact_verified_sha256=SHA),
            {"sha256": OTHER_SHA},
        )
        self.assertIn("2026-11-20", issues[0]["message"])

    def test_a_source_with_no_stored_hash_cannot_pin_and_says_so(self):
        """Silence here would let an unpinnable verification pass as a pinned one."""
        issues = validate_artifact_verification(
            self.record(artifact_verified_at="2026-11-20", artifact_verified_sha256=SHA),
            {},
        )
        self.assertEqual(codes(issues), {"artifact_verification_unpinnable"})
        self.assertEqual(severities(issues), {"warning"})


if __name__ == "__main__":
    unittest.main()
