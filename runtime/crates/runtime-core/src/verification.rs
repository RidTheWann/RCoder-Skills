//! Bounded, read-only inspection of evidence artifacts.
//!
//! This module deliberately answers a narrow question: does a confined,
//! inspectable artifact exist inside the project, and do its bytes match a
//! declared SHA-256 digest? It never executes a command taken from an evidence
//! record, never reads file contents into a report, and never proves that a
//! claimed check actually ran. A verification report is a separate, auditable
//! observation that cannot by itself satisfy an acceptance criterion.

use std::collections::HashSet;
use std::fs::{self, File};
use std::io::Read;
use std::path::{Component, Path, PathBuf};

use anyhow::Result;
use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};

use crate::task::EvidenceOutcome;

/// Largest artifact the verifier will inspect. Oversized artifacts produce an
/// explicit verdict; they are never partially read or silently truncated.
pub const MAX_ARTIFACT_BYTES: u64 = 262_144;

/// Bounded verification history per task, independent of evidence history.
pub const MAX_VERIFICATION_RECORDS: usize = 200;

const MAX_ARTIFACT_PATH_CHARS: usize = 4_096;
const MAX_PROVENANCE_CHARS: usize = 200;
const MAX_REPORT_CASES: usize = 200;
const MAX_CASE_NAME_CHARS: usize = 200;
const SCHEMA_VERSION: u32 = 1;

/// Bounded, versioned artifact references accepted by the verifier.
pub const MAX_ARTIFACT_REFERENCES: usize = 10;
pub const ALLOWED_PARSERS: &[&str] = &["rcoder_test_report_v1"];

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum VerificationVerdict {
    /// The artifact was inspected and its bytes matched the declared digest.
    DigestMatch,
    /// The artifact was inspected and its bytes differed from the declared digest.
    DigestMismatch,
    /// The artifact was inspected; no digest was declared for comparison.
    Inspected,
    /// The artifact path did not resolve to an existing file.
    Missing,
    /// The path was absolute, traversed outside the project, or used a symlink.
    UnsafePath,
    /// The path resolved to something other than a regular file.
    NotRegularFile,
    /// The artifact exceeded the byte bound and was not inspected.
    TooLarge,
    /// The declared digest was not 64 hexadecimal characters and was not checked.
    InvalidDigest,
    /// The artifact changed between the first read and the stability re-check.
    MutatedDuringInspection,
}

impl VerificationVerdict {
    pub fn as_str(self) -> &'static str {
        match self {
            Self::DigestMatch => "digest_match",
            Self::DigestMismatch => "digest_mismatch",
            Self::Inspected => "inspected",
            Self::Missing => "missing",
            Self::UnsafePath => "unsafe_path",
            Self::NotRegularFile => "not_regular_file",
            Self::TooLarge => "too_large",
            Self::InvalidDigest => "invalid_digest",
            Self::MutatedDuringInspection => "mutated_during_inspection",
        }
    }

    /// Whether the artifact bytes were actually inspected. Even `true` only
    /// establishes artifact existence and content; it is not proof of execution.
    pub fn is_inspectable(self) -> bool {
        matches!(
            self,
            Self::DigestMatch | Self::DigestMismatch | Self::Inspected
        )
    }
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct VerificationReport {
    pub schema_version: u32,
    /// Evidence record this inspection is linked to. The task API supplies it;
    /// callers cannot forge the linkage through the artifact path.
    pub evidence_id: String,
    pub criterion_id: String,
    /// Normalized, project-relative artifact path using forward slashes.
    pub artifact: String,
    pub size_bytes: u64,
    /// SHA-256 of the inspected bytes, or an empty string if nothing was read.
    pub sha256: String,
    pub verdict: VerificationVerdict,
    /// Fixed-vocabulary explanation. Never contains file contents.
    pub detail: String,
    /// Caller-supplied clock value, so identical inputs yield identical reports.
    pub inspected_at_unix: u64,
    /// Snapshot of the caller's attestation, never the verifier's conclusion.
    #[serde(default)]
    pub declared_outcome: Option<EvidenceOutcome>,
    /// Bounded provenance reference supplied with the artifact reference.
    #[serde(default)]
    pub provenance: String,
    /// The acceptance cycle this observation belongs to.
    #[serde(default)]
    pub cycle_start_index: usize,
    /// Deterministically extracted test outcomes, when an allowlisted parser ran.
    #[serde(default)]
    pub outcome: Option<OutcomeExtraction>,
    /// Explicit verification conclusion. Older reports leave this unset and the
    /// conclusion is derived conservatively from the recorded verdict.
    #[serde(default)]
    pub verification_state: Option<VerificationState>,
}

