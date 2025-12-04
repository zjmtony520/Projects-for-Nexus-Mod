import os
import json
import shutil
import subprocess
import datetime
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

CONFIG_FILE = "safe_mode_config.json"
STATE_FILE = "safe_mode_state.json"

LANGS = {
    "EN": "English",
    "ZH": "简体中文",
    "RU": "Русский",
    "PT_BR": "Português (BR)",
}

STRINGS = {
    "EN": {
        "window_title": "Stardew Valley - Safe Mode Loader",
        "mods_frame": "Mods Folder (SMAPI Mods)",
        "mods_browse": "Browse...",
        "game_frame": "Game / SMAPI Executable",
        "game_browse": "Browse...",
        "profiles_frame": "Profiles (Safe Setups)",
        "profile_label": "Profile:",
        "load_profile_btn": "Load Selection",
        "delete_profile_btn": "Delete",
        "save_profile_label": "Save current selection as:",
        "save_profile_btn": "Save Profile",
        "mods_list_frame": "Available Mods (check to keep enabled)",
        "select_all": "Select / Deselect All",
        "safe_mode_btn": 'Enable "Safe Mode" with Selected Mods',
        "restore_btn": "Restore All Mods",
        "launch_btn": "Launch Game in Current Mode",
        "refresh_btn": "Refresh Mod List",
        "status_ready": "Ready.",
        "status_no_mods": "No mods found in the selected Mods folder.",
        "status_found_mods": "Found {count} mod(s).",
        "status_normal": "Normal mode. All mods should be active.",
        "status_safe_mode_active": 'SAFE MODE ACTIVE ({profile}): {desc} enabled. Backup: {backup}',
        "status_safe_mode_active_short": "SAFE MODE ACTIVE. Backup: {backup}",
        "lang_label": "Language:",

        "msg_no_name_title": "No Name",
        "msg_no_name_body": "Please enter a name for the profile.",
        "msg_no_mods_selected_title": "No Mods Selected",
        "msg_no_mods_selected_profile_body": "Select one or more mods to save in the profile.",
        "msg_no_mods_selected_safe_body": "Please check one or more mods to keep enabled.",
        "msg_overwrite_profile_title": "Overwrite Profile",
        "msg_overwrite_profile_body": 'A profile named "{name}" already exists. Overwrite it?',
        "msg_profile_saved_title": "Profile Saved",
        "msg_profile_saved_body": 'Profile "{name}" saved ({count} mod(s)).',
        "msg_no_profile_selected_title": "No Profile Selected",
        "msg_no_profile_selected_body": "Please select a profile to load.",
        "msg_profile_not_found_title": "Error",
        "msg_profile_not_found_body": 'Profile "{name}" not found.',
        "msg_empty_profile_title": "Empty Profile",
        "msg_empty_profile_body": 'Profile "{name}" has no mods.',
        "msg_no_mods_listed_title": "No Mods Listed",
        "msg_no_mods_listed_body": "No mods found in the Mods folder.",
        "msg_missing_mods_title": "Some Mods Not Found",
        "msg_missing_mods_body": "These mods from the profile are not present in the Mods folder:\n\n{mods}",
        "msg_delete_profile_title": "Delete Profile",
        "msg_delete_profile_body": 'Are you sure you want to delete the profile "{name}"?',
        "msg_profile_deleted_title": "Profile Deleted",
        "msg_profile_deleted_body": 'Profile "{name}" has been deleted.',
        "msg_invalid_mods_path_title": "Error",
        "msg_invalid_mods_path_body": "Please select a valid Mods folder.",
        "msg_safe_already_active_title": "Safe Mode Already Active",
        "msg_safe_already_active_body": "Safe mode is already active.\n\n"
                                        "To apply a new safe setup, the previous one will be turned off "
                                        "and all mods will be restored first.\n\nContinue?",
        "msg_restore_failed_title": "Error",
        "msg_restore_failed_body": "Failed to restore previous safe mode; cannot continue.\n\n{details}",
        "msg_backup_create_failed_title": "Error",
        "msg_backup_create_failed_body": "Failed to create backup folder:\n{error}",
        "msg_move_failed_title": "Error",
        "msg_move_failed_body": "Failed to move some mods. Safe mode not activated.\n\n{errors}",
        "msg_safe_enabled_title": "Safe Mode Enabled",
        "msg_safe_enabled_body": "Safe mode ON ({profile}).\n"
                                 "Enabled mods: {count}\n"
                                 "Backup: {backup}",
        "msg_not_in_safe_title": "Not in Safe Mode",
        "msg_not_in_safe_body": "Safe mode is not currently active.",
        "msg_backup_missing_title": "Error",
        "msg_backup_missing_body": "Backup folder not found. Cannot restore mods.",
        "msg_restore_errors_title": "Restore Completed with Errors",
        "msg_restore_errors_body": "Some mods could not be restored:\n\n{errors}",
        "msg_restore_complete_title": "Restore Complete",
        "msg_restore_complete_body": "All mods have been restored. Safe mode is off.",
        "msg_game_exe_not_set_title": "Game Executable Not Set",
        "msg_game_exe_not_set_body": "Please select a valid game/SMAPI executable before launching.",
        "msg_game_launch_error_title": "Error",
        "msg_game_launch_error_body": "Failed to launch the game:\n{error}",
    },
    "ZH": {
        "window_title": "星露谷物语 - 安全模式加载器",
        "mods_frame": "Mods 文件夹（SMAPI 模组）",
        "mods_browse": "浏览...",
        "game_frame": "游戏 / SMAPI 可执行文件",
        "game_browse": "浏览...",
        "profiles_frame": "配置（安全组合）",
        "profile_label": "配置：",
        "load_profile_btn": "载入选择",
        "delete_profile_btn": "删除",
        "save_profile_label": "将当前选择保存为：",
        "save_profile_btn": "保存配置",
        "mods_list_frame": "可用模组（勾选保留启用）",
        "select_all": "全选 / 全不选",
        "safe_mode_btn": "用已选模组启用“安全模式”",
        "restore_btn": "还原所有模组",
        "launch_btn": "以当前模式启动游戏",
        "refresh_btn": "刷新模组列表",
        "status_ready": "就绪。",
        "status_no_mods": "在所选 Mods 文件夹中未找到模组。",
        "status_found_mods": "找到 {count} 个模组。",
        "status_normal": "普通模式。所有模组应已启用。",
        "status_safe_mode_active": "安全模式已开启（{profile}）：已启用 {desc}。备份：{backup}",
        "status_safe_mode_active_short": "安全模式已开启。备份：{backup}",
        "lang_label": "语言：",

        "msg_no_name_title": "缺少名称",
        "msg_no_name_body": "请输入配置名称。",
        "msg_no_mods_selected_title": "未选择模组",
        "msg_no_mods_selected_profile_body": "请选择一个或多个模组并保存到配置。",
        "msg_no_mods_selected_safe_body": "请选择要保留启用的一个或多个模组。",
        "msg_overwrite_profile_title": "覆盖配置",
        "msg_overwrite_profile_body": "名为“{name}”的配置已存在，是否覆盖？",
        "msg_profile_saved_title": "配置已保存",
        "msg_profile_saved_body": "配置“{name}”已保存（{count} 个模组）。",
        "msg_no_profile_selected_title": "未选择配置",
        "msg_no_profile_selected_body": "请选择要载入的配置。",
        "msg_profile_not_found_title": "错误",
        "msg_profile_not_found_body": "未找到配置“{name}”。",
        "msg_empty_profile_title": "空配置",
        "msg_empty_profile_body": "配置“{name}”中没有模组。",
        "msg_no_mods_listed_title": "无模组",
        "msg_no_mods_listed_body": "Mods 文件夹中没有模组。",
        "msg_missing_mods_title": "部分模组未找到",
        "msg_missing_mods_body": "以下配置中的模组在 Mods 文件夹中不存在：\n\n{mods}",
        "msg_delete_profile_title": "删除配置",
        "msg_delete_profile_body": "确定要删除配置“{name}”吗？",
        "msg_profile_deleted_title": "配置已删除",
        "msg_profile_deleted_body": "配置“{name}”已删除。",
        "msg_invalid_mods_path_title": "错误",
        "msg_invalid_mods_path_body": "请选择有效的 Mods 文件夹。",
        "msg_safe_already_active_title": "安全模式已开启",
        "msg_safe_already_active_body": "安全模式已经开启。\n\n要应用新的安全组合，将先关闭当前安全模式并还原所有模组。\n\n继续？",
        "msg_restore_failed_title": "错误",
        "msg_restore_failed_body": "无法还原上一次安全模式，无法继续。\n\n{details}",
        "msg_backup_create_failed_title": "错误",
        "msg_backup_create_failed_body": "创建备份文件夹失败：\n{error}",
        "msg_move_failed_title": "错误",
        "msg_move_failed_body": "移动部分模组失败，未启用安全模式。\n\n{errors}",
        "msg_safe_enabled_title": "安全模式已启用",
        "msg_safe_enabled_body": "安全模式已开启（{profile}）。\n"
                                 "已启用模组：{count}\n"
                                 "备份位置：{backup}",
        "msg_not_in_safe_title": "未处于安全模式",
        "msg_not_in_safe_body": "当前未启用安全模式。",
        "msg_backup_missing_title": "错误",
        "msg_backup_missing_body": "未找到备份文件夹，无法还原模组。",
        "msg_restore_errors_title": "还原完成但有错误",
        "msg_restore_errors_body": "部分模组无法还原：\n\n{errors}",
        "msg_restore_complete_title": "还原完成",
        "msg_restore_complete_body": "所有模组已还原，安全模式已关闭。",
        "msg_game_exe_not_set_title": "未设置可执行文件",
        "msg_game_exe_not_set_body": "请先选择有效的游戏 / SMAPI 可执行文件。",
        "msg_game_launch_error_title": "错误",
        "msg_game_launch_error_body": "启动游戏失败：\n{error}",
    },
    "RU": {
        "window_title": "Stardew Valley — загрузчик в безопасном режиме",
        "mods_frame": "Папка Mods (моды SMAPI)",
        "mods_browse": "Обзор...",
        "game_frame": "Исполняемый файл игры / SMAPI",
        "game_browse": "Обзор...",
        "profiles_frame": "Профили (наборы для отладки)",
        "profile_label": "Профиль:",
        "load_profile_btn": "Загрузить набор",
        "delete_profile_btn": "Удалить",
        "save_profile_label": "Сохранить текущий выбор как:",
        "save_profile_btn": "Сохранить профиль",
        "mods_list_frame": "Доступные моды (отметьте, чтобы оставить включёнными)",
        "select_all": "Выбрать / снять все",
        "safe_mode_btn": 'Включить "безопасный режим" с отмеченными модами',
        "restore_btn": "Вернуть все моды",
        "launch_btn": "Запустить игру в текущем режиме",
        "refresh_btn": "Обновить список модов",
        "status_ready": "Готово.",
        "status_no_mods": "В выбранной папке Mods моды не найдены.",
        "status_found_mods": "Найдено модов: {count}.",
        "status_normal": "Обычный режим. Все моды должны быть активны.",
        "status_safe_mode_active": "БЕЗОПАСНЫЙ РЕЖИМ ({profile}): включено {desc}. Резерв: {backup}",
        "status_safe_mode_active_short": "БЕЗОПАСНЫЙ РЕЖИМ. Резерв: {backup}",
        "lang_label": "Язык:",

        "msg_no_name_title": "Нет имени",
        "msg_no_name_body": "Введите имя профиля.",
        "msg_no_mods_selected_title": "Моды не выбраны",
        "msg_no_mods_selected_profile_body": "Выберите один или несколько модов для сохранения в профиль.",
        "msg_no_mods_selected_safe_body": "Отметьте один или несколько модов, которые нужно оставить включёнными.",
        "msg_overwrite_profile_title": "Перезаписать профиль",
        "msg_overwrite_profile_body": 'Профиль с именем «{name}» уже существует. Перезаписать его?',
        "msg_profile_saved_title": "Профиль сохранён",
        "msg_profile_saved_body": 'Профиль «{name}» сохранён ({count} мод(ов)).',
        "msg_no_profile_selected_title": "Профиль не выбран",
        "msg_no_profile_selected_body": "Выберите профиль для загрузки.",
        "msg_profile_not_found_title": "Ошибка",
        "msg_profile_not_found_body": 'Профиль «{name}» не найден.',
        "msg_empty_profile_title": "Пустой профиль",
        "msg_empty_profile_body": 'Профиль «{name}» не содержит модов.',
        "msg_no_mods_listed_title": "Нет модов",
        "msg_no_mods_listed_body": "В папке Mods нет модов.",
        "msg_missing_mods_title": "Некоторые моды не найдены",
        "msg_missing_mods_body": "Эти моды из профиля отсутствуют в папке Mods:\n\n{mods}",
        "msg_delete_profile_title": "Удалить профиль",
        "msg_delete_profile_body": 'Удалить профиль «{name}»?',
        "msg_profile_deleted_title": "Профиль удалён",
        "msg_profile_deleted_body": 'Профиль «{name}» удалён.',
        "msg_invalid_mods_path_title": "Ошибка",
        "msg_invalid_mods_path_body": "Выберите корректную папку Mods.",
        "msg_safe_already_active_title": "Безопасный режим уже включён",
        "msg_safe_already_active_body": "Безопасный режим уже активен.\n\n"
                                       "Чтобы применить новый набор, предыдущий будет отключён, "
                                       "а все моды будут восстановлены.\n\nПродолжить?",
        "msg_restore_failed_title": "Ошибка",
        "msg_restore_failed_body": "Не удалось восстановить предыдущий безопасный режим; продолжение невозможно.\n\n{details}",
        "msg_backup_create_failed_title": "Ошибка",
        "msg_backup_create_failed_body": "Не удалось создать папку для резервной копии:\n{error}",
        "msg_move_failed_title": "Ошибка",
        "msg_move_failed_body": "Не удалось переместить некоторые моды. Безопасный режим не включён.\n\n{errors}",
        "msg_safe_enabled_title": "Безопасный режим включён",
        "msg_safe_enabled_body": "Безопасный режим включён ({profile}).\n"
                                 "Включено модов: {count}\n"
                                 "Резерв: {backup}",
        "msg_not_in_safe_title": "Не в безопасном режиме",
        "msg_not_in_safe_body": "Безопасный режим сейчас не активен.",
        "msg_backup_missing_title": "Ошибка",
        "msg_backup_missing_body": "Папка резервной копии не найдена. Невозможно восстановить моды.",
        "msg_restore_errors_title": "Восстановление завершено с ошибками",
        "msg_restore_errors_body": "Некоторые моды не удалось восстановить:\n\n{errors}",
        "msg_restore_complete_title": "Восстановление завершено",
        "msg_restore_complete_body": "Все моды восстановлены. Безопасный режим выключен.",
        "msg_game_exe_not_set_title": "Файл игры не задан",
        "msg_game_exe_not_set_body": "Выберите корректный исполняемый файл игры / SMAPI.",
        "msg_game_launch_error_title": "Ошибка",
        "msg_game_launch_error_body": "Не удалось запустить игру:\n{error}",
    },
    "PT_BR": {
        "window_title": "Stardew Valley - Carregador em Modo Seguro",
        "mods_frame": "Pasta Mods (mods do SMAPI)",
        "mods_browse": "Procurar...",
        "game_frame": "Executável do jogo / SMAPI",
        "game_browse": "Procurar...",
        "profiles_frame": "Perfis (configurações seguras)",
        "profile_label": "Perfil:",
        "load_profile_btn": "Carregar seleção",
        "delete_profile_btn": "Excluir",
        "save_profile_label": "Salvar seleção atual como:",
        "save_profile_btn": "Salvar perfil",
        "mods_list_frame": "Mods disponíveis (marque para manter ativo)",
        "select_all": "Marcar / desmarcar todos",
        "safe_mode_btn": 'Ativar "Modo Seguro" com mods marcados',
        "restore_btn": "Restaurar todos os mods",
        "launch_btn": "Iniciar jogo no modo atual",
        "refresh_btn": "Atualizar lista de mods",
        "status_ready": "Pronto.",
        "status_no_mods": "Nenhum mod encontrado na pasta Mods selecionada.",
        "status_found_mods": "{count} mod(s) encontrado(s).",
        "status_normal": "Modo normal. Todos os mods devem estar ativos.",
        "status_safe_mode_active": "MODO SEGURO ATIVO ({profile}): {desc} ativo(s). Backup: {backup}",
        "status_safe_mode_active_short": "MODO SEGURO ATIVO. Backup: {backup}",
        "lang_label": "Idioma:",

        "msg_no_name_title": "Sem nome",
        "msg_no_name_body": "Digite um nome para o perfil.",
        "msg_no_mods_selected_title": "Nenhum mod selecionado",
        "msg_no_mods_selected_profile_body": "Selecione um ou mais mods para salvar no perfil.",
        "msg_no_mods_selected_safe_body": "Marque um ou mais mods para manter ativos.",
        "msg_overwrite_profile_title": "Sobrescrever perfil",
        "msg_overwrite_profile_body": 'Já existe um perfil chamado "{name}". Deseja sobrescrever?',
        "msg_profile_saved_title": "Perfil salvo",
        "msg_profile_saved_body": 'Perfil "{name}" salvo ({count} mod(s)).',
        "msg_no_profile_selected_title": "Nenhum perfil selecionado",
        "msg_no_profile_selected_body": "Selecione um perfil para carregar.",
        "msg_profile_not_found_title": "Erro",
        "msg_profile_not_found_body": 'Perfil "{name}" não encontrado.',
        "msg_empty_profile_title": "Perfil vazio",
        "msg_empty_profile_body": 'O perfil "{name}" não contém mods.',
        "msg_no_mods_listed_title": "Sem mods",
        "msg_no_mods_listed_body": "Nenhum mod na pasta Mods.",
        "msg_missing_mods_title": "Alguns mods não encontrados",
        "msg_missing_mods_body": "Estes mods do perfil não estão presentes na pasta Mods:\n\n{mods}",
        "msg_delete_profile_title": "Excluir perfil",
        "msg_delete_profile_body": 'Tem certeza de que deseja excluir o perfil "{name}"?',
        "msg_profile_deleted_title": "Perfil excluído",
        "msg_profile_deleted_body": 'Perfil "{name}" foi excluído.',
        "msg_invalid_mods_path_title": "Erro",
        "msg_invalid_mods_path_body": "Selecione uma pasta Mods válida.",
        "msg_safe_already_active_title": "Modo seguro já está ativo",
        "msg_safe_already_active_body": "O modo seguro já está ativo.\n\n"
                                        "Para aplicar uma nova configuração segura, o modo atual será desligado "
                                        "e todos os mods serão restaurados.\n\nContinuar?",
        "msg_restore_failed_title": "Erro",
        "msg_restore_failed_body": "Falha ao restaurar o modo seguro anterior; não é possível continuar.\n\n{details}",
        "msg_backup_create_failed_title": "Erro",
        "msg_backup_create_failed_body": "Falha ao criar pasta de backup:\n{error}",
        "msg_move_failed_title": "Erro",
        "msg_move_failed_body": "Falha ao mover alguns mods. Modo seguro não foi ativado.\n\n{errors}",
        "msg_safe_enabled_title": "Modo seguro ativado",
        "msg_safe_enabled_body": "Modo seguro LIGADO ({profile}).\n"
                                 "Mods ativos: {count}\n"
                                 "Backup: {backup}",
        "msg_not_in_safe_title": "Não está em modo seguro",
        "msg_not_in_safe_body": "O modo seguro não está ativo no momento.",
        "msg_backup_missing_title": "Erro",
        "msg_backup_missing_body": "Pasta de backup não encontrada. Não é possível restaurar mods.",
        "msg_restore_errors_title": "Restauração concluída com erros",
        "msg_restore_errors_body": "Alguns mods não puderam ser restaurados:\n\n{errors}",
        "msg_restore_complete_title": "Restauração concluída",
        "msg_restore_complete_body": "Todos os mods foram restaurados. Modo seguro desligado.",
        "msg_game_exe_not_set_title": "Executável do jogo não definido",
        "msg_game_exe_not_set_body": "Selecione um executável válido do jogo / SMAPI antes de iniciar.",
        "msg_game_launch_error_title": "Erro",
        "msg_game_launch_error_body": "Falha ao iniciar o jogo:\n{error}",
    },
}


