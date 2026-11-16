use crate::sidecar::BackendInfo;

/// Where the UI should send API requests, and the token to send with them.
#[tauri::command]
pub fn backend_info(info: tauri::State<'_, BackendInfo>) -> BackendInfo {
    info.inner().clone()
}