fn report(
    evidence_id: &str,
    criterion_id: &str,
    artifact: &str,
    now_unix: u64,
    size_bytes: u64,
    sha256: &str,
    verdict: VerificationVerdict,
    detail: &str,
) -> VerificationReport {
    VerificationReport {
        schema_version: SCHEMA_VERSION,
        evidence_id: evidence_id.to_string(),
        criterion_id: criterion_id.to_string(),
        artifact: artifact.to_string(),
        size_bytes,
        sha256: sha256.to_string(),
        verdict,
        detail: detail.to_string(),
        inspected_at_unix: now_unix,
        declared_outcome: None,
        provenance: String::new(),
        cycle_start_index: 0,
        outcome: None,
        verification_state: None,
    }
}

pub(crate) fn normalized_relative(artifact: &str) -> Option<PathBuf> {
    if artifact.is_empty() || artifact.chars().count() > MAX_ARTIFACT_PATH_CHARS {
        return None;
    }
    let mut relative = PathBuf::new();
    for component in Path::new(artifact).components() {
        match component {
            Component::Normal(part) => relative.push(part),
            _ => return None,
        }
    }
    if relative.as_os_str().is_empty() {
        None
    } else {
        Some(relative)
    }
}

fn display_relative(relative: &Path) -> String {
    relative
        .components()
        .filter_map(|component| match component {
            Component::Normal(part) => Some(part.to_string_lossy().into_owned()),
            _ => None,
        })
        .collect::<Vec<_>>()
        .join("/")
}

fn has_symlink_component(root: &Path, relative: &Path) -> bool {
    let mut current = root.to_path_buf();
    for component in relative.components() {
        current.push(component);
        match fs::symlink_metadata(&current) {
            Ok(metadata) if metadata.file_type().is_symlink() => return true,
            Ok(_) => {}
            Err(_) => return false,
        }
    }
    false
}

fn valid_digest(value: &str) -> bool {
    value.len() == 64 && value.bytes().all(|byte| byte.is_ascii_hexdigit())
}

pub(crate) fn sha256_hex(bytes: &[u8]) -> String {
    let digest = Sha256::digest(bytes);
    let mut output = String::with_capacity(digest.len() * 2);
    for byte in digest {
        use std::fmt::Write as _;
        let _ = write!(&mut output, "{byte:02x}");
    }
    output
}