def load_json(path, default=None):
    if default is None:
        default = {}
    try:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return default


def save_json(path, data):
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        # Fallback simple English error; localization here is overkill
        messagebox.showerror("Error", f"Failed to save {path}:\n{e}")


class SafeModeLoaderApp:
    def __init__(self, root):
        self.root = root

        self.config = load_json(CONFIG_FILE, {
            "mods_path": "",
            "game_exe": "",
            "profiles": {},
            "language": "EN",
        })
        self.state = load_json(STATE_FILE, {})
        self.profiles = self.config.get("profiles", {})
        self.lang_code = self.config.get("language", "EN")
        if self.lang_code not in STRINGS:
            self.lang_code = "EN"

        # will be filled later when language combobox created
        self.lang_var = None

        # mod_name -> BooleanVar
        self.mod_vars = {}

        # basic window setup (title updated in update_texts)
        self.root.title("Safe Mode Loader")
        self.root.configure(bg="white")

        self.create_widgets()
        self.refresh_profiles_ui()
        self.refresh_mod_list()
        self.update_status_from_state()
        self.update_texts()

        # Auto-fit: ensure the window is large enough for all widgets
        self.root.update_idletasks()
        self.root.minsize(self.root.winfo_reqwidth(), self.root.winfo_reqheight())

    # ---------- translation helper ----------

    def tr(self, key, **kwargs):
        lang_dict = STRINGS.get(self.lang_code, STRINGS["EN"])
        text = lang_dict.get(key, STRINGS["EN"].get(key, key))
        if kwargs:
            try:
                text = text.format(**kwargs)
            except Exception:
                pass
        return text

    # ---------- UI SETUP ----------

    def create_widgets(self):
        main_frame = ttk.Frame(self.root, padding=10)
        main_frame.pack(fill="both", expand=True)

        # language row (top right)
        lang_frame = ttk.Frame(main_frame)
        lang_frame.pack(fill="x", pady=(0, 5))

        self.lang_label = ttk.Label(lang_frame, text="Language:")
        self.lang_label.pack(side="right", padx=(5, 5))

        # combobox with human-readable names
        lang_names = [LANGS[code] for code in ["EN", "ZH", "RU", "PT_BR"]]
        current_name = LANGS.get(self.lang_code, LANGS["EN"])
        self.lang_var = tk.StringVar(value=current_name)
        self.lang_combo = ttk.Combobox(
            lang_frame,
            textvariable=self.lang_var,
            state="readonly",
            values=lang_names,
            width=18
        )
        self.lang_combo.pack(side="right")
        self.lang_combo.bind("<<ComboboxSelected>>", self.on_language_change)

        # Mods path
        self.mods_frame = ttk.LabelFrame(main_frame, text="")
        self.mods_frame.pack(fill="x", pady=(0, 10))

        self.mods_path_var = tk.StringVar(value=self.config.get("mods_path", ""))
        self.mods_entry = ttk.Entry(self.mods_frame, textvariable=self.mods_path_var)
        self.mods_entry.pack(side="left", fill="x", expand=True, padx=(5, 5), pady=5)

        self.mods_browse_btn = ttk.Button(self.mods_frame, text="", command=self.browse_mods_folder)
        self.mods_browse_btn.pack(side="right", padx=5, pady=5)

        # Game exe
        self.game_frame = ttk.LabelFrame(main_frame, text="")
        self.game_frame.pack(fill="x", pady=(0, 10))

        self.game_exe_var = tk.StringVar(value=self.config.get("game_exe", ""))
        self.game_entry = ttk.Entry(self.game_frame, textvariable=self.game_exe_var)
        self.game_entry.pack(side="left", fill="x", expand=True, padx=(5, 5), pady=5)

        self.game_browse_btn = ttk.Button(self.game_frame, text="", command=self.browse_game_exe)
        self.game_browse_btn.pack(side="right", padx=5, pady=5)

        # Profiles
        self.profile_frame = ttk.LabelFrame(main_frame, text="")
        self.profile_frame.pack(fill="x", pady=(0, 10))

        # Row 1: existing profiles
        top_profile_row = ttk.Frame(self.profile_frame)
        top_profile_row.pack(fill="x", pady=(5, 0))

        self.profile_label = ttk.Label(top_profile_row, text="")
        self.profile_label.pack(side="left", padx=(5, 5))

        self.profile_select_var = tk.StringVar()
        self.profile_combo = ttk.Combobox(
            top_profile_row,
            textvariable=self.profile_select_var,
            state="readonly",
            width=30
        )
        self.profile_combo.pack(side="left", padx=(0, 5), fill="x", expand=True)

        self.load_profile_btn = ttk.Button(
            top_profile_row,
            text="",
            command=self.load_profile_selection
        )
        self.load_profile_btn.pack(side="left", padx=3)

        self.delete_profile_btn = ttk.Button(
            top_profile_row,
            text="",
            command=self.delete_profile
        )
        self.delete_profile_btn.pack(side="left", padx=3)

        # Row 2: save new profile
        bottom_profile_row = ttk.Frame(self.profile_frame)
        bottom_profile_row.pack(fill="x", pady=(5, 5))

        self.save_profile_label = ttk.Label(bottom_profile_row, text="")
        self.save_profile_label.pack(side="left", padx=(5, 5))

        self.new_profile_name_var = tk.StringVar()
        self.new_profile_entry = ttk.Entry(
            bottom_profile_row,
            textvariable=self.new_profile_name_var,
            width=25
        )
        self.new_profile_entry.pack(side="left", padx=(0, 5), fill="x", expand=True)

        self.save_profile_btn = ttk.Button(
            bottom_profile_row,
            text="",
            command=self.save_current_selection_as_profile
        )
        self.save_profile_btn.pack(side="left", padx=3)

        # Mods list (checkboxes + select all)
        self.list_frame = ttk.LabelFrame(main_frame, text="")
        self.list_frame.pack(fill="both", expand=True, pady=(0, 10))

        # Select all row
        select_all_row = ttk.Frame(self.list_frame)
        select_all_row.pack(fill="x", padx=5, pady=(5, 0))

        self.select_all_var = tk.BooleanVar(value=False)
        self.select_all_chk = ttk.Checkbutton(
            select_all_row,
            text="",
            variable=self.select_all_var,
            command=self.toggle_select_all
        )
        self.select_all_chk.pack(side="left")

        # Scrollable checkbox area
        self.mods_canvas = tk.Canvas(self.list_frame, highlightthickness=0, background="white")
        self.mods_scrollbar = ttk.Scrollbar(self.list_frame, orient="vertical", command=self.mods_canvas.yview)
        self.mods_canvas.configure(yscrollcommand=self.mods_scrollbar.set)

        self.mods_canvas.pack(side="left", fill="both", expand=True, padx=(5, 0), pady=5)
        self.mods_scrollbar.pack(side="right", fill="y", padx=(0, 5), pady=5)

        self.mods_inner_frame = ttk.Frame(self.mods_canvas)
        self.mods_canvas_window = self.mods_canvas.create_window(
            (0, 0),
            window=self.mods_inner_frame,
            anchor="nw"
        )

        # Update scroll region when content changes
        self.mods_inner_frame.bind(
            "<Configure>",
            lambda event: self.mods_canvas.configure(scrollregion=self.mods_canvas.bbox("all"))
        )

        # Keep inner frame width synced with canvas width
        def _on_canvas_config(event):
            self.mods_canvas.itemconfig(self.mods_canvas_window, width=event.width)

        self.mods_canvas.bind("<Configure>", _on_canvas_config)

        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill="x", pady=(0, 10))

        self.safe_mode_btn = ttk.Button(
            button_frame,
            text="",
            command=self.enable_safe_mode
        )
        self.safe_mode_btn.pack(side="left", padx=5, pady=5)

        self.restore_btn = ttk.Button(
            button_frame,
            text="",
            command=self.restore_all_mods
        )
        self.restore_btn.pack(side="left", padx=5, pady=5)

        self.launch_btn = ttk.Button(
            button_frame,
            text="",
            command=self.launch_game
        )
        self.launch_btn.pack(side="right", padx=5, pady=5)

        # Bottom: refresh + status
        bottom_frame = ttk.Frame(main_frame)
        bottom_frame.pack(fill="x")

        self.refresh_btn = ttk.Button(
            bottom_frame,
            text="",
            command=self.refresh_mod_list
        )
        self.refresh_btn.pack(side="left", padx=5, pady=5)

        self.status_var = tk.StringVar(value="")
        self.status_label = ttk.Label(
            bottom_frame,
            textvariable=self.status_var,
            relief="sunken",
            anchor="w"
        )
        self.status_label.pack(side="left", fill="x", expand=True, padx=(10, 0), pady=5)

        # Save config on close
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    # ---------- language switching ----------

    def on_language_change(self, event=None):
        selected_name = self.lang_var.get()
        # find code by name
        for code, name in LANGS.items():
            if name == selected_name:
                self.lang_code = code
                break
        else:
            self.lang_code = "EN"
        self.update_texts()
        self.save_config()

    def update_texts(self):
        self.root.title(self.tr("window_title"))

        self.mods_frame.configure(text=self.tr("mods_frame"))
        self.mods_browse_btn.configure(text=self.tr("mods_browse"))

        self.game_frame.configure(text=self.tr("game_frame"))
        self.game_browse_btn.configure(text=self.tr("game_browse"))

        self.profile_frame.configure(text=self.tr("profiles_frame"))
        self.profile_label.configure(text=self.tr("profile_label"))
        self.load_profile_btn.configure(text=self.tr("load_profile_btn"))
        self.delete_profile_btn.configure(text=self.tr("delete_profile_btn"))
        self.save_profile_label.configure(text=self.tr("save_profile_label"))
        self.save_profile_btn.configure(text=self.tr("save_profile_btn"))

        self.list_frame.configure(text=self.tr("mods_list_frame"))
        self.select_all_chk.configure(text=self.tr("select_all"))

        self.safe_mode_btn.configure(text=self.tr("safe_mode_btn"))
        self.restore_btn.configure(text=self.tr("restore_btn"))
        self.launch_btn.configure(text=self.tr("launch_btn"))
        self.refresh_btn.configure(text=self.tr("refresh_btn"))
        self.lang_label.configure(text=self.tr("lang_label"))

        # status text: if it's empty, set default "Ready."
        if not self.status_var.get():
            self.status_var.set(self.tr("status_ready"))

    # ---------- PATH BROWSERS ----------

    def browse_mods_folder(self):
        folder = filedialog.askdirectory(title=self.tr("mods_frame"))
        if folder:
            self.mods_path_var.set(folder)
            self.config["mods_path"] = folder
            self.save_config()
            self.refresh_mod_list()

    def browse_game_exe(self):
        filetypes = [
            ("Executable", "*.exe"),
            ("All files", "*.*"),
        ]
        file = filedialog.askopenfilename(
            title=self.tr("game_frame"),
            filetypes=filetypes
        )
        if file:
            self.game_exe_var.set(file)
            self.config["game_exe"] = file
            self.save_config()

    # ---------- CONFIG / STATE / PROFILES ----------

    def save_config(self):
        self.config["mods_path"] = self.mods_path_var.get()
        self.config["game_exe"] = self.game_exe_var.get()
        self.config["profiles"] = self.profiles
        self.config["language"] = self.lang_code
        save_json(CONFIG_FILE, self.config)

    def save_state(self):
        save_json(STATE_FILE, self.state)

    def update_status_from_state(self):
        if self.state.get("mode") == "safe":
            backup_dir = self.state.get("backup_dir", "Unknown")
            mods = self.state.get("selected_mods")
            if not mods and self.state.get("selected_mod"):
                mods = [self.state.get("selected_mod")]
            profile = self.state.get("active_profile") or "Manual"

            if mods:
                if len(mods) <= 3:
                    mods_desc = ", ".join(mods)
                else:
                    mods_desc = f"{len(mods)} mods"
                self.status_var.set(
                    self.tr(
                        "status_safe_mode_active",
                        profile=profile,
                        desc=mods_desc,
                        backup=backup_dir
                    )
                )
            else:
                self.status_var.set(
                    self.tr(
                        "status_safe_mode_active_short",
                        backup=backup_dir
                    )
                )
        else:
            self.status_var.set(self.tr("status_normal"))

    def refresh_profiles_ui(self):
        names = sorted(self.profiles.keys())
        self.profile_combo["values"] = names
        current = self.profile_select_var.get()
        if current not in names:
            if names:
                self.profile_select_var.set(names[0])
            else:
                self.profile_select_var.set("")

    def get_selected_mods(self):
        return [name for name, var in self.mod_vars.items() if var.get()]

    def save_current_selection_as_profile(self):
        name = self.new_profile_name_var.get().strip()
        if not name:
            messagebox.showwarning(
                self.tr("msg_no_name_title"),
                self.tr("msg_no_name_body")
            )
            return

        selected_mods = self.get_selected_mods()
        if not selected_mods:
            messagebox.showwarning(
                self.tr("msg_no_mods_selected_title"),
                self.tr("msg_no_mods_selected_profile_body")
            )
            return

        if name in self.profiles:
            res = messagebox.askyesno(
                self.tr("msg_overwrite_profile_title"),
                self.tr("msg_overwrite_profile_body", name=name)
            )
            if not res:
                return

        self.profiles[name] = {"mods": selected_mods}
        self.save_config()
        self.refresh_profiles_ui()
        self.profile_select_var.set(name)
        messagebox.showinfo(
            self.tr("msg_profile_saved_title"),
            self.tr("msg_profile_saved_body", name=name, count=len(selected_mods))
        )

    def load_profile_selection(self):
        name = self.profile_select_var.get().strip()
        if not name:
            messagebox.showwarning(
                self.tr("msg_no_profile_selected_title"),
                self.tr("msg_no_profile_selected_body")
            )
            return

        data = self.profiles.get(name)
        if not data:
            messagebox.showerror(
                self.tr("msg_profile_not_found_title"),
                self.tr("msg_profile_not_found_body", name=name)
            )
            return

        mods_in_profile = set(data.get("mods", []))
        if not mods_in_profile:
            messagebox.showwarning(
                self.tr("msg_empty_profile_title"),
                self.tr("msg_empty_profile_body", name=name)
            )
            return

        if not self.mod_vars:
            messagebox.showwarning(
                self.tr("msg_no_mods_listed_title"),
                self.tr("msg_no_mods_listed_body")
            )
            return

        for mod_name, var in self.mod_vars.items():
            var.set(mod_name in mods_in_profile)

        available_mods = set(self.mod_vars.keys())
        missing = [m for m in mods_in_profile if m not in available_mods]

        self.update_select_all_from_mods()

        if missing:
            messagebox.showwarning(
                self.tr("msg_missing_mods_title"),
                self.tr("msg_missing_mods_body", mods="\n".join(missing))
            )

    def delete_profile(self):
        name = self.profile_select_var.get().strip()
        if not name:
            messagebox.showwarning(
                self.tr("msg_no_profile_selected_title"),
                self.tr("msg_no_profile_selected_body")
            )
            return

        if name not in self.profiles:
            messagebox.showerror(
                self.tr("msg_profile_not_found_title"),
                self.tr("msg_profile_not_found_body", name=name)
            )
            return

        res = messagebox.askyesno(
            self.tr("msg_delete_profile_title"),
            self.tr("msg_delete_profile_body", name=name)
        )
        if not res:
            return

        del self.profiles[name]
        self.save_config()
        self.refresh_profiles_ui()
        messagebox.showinfo(
            self.tr("msg_profile_deleted_title"),
            self.tr("msg_profile_deleted_body", name=name)
        )

    # ---------- MOD LIST ----------

    def get_mods_list(self):
        mods_path = self.mods_path_var.get().strip()
        if not mods_path or not os.path.isdir(mods_path):
            return []
        try:
            entries = os.listdir(mods_path)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to read Mods folder:\n{e}")
            return []

        mods = []
        for entry in entries:
            full = os.path.join(mods_path, entry)
            if os.path.isdir(full):
                mods.append(entry)
        return sorted(mods, key=str.lower)

    def refresh_mod_list(self):
        # Clear existing checkboxes
        for child in self.mods_inner_frame.winfo_children():
            child.destroy()
        self.mod_vars.clear()

        mods = self.get_mods_list()
        if not mods:
            self.status_var.set(self.tr("status_no_mods"))
            self.select_all_var.set(False)
            return

        for mod_name in mods:
            var = tk.BooleanVar(value=False)
            cb = ttk.Checkbutton(
                self.mods_inner_frame,
                text=mod_name,
                variable=var,
                command=self.on_mod_checkbox_changed
            )
            cb.pack(anchor="w", padx=5, pady=1)
            self.mod_vars[mod_name] = var

        self.status_var.set(self.tr("status_found_mods", count=len(mods)))
        self.update_select_all_from_mods()

    def toggle_select_all(self):
        value = self.select_all_var.get()
        for var in self.mod_vars.values():
            var.set(value)

    def update_select_all_from_mods(self):
        if not self.mod_vars:
            self.select_all_var.set(False)
            return
        values = [var.get() for var in self.mod_vars.values()]
        self.select_all_var.set(all(values))

    def on_mod_checkbox_changed(self):
        self.update_select_all_from_mods()

    # ---------- SAFE MODE LOGIC ----------

    def enable_safe_mode(self):
        mods_path = self.mods_path_var.get().strip()
        if not mods_path or not os.path.isdir(mods_path):
            messagebox.showerror(
                self.tr("msg_invalid_mods_path_title"),
                self.tr("msg_invalid_mods_path_body")
            )
            return

        selected_mods = self.get_selected_mods()
        if not selected_mods:
            messagebox.showwarning(
                self.tr("msg_no_mods_selected_title"),
                self.tr("msg_no_mods_selected_safe_body")
            )
            return

        # If safe mode already active, restore first
        if self.state.get("mode") == "safe":
            res = messagebox.askyesno(
                self.tr("msg_safe_already_active_title"),
                self.tr("msg_safe_already_active_body")
            )
            if not res:
                return

            success, errors = self._restore_all_mods_internal(show_messages=False)
            if not success:
                messagebox.showerror(
                    self.tr("msg_restore_failed_title"),
                    self.tr("msg_restore_failed_body", details="\n".join(errors))
                )
                return

        parent_dir = os.path.dirname(mods_path.rstrip(os.sep))
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir_name = f"Mods_backup_safe_mode_{timestamp}"
        backup_dir = os.path.join(parent_dir, backup_dir_name)

        try:
            os.makedirs(backup_dir, exist_ok=False)
        except FileExistsError:
            backup_dir += "_extra"
            os.makedirs(backup_dir, exist_ok=False)
        except Exception as e:
            messagebox.showerror(
                self.tr("msg_backup_create_failed_title"),
                self.tr("msg_backup_create_failed_body", error=e)
            )
            return

        moved_mods = []
        errors = []
        selected_set = set(selected_mods)

        for mod_folder in self.get_mods_list():
            full_mod_path = os.path.join(mods_path, mod_folder)
            if mod_folder in selected_set:
                continue
            try:
                shutil.move(full_mod_path, os.path.join(backup_dir, mod_folder))
                moved_mods.append(mod_folder)
            except Exception as e:
                errors.append(f"{mod_folder}: {e}")

        if errors:
            for mod_folder in moved_mods:
                src = os.path.join(backup_dir, mod_folder)
                dst = os.path.join(mods_path, mod_folder)
                if os.path.exists(src):
                    try:
                        shutil.move(src, dst)
                    except Exception:
                        pass
            try:
                if not os.listdir(backup_dir):
                    os.rmdir(backup_dir)
            except Exception:
                pass
            messagebox.showerror(
                self.tr("msg_move_failed_title"),
                self.tr("msg_move_failed_body", errors="\n".join(errors))
            )
            return

        active_profile = self.profile_select_var.get().strip() or None
        self.state = {
            "mode": "safe",
            "selected_mods": selected_mods,
            "backup_dir": backup_dir,
            "mods_path": mods_path,
            "active_profile": active_profile,
        }
        self.save_state()
        self.refresh_mod_list()
        self.update_status_from_state()

        count = len(selected_mods)
        profile_label = active_profile if active_profile else "Manual"
        # short confirmation popup
        messagebox.showinfo(
            self.tr("msg_safe_enabled_title"),
            self.tr(
                "msg_safe_enabled_body",
                profile=profile_label,
                count=count,
                backup=backup_dir
            )
        )

    def _restore_all_mods_internal(self, show_messages=True):
        if self.state.get("mode") != "safe":
            if show_messages:
                messagebox.showinfo(
                    self.tr("msg_not_in_safe_title"),
                    self.tr("msg_not_in_safe_body")
                )
            return False, []

        mods_path = self.mods_path_var.get().strip()
        backup_dir = self.state.get("backup_dir")

        if not backup_dir or not os.path.isdir(backup_dir):
            if show_messages:
                messagebox.showerror(
                    self.tr("msg_backup_missing_title"),
                    self.tr("msg_backup_missing_body")
                )
            return False, ["Backup folder not found."]

        errors = []
        for entry in os.listdir(backup_dir):
            src = os.path.join(backup_dir, entry)
            dst = os.path.join(mods_path, entry)
            try:
                shutil.move(src, dst)
            except Exception as e:
                errors.append(f"{entry}: {e}")

        try:
            if not os.listdir(backup_dir):
                os.rmdir(backup_dir)
        except Exception:
            pass

        self.state = {}
        self.save_state()
        self.refresh_mod_list()
        self.update_status_from_state()

        if show_messages:
            if errors:
                messagebox.showwarning(
                    self.tr("msg_restore_errors_title"),
                    self.tr("msg_restore_errors_body", errors="\n".join(errors))
                )
            else:
                messagebox.showinfo(
                    self.tr("msg_restore_complete_title"),
                    self.tr("msg_restore_complete_body")
                )

        return len(errors) == 0, errors

    def restore_all_mods(self):
        self._restore_all_mods_internal(show_messages=True)

    # ---------- LAUNCH GAME ----------

    def launch_game(self):
        game_exe = self.game_exe_var.get().strip()
        if not game_exe or not os.path.isfile(game_exe):
            messagebox.showerror(
                self.tr("msg_game_exe_not_set_title"),
                self.tr("msg_game_exe_not_set_body")
            )
            return

        try:
            subprocess.Popen([game_exe], cwd=os.path.dirname(game_exe))
            # keep existing status text
        except Exception as e:
            messagebox.showerror(
                self.tr("msg_game_launch_error_title"),
                self.tr("msg_game_launch_error_body", error=e)
            )

    # ---------- CLEANUP ----------

    def on_close(self):
        self.save_config()
        self.root.destroy()


def main():
    root = tk.Tk()
    try:
        style = ttk.Style()
        if "clam" in style.theme_names():
            style.theme_use("clam")
        # make ttk background white-ish
        style.configure("TFrame", background="white")
        style.configure("TLabelFrame", background="white")
        style.configure("TLabel", background="white")
        style.configure("TCheckbutton", background="white")
    except Exception:
        pass

    root.configure(bg="white")

    app = SafeModeLoaderApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
