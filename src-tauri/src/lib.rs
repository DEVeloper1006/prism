use rand::RngCore;
use tauri_plugin_dialog::DialogExt;
use tauri_plugin_shell::ShellExt;

#[tauri::command]
fn get_token(state: tauri::State<'_, AppState>) -> String {
    state.session_token.clone()
}

#[tauri::command]
async fn open_folder(app: tauri::AppHandle) -> Result<Option<String>, String> {
    let folder = app
        .dialog()
        .file()
        .blocking_pick_folder();

    Ok(folder.map(|p| p.to_string()))
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
            session_token: token.clone(),
        })
        .invoke_handler(tauri::generate_handler![get_token, open_folder])
        .setup(move |app| {
            let handle = app.handle().clone();
            let token_arg = token.clone();

            tauri::async_runtime::spawn(async move {
                let _ = handle
                    .shell()
                    .command("python3")
                    .args(["backend/main.py", "--token", &token_arg])
                    .spawn();
            });

            Ok(())
        })
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
