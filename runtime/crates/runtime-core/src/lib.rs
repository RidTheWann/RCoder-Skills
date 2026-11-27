//! Local lifecycle and discovery core for RCoder Runtime.
//!
//! Runtime tracks local RCoder MCP process lifetimes and persists typed task
//! contracts. It does not execute agent tools or grant host permissions.

mod discovery;
mod instruction;
mod session;
mod task;
mod verification;

pub use discovery::{ConfigIssue, DetectedServer, DetectionReport, detect_project};
pub use instruction::{
    CompiledCriterion, CompiledEvidence, CompiledTask, CompiledVerification, InstructionPacket,
    InstructionPolicy, compile_task,
};
pub use session::{SessionSnapshot, attach_until_parent_exits, list_sessions};
pub use task::{
    AcceptanceCriterion, EvidenceOutcome, EvidenceRecord, RiskLevel, StatusTransition,
    TaskContract, TaskStatus, create_task, get_task, list_tasks, record_evidence,
    require_artifact_verification, transition_task, verify_artifact_references,
    verify_task_evidence,
};
pub use verification::{
    ALLOWED_PARSERS, ArtifactReference, ArtifactVerificationRequirement, ExtractedOutcome,
    MAX_ARTIFACT_BYTES, MAX_ARTIFACT_REFERENCES, MAX_VERIFICATION_RECORDS, OutcomeError,
    OutcomeExtraction, VerificationReport, VerificationState, VerificationVerdict, extract_outcome,
    inspect_artifact, stable_snapshot_matches,
};
