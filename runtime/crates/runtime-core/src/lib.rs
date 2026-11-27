//! Local lifecycle and discovery core for RCoder Runtime.
//!
//! The first runtime slice deliberately manages only the lifetime of a local
//! RCoder MCP process. It does not execute agent tools or grant permissions.

mod discovery;
mod session;

pub use discovery::{ConfigIssue, DetectedServer, DetectionReport, detect_project};
pub use session::{SessionSnapshot, attach_until_parent_exits, list_sessions};