/// Inspect one bounded artifact inside `project_root`.
///
/// `artifact` is untrusted data: absolute paths, `..` traversal, symlinks and
/// oversized files are refused with an explicit verdict. The clock is explicit
/// so a repeat inspection with identical inputs produces an identical report.
pub fn inspect_artifact(
    project_root: &Path,
    evidence_id: &str,
    criterion_id: &str,
    artifact: &str,
    expected_sha256: Option<&str>,
    now_unix: u64,
) -> VerificationReport {
    let display = display_relative(Path::new(artifact));
    let normalized = match normalized_relative(artifact) {
        Some(path) => path,
        None => {
            return report(
                evidence_id,
                criterion_id,
                &display,
                now_unix,
                0,
                "",
                VerificationVerdict::UnsafePath,
                "artifact path must be a bounded relative path without traversal",
            );
        }
    };
    let display = display_relative(&normalized);

    let root = match project_root.canonicalize() {
        Ok(root) => root,
        Err(_) => {
            return report(
                evidence_id,
                criterion_id,
                &display,
                now_unix,
                0,
                "",
                VerificationVerdict::UnsafePath,
                "project root could not be resolved",
            );
        }
    };
    let candidate = root.join(&normalized);
    if has_symlink_component(&root, &normalized) {
        return report(
            evidence_id,
            criterion_id,
            &display,
            now_unix,
            0,
            "",
            VerificationVerdict::UnsafePath,
            "artifact path contains a symlink component",
        );
    }

    if let Some(expected) = expected_sha256 {
        if !valid_digest(expected) {
            return report(
                evidence_id,
                criterion_id,
                &display,
                now_unix,
                0,
                "",
                VerificationVerdict::InvalidDigest,
                "declared digest must be 64 hexadecimal characters",
            );
        }
    }

    let resolved = match candidate.canonicalize() {
        Ok(path) => path,
        Err(error) if error.kind() == std::io::ErrorKind::NotFound => {
            return report(
                evidence_id,
                criterion_id,
                &display,
                now_unix,
                0,
                "",
                VerificationVerdict::Missing,
                "artifact does not exist",
            );
        }
        Err(_) => {
            return report(
                evidence_id,
                criterion_id,
                &display,
                now_unix,
                0,
                "",
                VerificationVerdict::UnsafePath,
                "artifact path could not be resolved",
            );
        }
    };
    if !resolved.starts_with(&root) || resolved == root {
        return report(
            evidence_id,
            criterion_id,
            &display,
            now_unix,
            0,
            "",
            VerificationVerdict::UnsafePath,
            "artifact resolves outside the project root",
        );
    }
    let metadata = match fs::symlink_metadata(&resolved) {
        Ok(metadata) => metadata,
        Err(_) => {
            return report(
                evidence_id,
                criterion_id,
                &display,
                now_unix,
                0,
                "",
                VerificationVerdict::Missing,
                "artifact could not be inspected",
            );
        }
    };
    if metadata.file_type().is_symlink() || !metadata.is_file() {
        return report(
            evidence_id,
            criterion_id,
            &display,
            now_unix,
            0,
            "",
            VerificationVerdict::NotRegularFile,
            "artifact is not a regular file",
        );
    }
    if metadata.len() > MAX_ARTIFACT_BYTES {
        return report(
            evidence_id,
            criterion_id,
            &display,
            now_unix,
            metadata.len(),
            "",
            VerificationVerdict::TooLarge,
            "artifact exceeds the inspection byte bound",
        );
    }

    let file = match File::open(&resolved) {
        Ok(file) => file,
        Err(_) => {
            return report(
                evidence_id,
                criterion_id,
                &display,
                now_unix,
                0,
                "",
                VerificationVerdict::Missing,
                "artifact could not be opened",
            );
        }
    };
    let mut bytes = Vec::new();
    let read = match file.take(MAX_ARTIFACT_BYTES + 1).read_to_end(&mut bytes) {
        Ok(read) => read as u64,
        Err(_) => {
            return report(
                evidence_id,
                criterion_id,
                &display,
                now_unix,
                0,
                "",
                VerificationVerdict::Missing,
                "artifact could not be read",
            );
        }
    };
    if read > MAX_ARTIFACT_BYTES {
        return report(
            evidence_id,
            criterion_id,
            &display,
            now_unix,
            read,
            "",
            VerificationVerdict::TooLarge,
            "artifact exceeds the inspection byte bound",
        );
    }

    let digest = sha256_hex(&bytes);
    let (verdict, detail) = match expected_sha256 {
        None => (
            VerificationVerdict::Inspected,
            "artifact inspected; no digest was declared for comparison",
        ),
        Some(expected) if digest.eq_ignore_ascii_case(expected) => (
            VerificationVerdict::DigestMatch,
            "artifact inspected and declared digest matched",
        ),
        Some(_) => (
            VerificationVerdict::DigestMismatch,
            "artifact inspected and declared digest did not match",
        ),
    };
    report(
        evidence_id,
        criterion_id,
        &display,
        now_unix,
        read,
        &digest,
        verdict,
        detail,
    )
}

/// Verifier conclusions. `CallerAttested` describes an unexamined claim; it is
/// never produced by artifact inspection.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum VerificationState {
    CallerAttested,
    ArtifactVerified,
    IntegrityOnly,
    Failed,
    InsufficientEvidence,
}

