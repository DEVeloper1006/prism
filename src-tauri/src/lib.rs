use rand::RngCore;

#[tauri::command]
fn get_token(state: tauri::State<'_, AppState>) -> String {
    state.session_token.clone()
}

#[tauri::command]
async fn open_folder() -> Result<Option<String>, String> {
    // TODO: use tauri-plugin-dialog to pick a folder
    Ok(None)
}

struct AppState {
    session_token: String,
}

pub fn run() {
    let mut key = [0u8; 32];
    rand::thread_rng().fill_bytes(&mut key);
    let token = hex::encode(key);

    tauri::Builder::default()
        .plugin(tauri_plugin_log::Builder::default().build())
        .plugin(tauri_plugin_shell::init())
        .plugin(tauri_plugin_dialog::init())
        .manage(AppState {
            session_token: token,
        })
        .invoke_handler(tauri::generate_handler![get_token, open_folder])
        .setup(|_app| {
            // TODO: spawn Python sidecar with session token
            Ok(())
        })
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
