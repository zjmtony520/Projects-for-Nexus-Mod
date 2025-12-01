import json
import os
import re
import tkinter as tk
from tkinter import filedialog, messagebox, ttk


def log_message(log_widget, message):
    """在日志区域追加消息 (Append message to log area)."""
    log_widget.configure(state="normal")
    log_widget.insert("end", message + "\n")
    log_widget.see("end")
    log_widget.configure(state="disabled")


def select_json_file(initial_dir=".", title="Select JSON File (选择 JSON 文件)"):
    """打开文件选择对话框，返回 JSON 文件路径 (Open file dialog and return selected JSON file path)."""
    path = filedialog.askopenfilename(
        initialdir=initial_dir,
        title=title,
        filetypes=[("JSON files (JSON 文件)", "*.json"), ("All files (所有文件)", "*.*")]
    )
    return path or None


def strip_json_comments(text):
    """
    删除字符串外的 // 行尾注释 (Strip // end-of-line comments outside of strings).

    只处理 // 风格注释，不动 /* */，避免误伤内容。
    This only strips // comments, not /* */, to avoid breaking content.
    """
    result_lines = []
    for line in text.splitlines():
        new_line_chars = []
        in_string = False
        escape = False
        i = 0
        while i < len(line):
            ch = line[i]

            if ch == '"' and not escape:
                # 进入或离开字符串 (enter or leave string)
                in_string = not in_string
                new_line_chars.append(ch)
            elif not in_string and ch == "/" and i + 1 < len(line) and line[i + 1] == "/":
                # 字符串外且遇到 //，后面整行丢弃 (outside string and see // → drop rest of line)
                break
            else:
                new_line_chars.append(ch)

            # 处理转义符 (handle escape character)
            if ch == "\\" and not escape:
                escape = True
            else:
                escape = False

            i += 1

        result_lines.append("".join(new_line_chars))
    return "\n".join(result_lines)


def strip_trailing_commas(text):
    """
    删除字符串外、紧挨 } 或 ] 之前的多余逗号 (Strip trailing commas before } or ] outside strings).

    示例:
      {"a":1,}   -> {"a":1}
      [1,2,]     -> [1,2]
    """
    result_chars = []
    in_string = False
    escape = False
    i = 0
    length = len(text)

    while i < length:
        ch = text[i]

        if ch == '"' and not escape:
            in_string = not in_string
            result_chars.append(ch)
        elif not in_string and ch == ",":
            # Look ahead for whitespace + } or ]
            j = i + 1
            while j < length and text[j] in " \t\r\n":
                j += 1
            if j < length and text[j] in "}]":
                # skip this extra comma (忽略多余逗号)
                i += 1
                continue
            else:
                result_chars.append(ch)
        else:
            result_chars.append(ch)

        # 转义处理 (escape handling)
        if ch == "\\" and not escape:
            escape = True
        else:
            escape = False

        i += 1

    return "".join(result_chars)


def load_json_file(path):
    """加载 JSON 文件并返回其内容 (Load JSON file and return its content)."""
    with open(path, "r", encoding="utf-8-sig") as f:
        raw = f.read()

    # 去掉 // 注释 + 末尾逗号 (strip comments + trailing commas)
    cleaned = strip_json_comments(raw)
    cleaned = strip_trailing_commas(cleaned)

    return json.loads(cleaned)


def flatten_dict(d, parent_key="", sep="."):
    """将嵌套字典拍平成一层字典 (Flatten nested dict into a single-level dict)."""
    items = {}
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.update(flatten_dict(v, new_key, sep=sep))
        else:
            items[new_key] = v
    return items


TOKEN_PATTERN = re.compile(r'(\{\{[^}]+\}\}|\{[0-9]+\})')


def extract_tokens(text):
    """提取文本中的占位符标记 (Extract placeholder tokens from text)."""
    if not isinstance(text, str):
        return set()
    return set(TOKEN_PATTERN.findall(text))