impl VerificationState {
    pub fn as_str(self) -> &'static str {
        match self {
            Self::CallerAttested => "caller_attested",
            Self::ArtifactVerified => "artifact_verified",
            Self::IntegrityOnly => "integrity_only",
            Self::Failed => "failed",
            Self::InsufficientEvidence => "insufficient_evidence",
        }
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum ExtractedOutcome {
    Pass,
    Fail,
    Insufficient,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct OutcomeExtraction {
    pub parser: String,
    pub outcome: ExtractedOutcome,
    pub passed: u32,
    pub failed: u32,
    pub skipped: u32,
    pub errors: u32,
    pub detail: String,
}

impl VerificationVerdict {
    /// Whether the inspected bytes were available for outcome extraction.
    pub fn is_integrity_ok(self) -> bool {
        matches!(self, Self::DigestMatch | Self::Inspected)
    }
}

impl VerificationReport {
    /// Conservative conclusion for this observation. Legacy reports without an
    /// explicit state are never upgraded to `ArtifactVerified`.
    pub fn verification_state(&self) -> VerificationState {
        if let Some(state) = self.verification_state {
            return state;
        }
        match &self.outcome {
            Some(extraction) => match extraction.outcome {
                ExtractedOutcome::Pass if self.verdict.is_integrity_ok() => {
                    VerificationState::ArtifactVerified
                }
                ExtractedOutcome::Fail => VerificationState::Failed,
                _ => VerificationState::InsufficientEvidence,
            },
            None if self.verdict == VerificationVerdict::DigestMatch => {
                VerificationState::IntegrityOnly
            }
            None => VerificationState::InsufficientEvidence,
        }
    }
}

/// Opt-in requirement stored on an acceptance criterion. Contracts without it
/// keep the original caller-attested completion behavior.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ArtifactVerificationRequirement {
    pub parser: String,
    #[serde(default)]
    pub require_digest: bool,
}

impl ArtifactVerificationRequirement {
    pub fn validate(&self) -> Result<()> {
        if !ALLOWED_PARSERS.contains(&self.parser.as_str()) {
            anyhow::bail!("unsupported artifact parser: {}", self.parser);
        }
        Ok(())
    }
}

/// Bounded, versioned reference to one verification artifact. The declared
/// outcome and provenance are stored alongside the verifier's own conclusion.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ArtifactReference {
    pub schema_version: u32,
    pub artifact: String,
    pub parser: Option<String>,
    #[serde(default)]
    pub expected_sha256: Option<String>,
    #[serde(default)]
    pub criterion_id: Option<String>,
    #[serde(default)]
    pub evidence_id: String,
    #[serde(default)]
    pub declared_outcome: Option<EvidenceOutcome>,
    #[serde(default)]
    pub provenance: String,
}

