mod commands;
mod sidecar;

use tauri::Manager;

pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .plugin(tauri_plugin_dialog::init())
        .plugin(tauri_plugin_opener::init())
        .setup(|app| {
            let info = sidecar::start(app.handle())?;
            app.manage(info);
            Ok(())
        })
        .invoke_handler(tauri::generate_handler![commands::backend_info])
        .build(tauri::generate_context!())
        .expect("error while building Mote")
        .run(|app, event| {
            if let tauri::RunEvent::Exit = event {
                sidecar::stop(app);
            }
        });
}