class LocalizationHelperFrame(ttk.Frame):
    """翻译版对比最新英文默认版工具界面 (Translated vs latest default English tool UI)."""

    def __init__(self, master, log_widget, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.log_widget = log_widget
        self.english_path = None
        self.translated_path = None
        self.english_data = {}
        self.translated_data = {}
        self.missing_keys = {}
        self.extra_keys = {}
        self.token_mismatches = {}

        self._build_ui()

    def _build_ui(self):
        # 文件选择区域 (File selection area)
        file_frame = ttk.LabelFrame(
            self,
            text="Translated Version compare to latest Default English Version Tool (翻译版对比最新英文默认版工具)"
        )
        file_frame.pack(fill="x", padx=8, pady=8)

        # 导入 1：最新英文默认版 (Import 1: latest English default)
        btn_eng = ttk.Button(
            file_frame,
            text="Latest English Default.json (最新英文默认版 JSON)",
            command=self.load_english_file
        )
        btn_eng.grid(row=0, column=0, padx=4, pady=4, sticky="w")

        self.eng_label = ttk.Label(
            file_frame,
            text="No English default file selected (尚未选择英文默认版文件)"
        )
        self.eng_label.grid(row=0, column=1, padx=4, pady=4, sticky="w")

        # 导入 2：旧翻译版 (Import 2: old translated)
        btn_tr = ttk.Button(
            file_frame,
            text="Your Old Translated JSON (你之前的旧翻译 JSON)",
            command=self.load_translated_file
        )
        btn_tr.grid(row=1, column=0, padx=4, pady=4, sticky="w")

        self.tr_label = ttk.Label(
            file_frame,
            text="No old translated file selected (尚未选择旧翻译文件)"
        )
        self.tr_label.grid(row=1, column=1, padx=4, pady=4, sticky="w")

        # 操作按钮 (Action buttons)
        action_frame = ttk.Frame(self)
        action_frame.pack(fill="x", padx=8, pady=4)

        compare_btn = ttk.Button(
            action_frame,
            text="Compare Files (比对文件)",
            command=self.compare_files
        )
        compare_btn.pack(side="left", padx=4)

        export_btn = ttk.Button(
            action_frame,
            text="Export To-Translate List (导出待翻译列表)",
            command=self.export_to_translate
        )
        export_btn.pack(side="left", padx=4)

        # 结果概览 (Result summary)
        summary_frame = ttk.LabelFrame(self, text="Summary (结果概览)")
        summary_frame.pack(fill="x", padx=8, pady=8)

        self.summary_missing = ttk.Label(
            summary_frame,
            text="Missing keys: 0 (缺少键：0)"
        )
        self.summary_missing.grid(row=0, column=0, padx=4, pady=2, sticky="w")

        self.summary_extra = ttk.Label(
            summary_frame,
            text="Extra keys: 0 (多余键：0)"
        )
        self.summary_extra.grid(row=1, column=0, padx=4, pady=2, sticky="w")

        self.summary_tokens = ttk.Label(
            summary_frame,
            text="Token mismatches: 0 (占位符不匹配：0)"
        )
        self.summary_tokens.grid(row=2, column=0, padx=4, pady=2, sticky="w")

    # ---- JSON loading helpers -------------------------------------------------

    def _validate_top_level_dict(self, data, role_text):
        """确保顶层是对象 { } (Ensure top-level JSON is an object {})."""
        if not isinstance(data, dict):
            raise ValueError(
                f"{role_text} must be a JSON object at the top level (顶层 {role_text} 必须是一个 JSON 对象 {{ }}。)"
            )

    def load_english_file(self):
        path = select_json_file(title="Select latest English default JSON (选择最新英文默认版 JSON 文件)")
        if not path:
            return
        try:
            data = load_json_file(path)
            self._validate_top_level_dict(data, "English JSON (英文 JSON)")
            flat = flatten_dict(data)
        except Exception as e:
            log_message(self.log_widget, f"[Error 错误] Failed to load English JSON (加载英文 JSON 失败): {e}")
            messagebox.showerror("Error (错误)", f"Failed to load English JSON (加载英文 JSON 失败):\n{e}")
            return
        self.english_path = path
        self.english_data = flat
        self.eng_label.config(text=f"English default: {os.path.basename(path)} (英文默认版已加载)")
        log_message(
            self.log_widget,
            f"[Info 信息] English default JSON loaded (英文默认版 JSON 已加载): {path} "
            f"(flattened keys: {len(self.english_data)} 个键)"
        )

    def load_translated_file(self):
        path = select_json_file(title="Select your old translated JSON (选择你之前的旧翻译 JSON 文件)")
        if not path:
            return
        try:
            data = load_json_file(path)
            self._validate_top_level_dict(data, "Translated JSON (翻译 JSON)")
            flat = flatten_dict(data)
        except Exception as e:
            log_message(self.log_widget, f"[Error 错误] Failed to load translated JSON (加载翻译 JSON 失败): {e}")
            messagebox.showerror("Error (错误)", f"Failed to load translated JSON (加载翻译 JSON 失败):\n{e}")
            return
        self.translated_path = path
        self.translated_data = flat
        self.tr_label.config(text=f"Old translated: {os.path.basename(path)} (旧翻译已加载)")
        log_message(
            self.log_widget,
            f"[Info 信息] Old translated JSON loaded (旧翻译 JSON 已加载): {path} "
            f"(flattened keys: {len(self.translated_data)} 个键)"
        )

    # ---- Comparison & export --------------------------------------------------

    def compare_files(self):
        """比对键与占位符 (Compare keys and tokens)."""
        if not self.english_data:
            messagebox.showwarning(
                "Warning (警告)",
                "Please load latest English default JSON first. (请先加载最新英文默认版 JSON。)"
            )
            return
        if not self.translated_data:
            messagebox.showwarning(
                "Warning (警告)",
                "Please load your old translated JSON first. (请先加载你的旧翻译 JSON。)"
            )
            return

        eng_keys = set(self.english_data.keys())
        tr_keys = set(self.translated_data.keys())

        missing = eng_keys - tr_keys
        extra = tr_keys - eng_keys

        self.missing_keys = {k: self.english_data[k] for k in sorted(missing)}
        self.extra_keys = {k: self.translated_data[k] for k in sorted(extra)}

        # 检查占位符 (Check tokens)
        mismatches = {}
        for key in eng_keys & tr_keys:
            eng_tokens = extract_tokens(self.english_data.get(key, ""))
            tr_tokens = extract_tokens(self.translated_data.get(key, ""))
            if eng_tokens != tr_tokens:
                mismatches[key] = {
                    "english": self.english_data.get(key, ""),
                    "translated": self.translated_data.get(key, ""),
                    "eng_tokens": sorted(eng_tokens),
                    "tr_tokens": sorted(tr_tokens),
                }
        self.token_mismatches = mismatches

        self.summary_missing.config(
            text=f"Missing keys: {len(self.missing_keys)} (缺少键：{len(self.missing_keys)})"
        )
        self.summary_extra.config(
            text=f"Extra keys: {len(self.extra_keys)} (多余键：{len(self.extra_keys)})"
        )
        self.summary_tokens.config(
            text=f"Token mismatches: {len(self.token_mismatches)} (占位符不匹配：{len(self.token_mismatches)})"
        )

        log_message(self.log_widget, "[Info 信息] Comparison finished. (比对完成。)")
        log_message(self.log_widget, f"  Missing keys (缺少键): {len(self.missing_keys)}")
        log_message(self.log_widget, f"  Extra keys (多余键): {len(self.extra_keys)}")
        log_message(self.log_widget, f"  Token mismatches (占位符不匹配): {len(self.token_mismatches)}")

    def export_to_translate(self):
        """导出待翻译列表与问题报告 (Export to-translate list and issues)."""
        if not self.missing_keys and not self.token_mismatches and not self.extra_keys:
            messagebox.showinfo(
                "Info (提示)",
                "No missing, extra, or token-mismatch keys to export. (没有可导出的缺少键、多余键或占位符问题。)"
            )
            return

        export_path = filedialog.asksaveasfilename(
            title="Save To-Translate List (保存待翻译列表)",
            defaultextension=".json",
            filetypes=[
                ("JSON files (JSON 文件)", "*.json"),
                ("Text files (文本文件)", "*.txt"),
                ("All files (所有文件)", "*.*"),
            ]
        )
        if not export_path:
            return

        try:
            export_data = {
                "missing_keys": [
                    {"key": k, "english": self.missing_keys[k]}
                    for k in sorted(self.missing_keys.keys())
                ],
                "token_mismatches": [
                    {
                        "key": k,
                        "english": v["english"],
                        "translated": v["translated"],
                        "eng_tokens": v["eng_tokens"],
                        "tr_tokens": v["tr_tokens"],
                    }
                    for k, v in sorted(self.token_mismatches.items())
                ],
                "extra_keys": [
                    {"key": k, "translated": self.extra_keys[k]}
                    for k in sorted(self.extra_keys.keys())
                ],
            }

            if export_path.lower().endswith(".txt"):
                with open(export_path, "w", encoding="utf-8") as f:
                    f.write("# To Translate / Report (待翻译与问题报告)\n\n")

                    f.write("## Missing keys (缺少键)\n")
                    for item in export_data["missing_keys"]:
                        f.write(f"{item['key']}: {item['english']}\n")

                    f.write("\n## Token mismatches (占位符不匹配)\n")
                    for item in export_data["token_mismatches"]:
                        f.write(f"{item['key']}:\n")
                        f.write(f"  EN: {item['english']}\n")
                        f.write(f"  TR: {item['translated']}\n")
                        f.write(f"  EN tokens: {', '.join(item['eng_tokens'])}\n")
                        f.write(f"  TR tokens: {', '.join(item['tr_tokens'])}\n")

                    f.write("\n## Extra / unused keys (多余 / 未使用键)\n")
                    for item in export_data["extra_keys"]:
                        f.write(f"{item['key']}: {item['translated']}\n")
            else:
                with open(export_path, "w", encoding="utf-8") as f:
                    json.dump(export_data, f, ensure_ascii=False, indent=2)

            log_message(self.log_widget, f"[Info 信息] Exported to-translate list. (待翻译列表已导出): {export_path}")
            messagebox.showinfo("Success (成功)", "To-translate list exported. (待翻译列表已导出。)")
        except Exception as e:
            log_message(self.log_widget, f"[Error 错误] Failed to export to-translate list (导出待翻译列表失败): {e}")
            messagebox.showerror("Error (错误)", f"Failed to export to-translate list (导出待翻译列表失败):\n{e}")


class MainApplication(tk.Tk):
    """星露谷翻译版对比工具主窗口 (Main window for translated vs English default tool)."""

    def __init__(self):
        super().__init__()
        self.title("Translated vs Latest Default English Tool (翻译版对比最新英文默认版工具)")
        self.geometry("900x600")

        # 主布局 (Main layout)
        main_pane = ttk.PanedWindow(self, orient=tk.VERTICAL)
        main_pane.pack(fill="both", expand=True)

        # 上方工具区域 (Top area)
        top_frame = ttk.Frame(main_pane)
        main_pane.add(top_frame, weight=3)

        # 下方日志区域 (Bottom log area)
        log_frame = ttk.LabelFrame(main_pane, text="Log / Errors (日志 / 错误)")
        main_pane.add(log_frame, weight=1)

        # 日志文本框 (Log text widget)
        log_text = tk.Text(log_frame, height=8, state="disabled")
        log_scroll = ttk.Scrollbar(log_frame, command=log_text.yview)
        log_text.configure(yscrollcommand=log_scroll.set)
        log_text.pack(side="left", fill="both", expand=True)
        log_scroll.pack(side="right", fill="y")

        # 工具页 (Tool frame)
        helper = LocalizationHelperFrame(top_frame, log_text)
        helper.pack(fill="both", expand=True, padx=4, pady=4)

        log_message(
            log_text,
            "Translated vs latest default English tool started. (翻译版对比最新英文默认版工具已启动。)"
        )


if __name__ == "__main__":
    app = MainApplication()
    app.mainloop()