impl ArtifactReference {
    pub fn validate(&self) -> Result<()> {
        if self.schema_version != 1 {
            anyhow::bail!("unsupported artifact reference schema version");
        }
        if normalized_relative(&self.artifact).is_none() {
            anyhow::bail!("artifact path must be a bounded workspace-relative path");
        }
        if uuid::Uuid::parse_str(&self.evidence_id).is_err() {
            anyhow::bail!("evidence ID must be a UUID");
        }
        if self.provenance.chars().count() > MAX_PROVENANCE_CHARS {
            anyhow::bail!("provenance exceeds {MAX_PROVENANCE_CHARS} characters");
        }
        if let Some(parser) = &self.parser {
            if !ALLOWED_PARSERS.contains(&parser.as_str()) {
                anyhow::bail!("unsupported artifact parser: {parser}");
            }
        }
        if let Some(digest) = &self.expected_sha256 {
            if !valid_digest(digest) {
                anyhow::bail!("expected digest must be 64 hexadecimal characters");
            }
        }
        Ok(())
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum OutcomeError {
    UnsupportedFormat,
    Malformed,
    CriterionMismatch,
    Insufficient,
}

impl OutcomeError {
    pub fn detail(self) -> &'static str {
        match self {
            Self::UnsupportedFormat => "unsupported artifact format",
            Self::Malformed => "artifact report is malformed or contradictory",
            Self::CriterionMismatch => "artifact report names a different acceptance criterion",
            Self::Insufficient => "artifact report lacks sufficient passing cases",
        }
    }
}

#[derive(Debug, Deserialize)]
#[serde(deny_unknown_fields)]
struct TestReportV1 {
    schema: String,
    criterion_id: String,
    summary: ReportSummary,
    cases: Vec<ReportCase>,
}

#[derive(Debug, Deserialize)]
#[serde(deny_unknown_fields)]
struct ReportSummary {
    passed: u32,
    failed: u32,
    skipped: u32,
    errors: u32,
}

#[derive(Debug, Deserialize)]
#[serde(deny_unknown_fields)]
struct ReportCase {
    name: String,
    outcome: String,
}

/// Extract a deterministic outcome from one allowlisted artifact format. No
/// command, script, plugin, or user-defined code is ever executed here.
pub fn extract_outcome(
    bytes: &[u8],
    parser: &str,
    criterion_id: &str,
) -> std::result::Result<OutcomeExtraction, OutcomeError> {
    if parser != "rcoder_test_report_v1" {
        return Err(OutcomeError::UnsupportedFormat);
    }
    let report: TestReportV1 =
        serde_json::from_slice(bytes).map_err(|_| OutcomeError::Malformed)?;
    if report.schema != "rcoder-test-report/v1" {
        return Err(OutcomeError::UnsupportedFormat);
    }
    if report.criterion_id != criterion_id {
        return Err(OutcomeError::CriterionMismatch);
    }
    if report.cases.len() > MAX_REPORT_CASES {
        return Err(OutcomeError::Malformed);
    }
    let mut names = HashSet::new();
    let mut passed = 0u32;
    let mut failed = 0u32;
    let mut skipped = 0u32;
    let mut errors = 0u32;
    for case in &report.cases {
        if case.name.is_empty()
            || case.name.chars().count() > MAX_CASE_NAME_CHARS
            || !names.insert(&case.name)
        {
            return Err(OutcomeError::Malformed);
        }
        match case.outcome.as_str() {
            "pass" => passed += 1,
            "fail" => failed += 1,
            "skip" => skipped += 1,
            "error" => errors += 1,
            _ => return Err(OutcomeError::Malformed),
        }
    }
    if report.summary.passed != passed
        || report.summary.failed != failed
        || report.summary.skipped != skipped
        || report.summary.errors != errors
    {
        return Err(OutcomeError::Malformed);
    }
    let (outcome, detail) = if failed > 0 || errors > 0 {
        (
            ExtractedOutcome::Fail,
            "report contains failing or errored cases",
        )
    } else if passed == 0 {
        (
            ExtractedOutcome::Insufficient,
            "report contains no passing cases",
        )
    } else {
        (
            ExtractedOutcome::Pass,
            "report contains passing cases and no failures or errors",
        )
    };
    Ok(OutcomeExtraction {
        parser: parser.to_string(),
        outcome,
        passed,
        failed,
        skipped,
        errors,
        detail: detail.to_string(),
    })
}

/// Re-read the same confined artifact within the byte bound. Used to prove the
/// inspected snapshot was stable before any outcome is attributed to it.
pub(crate) fn read_bounded_snapshot(root: &Path, relative: &Path) -> Option<Vec<u8>> {
    let root = root.canonicalize().ok()?;
    if has_symlink_component(&root, relative) {
        return None;
    }
    let resolved = root.join(relative).canonicalize().ok()?;
    if !resolved.starts_with(&root) || resolved == root {
        return None;
    }
    let metadata = fs::symlink_metadata(&resolved).ok()?;
    if metadata.file_type().is_symlink()
        || !metadata.is_file()
        || metadata.len() > MAX_ARTIFACT_BYTES
    {
        return None;
    }
    let file = File::open(&resolved).ok()?;
    let mut bytes = Vec::new();
    let read = file
        .take(MAX_ARTIFACT_BYTES + 1)
        .read_to_end(&mut bytes)
        .ok()? as u64;
    if read > MAX_ARTIFACT_BYTES {
        return None;
    }
    Some(bytes)
}

/// Whether a second bounded read still matches the digest of the first snapshot.
pub fn stable_snapshot_matches(project_root: &Path, artifact: &str, observed_digest: &str) -> bool {
    let Some(relative) = normalized_relative(artifact) else {
        return false;
    };
    match read_bounded_snapshot(project_root, &relative) {
        Some(bytes) => sha256_hex(&bytes).eq_ignore_ascii_case(observed_digest),
        None => false,
    }
}

#[cfg(test)]
mod tests {
    use std::fs;
    use std::path::PathBuf;

    use super::*;

    struct Fixture {
        root: PathBuf,
    }

    impl Fixture {
        fn new(label: &str) -> Self {
            let root = std::env::temp_dir().join(format!(
                "rcoder-verification-{label}-{}-{}",
                std::process::id(),
                uuid::Uuid::new_v4()
            ));
            fs::create_dir_all(&root).expect("fixture root");
            Self { root }
        }

