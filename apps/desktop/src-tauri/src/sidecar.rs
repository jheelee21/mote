//! Launch, supervise and stop the Python sidecar.
//!
//! In development set `MOTE_API_URL` (and optionally `MOTE_API_TOKEN`) to use a
//! backend you started yourself; no sidecar is spawned then.

use std::net::TcpListener;
use std::sync::Mutex;

use rand::{distributions::Alphanumeric, Rng};
use serde::Serialize;
use tauri::{AppHandle, Manager};
use tauri_plugin_shell::process::{CommandChild, CommandEvent};
use tauri_plugin_shell::ShellExt;

const MAX_RESTARTS: u32 = 3;

#[derive(Clone, Serialize)]
pub struct BackendInfo {
    pub url: String,
    pub token: String,
}

#[derive(Default)]
struct SidecarState {
    child: Mutex<Option<CommandChild>>,
    restarts: Mutex<u32>,
}

pub fn start(app: &AppHandle) -> Result<BackendInfo, Box<dyn std::error::Error>> {
    if let Ok(url) = std::env::var("MOTE_API_URL") {
        let token = std::env::var("MOTE_API_TOKEN").unwrap_or_else(|_| "dev".into());
        log::info!("using external backend at {url}");
        return Ok(BackendInfo { url, token });
    }

    let port = free_port()?;
    let token: String = rand::thread_rng()
        .sample_iter(&Alphanumeric)
        .take(32)
        .map(char::from)
        .collect();
    let data_dir = app.path().app_data_dir()?;
    std::fs::create_dir_all(&data_dir)?;

    app.manage(SidecarState::default());
    spawn(app, port, &token, &data_dir.to_string_lossy())?;

    Ok(BackendInfo {
        url: format!("http://127.0.0.1:{port}"),
        token,
    })
}

fn spawn(
    app: &AppHandle,
    port: u16,
    token: &str,
    data_dir: &str,
) -> Result<(), Box<dyn std::error::Error>> {
    let (mut rx, child) = app
        .shell()
        .sidecar("mote-sidecar")?
        .args([
            "serve",
            "--port",
            &port.to_string(),
            "--token",
            token,
            "--data-dir",
            data_dir,
        ])
        .spawn()?;

    *app.state::<SidecarState>().child.lock().unwrap() = Some(child);

    let handle = app.clone();
    let token = token.to_string();
    let data_dir = data_dir.to_string();
    tauri::async_runtime::spawn(async move {
        while let Some(event) = rx.recv().await {
            match event {
                CommandEvent::Stdout(line) | CommandEvent::Stderr(line) => {
                    log::info!("[sidecar] {}", String::from_utf8_lossy(&line).trim_end());
                }
                CommandEvent::Terminated(status) => {
                    log::warn!("sidecar exited: {status:?}");
                    let state = handle.state::<SidecarState>();
                    let mut restarts = state.restarts.lock().unwrap();
                    if *restarts < MAX_RESTARTS {
                        *restarts += 1;
                        drop(restarts);
                        if let Err(e) = spawn(&handle, port, &token, &data_dir) {
                            log::error!("failed to restart sidecar: {e}");
                        }
                    }
                    break;
                }
                _ => {}
            }
        }
    });
    Ok(())
}

pub fn stop(app: &AppHandle) {
    if let Some(state) = app.try_state::<SidecarState>() {
        // Prevent the supervisor from restarting it while we shut down.
        *state.restarts.lock().unwrap() = MAX_RESTARTS;
        if let Some(child) = state.child.lock().unwrap().take() {
            let _ = child.kill();
        }
    }
}

fn free_port() -> std::io::Result<u16> {
    Ok(TcpListener::bind("127.0.0.1:0")?.local_addr()?.port())
}