        fn write(&self, relative: &str, bytes: &[u8]) {
            let path = self.root.join(relative);
            if let Some(parent) = path.parent() {
                fs::create_dir_all(parent).expect("fixture parent");
            }
            fs::write(path, bytes).expect("fixture file");
        }

        fn path(&self) -> &Path {
            &self.root
        }
    }

    impl Drop for Fixture {
        fn drop(&mut self) {
            let _ = fs::remove_dir_all(&self.root);
        }
    }

    fn sha256_of(bytes: &[u8]) -> String {
        sha256_hex(bytes)
    }

    #[test]
    fn matching_declared_digest_produces_a_deterministic_report() {
        let fixture = Fixture::new("match");
        fixture.write("artifacts/test.log", b"all tests passed\n");
        let digest = sha256_of(b"all tests passed\n");

        let first = inspect_artifact(
            fixture.path(),
            "evidence-1",
            "AC-001",
            "artifacts/test.log",
            Some(&digest),
            1_700_000_000,
        );
        let second = inspect_artifact(
            fixture.path(),
            "evidence-1",
            "AC-001",
            "artifacts/test.log",
            Some(&digest),
            1_700_000_000,
        );
        assert_eq!(first, second);
        assert_eq!(first.verdict, VerificationVerdict::DigestMatch);
        assert!(first.verdict.is_inspectable());
        assert_eq!(first.size_bytes, 17);
        assert_eq!(first.sha256, digest);
        assert_eq!(first.evidence_id, "evidence-1");
        assert_eq!(first.criterion_id, "AC-001");
        assert!(!first.detail.contains("all tests passed"));
    }

    #[test]
    fn wrong_digest_is_reported_without_claiming_verification() {
        let fixture = Fixture::new("mismatch");
        fixture.write("report.txt", b"payload");
        let wrong = "0".repeat(64);
        let report = inspect_artifact(
            fixture.path(),
            "evidence-2",
            "AC-001",
            "report.txt",
            Some(&wrong),
            42,
        );
        assert_eq!(report.verdict, VerificationVerdict::DigestMismatch);
        assert!(report.verdict.is_inspectable());
        assert_ne!(report.sha256, wrong);
    }

    #[test]
    fn no_declared_digest_yields_inspected_not_verified() {
        let fixture = Fixture::new("inspected");
        fixture.write("report.txt", b"payload");
        let report = inspect_artifact(
            fixture.path(),
            "evidence-3",
            "AC-001",
            "report.txt",
            None,
            42,
        );
        assert_eq!(report.verdict, VerificationVerdict::Inspected);
        assert_eq!(report.sha256.len(), 64);
    }

    #[test]
    fn missing_artifact_is_reported() {
        let fixture = Fixture::new("missing");
        let report = inspect_artifact(
            fixture.path(),
            "evidence-4",
            "AC-001",
            "absent.txt",
            None,
            42,
        );
        assert_eq!(report.verdict, VerificationVerdict::Missing);
        assert_eq!(report.sha256, "");
    }

    #[test]
    fn absolute_and_traversal_paths_are_refused() {
        let fixture = Fixture::new("paths");
        let outside = fixture.path().join("outside.txt");
        fs::write(&outside, b"secret").expect("outside file");

        for artifact in [
            "/etc/passwd",
            "../outside.txt",
            "./report.txt",
            "a/../../outside.txt",
        ] {
            let report =
                inspect_artifact(fixture.path(), "evidence-5", "AC-001", artifact, None, 42);
            assert_eq!(
                report.verdict,
                VerificationVerdict::UnsafePath,
                "{artifact}"
            );
            assert_eq!(report.size_bytes, 0);
        }
    }

    #[cfg(unix)]
    #[test]
    fn symlinks_inside_and_outside_the_project_are_refused() {
        let fixture = Fixture::new("symlinks");
        fixture.write("inside.txt", b"inside");
        let outside = fixture.path().join("..").join("rcoder-outside-target.txt");
        fs::write(&outside, b"outside").expect("outside target");
        std::os::unix::fs::symlink(
            fixture.path().join("inside.txt"),
            fixture.path().join("link-inside.txt"),
        )
        .expect("inside symlink");
        std::os::unix::fs::symlink(&outside, fixture.path().join("link-outside.txt"))
            .expect("outside symlink");

        for artifact in ["link-inside.txt", "link-outside.txt"] {
            let report =
                inspect_artifact(fixture.path(), "evidence-6", "AC-001", artifact, None, 42);
            assert_eq!(
                report.verdict,
                VerificationVerdict::UnsafePath,
                "{artifact}"
            );
        }
        let _ = fs::remove_file(&outside);
    }

    #[test]
    fn directories_are_not_inspected_as_files() {
        let fixture = Fixture::new("directory");
        fs::create_dir(fixture.path().join("folder")).expect("fixture directory");
        let report = inspect_artifact(fixture.path(), "evidence-7", "AC-001", "folder", None, 42);
        assert_eq!(report.verdict, VerificationVerdict::NotRegularFile);
    }

    #[test]
    fn oversized_artifacts_are_not_truncated_or_inspected() {
        let fixture = Fixture::new("oversized");
        let bytes = vec![b'x'; (MAX_ARTIFACT_BYTES + 1) as usize];
        fixture.write("large.bin", &bytes);
        let report = inspect_artifact(
            fixture.path(),
            "evidence-8",
            "AC-001",
            "large.bin",
            None,
            42,
        );
        assert_eq!(report.verdict, VerificationVerdict::TooLarge);
        assert_eq!(report.sha256, "");
        assert_eq!(report.size_bytes, MAX_ARTIFACT_BYTES + 1);
    }

    #[test]
    fn malformed_digests_are_rejected_before_reading_bytes() {
        let fixture = Fixture::new("bad-digest");
        fixture.write("report.txt", b"payload");
        for digest in ["abc", &"z".repeat(64)] {
            let report = inspect_artifact(
                fixture.path(),
                "evidence-9",
                "AC-001",
                "report.txt",
                Some(digest),
                42,
            );
            assert_eq!(report.verdict, VerificationVerdict::InvalidDigest);
            assert_eq!(report.sha256, "");
        }
    }

    fn report_bytes(cases: &[(&str, &str)], passed: u32, failed: u32) -> Vec<u8> {
        let skipped = cases.iter().filter(|case| case.1 == "skip").count() as u32;
        let errors = cases.iter().filter(|case| case.1 == "error").count() as u32;
        serde_json::to_vec(&serde_json::json!({
            "schema": "rcoder-test-report/v1",
            "criterion_id": "AC-001",
            "summary": {
                "passed": passed,
                "failed": failed,
                "skipped": skipped,
                "errors": errors,
            },
            "cases": cases.iter().map(|(name, outcome)| serde_json::json!({
                "name": name,
                "outcome": outcome,
            })).collect::<Vec<_>>(),
        }))
        .expect("serialize report fixture")
    }

    #[test]
    fn allowlisted_passing_report_extracts_pass() {
        let bytes = report_bytes(&[("unit-one", "pass"), ("unit-two", "pass")], 2, 0);
        let outcome = extract_outcome(&bytes, "rcoder_test_report_v1", "AC-001")
            .expect("extract passing report");
        assert_eq!(outcome.outcome, ExtractedOutcome::Pass);
        assert_eq!(outcome.passed, 2);
        assert_eq!(outcome.failed, 0);
    }

    #[test]
    fn failing_and_mixed_reports_never_extract_pass() {
        let failing = report_bytes(&[("unit-one", "fail")], 0, 1);
        let mixed = report_bytes(&[("unit-one", "pass"), ("unit-two", "fail")], 1, 1);
        for bytes in [&failing, &mixed] {
            let outcome = extract_outcome(bytes, "rcoder_test_report_v1", "AC-001")
                .expect("extract failing report");
            assert_eq!(outcome.outcome, ExtractedOutcome::Fail);
            assert!(outcome.failed > 0);
        }
    }

    #[test]
    fn empty_and_skipped_only_reports_are_insufficient() {
        let empty = report_bytes(&[], 0, 0);
        let skipped = report_bytes(&[("unit-one", "skip")], 0, 0);
        for bytes in [&empty, &skipped] {
            let outcome = extract_outcome(bytes, "rcoder_test_report_v1", "AC-001")
                .expect("extract insufficient report");
            assert_eq!(outcome.outcome, ExtractedOutcome::Insufficient);
        }
    }

    #[test]
    fn malformed_contradictory_and_duplicate_reports_are_rejected() {
        let malformed = b"not json".to_vec();
        assert_eq!(
            extract_outcome(&malformed, "rcoder_test_report_v1", "AC-001").unwrap_err(),
            OutcomeError::Malformed
        );

        let contradictory = serde_json::to_vec(&serde_json::json!({
            "schema": "rcoder-test-report/v1",
            "criterion_id": "AC-001",
            "summary": {"passed": 9, "failed": 0, "skipped": 0, "errors": 0},
            "cases": [{"name": "unit-one", "outcome": "pass"}],
        }))
        .expect("serialize contradictory report");
        assert_eq!(
            extract_outcome(&contradictory, "rcoder_test_report_v1", "AC-001").unwrap_err(),
            OutcomeError::Malformed
        );

        let duplicate = report_bytes(&[("same-name", "pass"), ("same-name", "pass")], 2, 0);
        assert_eq!(
            extract_outcome(&duplicate, "rcoder_test_report_v1", "AC-001").unwrap_err(),
            OutcomeError::Malformed
        );

        let unknown_field = serde_json::to_vec(&serde_json::json!({
            "schema": "rcoder-test-report/v1",
            "criterion_id": "AC-001",
            "extra": "unexpected",
            "summary": {"passed": 0, "failed": 0, "skipped": 0, "errors": 0},
            "cases": [],
        }))
        .expect("serialize report with unknown field");
        assert_eq!(
            extract_outcome(&unknown_field, "rcoder_test_report_v1", "AC-001").unwrap_err(),
            OutcomeError::Malformed
        );
    }

    #[test]
    fn unsupported_formats_and_criterion_mismatch_are_refused() {
        let bytes = report_bytes(&[("unit-one", "pass")], 1, 0);
        assert_eq!(
            extract_outcome(&bytes, "arbitrary_script", "AC-001").unwrap_err(),
            OutcomeError::UnsupportedFormat
        );
        assert_eq!(
            extract_outcome(&bytes, "rcoder_test_report_v1", "AC-002").unwrap_err(),
            OutcomeError::CriterionMismatch
        );
    }

    #[test]
    fn stability_check_detects_file_mutation() {
        let fixture = Fixture::new("stable");
        fixture.write("report.txt", b"first snapshot");
        let first = inspect_artifact(fixture.path(), "evidence", "AC-001", "report.txt", None, 1);
        assert_eq!(first.verdict, VerificationVerdict::Inspected);
        assert!(stable_snapshot_matches(
            fixture.path(),
            "report.txt",
            &first.sha256
        ));

        fixture.write("report.txt", b"changed snapshot");
        assert!(!stable_snapshot_matches(
            fixture.path(),
            "report.txt",
            &first.sha256
        ));
    }

    #[test]
    fn legacy_inspection_reports_are_never_artifact_verified() {
        let fixture = Fixture::new("legacy-state");
        fixture.write("report.txt", b"payload");
        let digest = sha256_of(b"payload");
        let report = inspect_artifact(
            fixture.path(),
            "evidence",
            "AC-001",
            "report.txt",
            Some(&digest),
            1,
        );
        assert_eq!(
            report.verification_state(),
            VerificationState::IntegrityOnly
        );
        let inspected =
            inspect_artifact(fixture.path(), "evidence", "AC-001", "report.txt", None, 1);
        assert_eq!(
            inspected.verification_state(),
            VerificationState::InsufficientEvidence
        );
    }

    #[test]
    fn artifact_references_are_bounded_and_allowlisted() {
        let evidence = uuid::Uuid::new_v4().to_string();
        let valid = ArtifactReference {
            schema_version: 1,
            artifact: "artifacts/report.json".to_string(),
            parser: Some("rcoder_test_report_v1".to_string()),
            expected_sha256: None,
            criterion_id: Some("AC-001".to_string()),
            evidence_id: evidence.clone(),
            declared_outcome: Some(EvidenceOutcome::Pass),
            provenance: "cli:local".to_string(),
        };
        assert!(valid.validate().is_ok());

        let mut unsupported = valid.clone();
        unsupported.parser = Some("python:exec".to_string());
        assert!(unsupported.validate().is_err());

        let mut traversal = valid.clone();
        traversal.artifact = "../outside.json".to_string();
        assert!(traversal.validate().is_err());

        let mut wrong_version = valid;
        wrong_version.schema_version = 2;
        assert!(wrong_version.validate().is_err());
    }
}
