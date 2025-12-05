import os
import json
import tkinter as tk
from tkinter import ttk, filedialog, messagebox


class EmptyStardewModScaffolder(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Stardew Mod Scaffolder - Empty manifest + i18n")
        # Taller window so buttons are definitely visible
        self.geometry("650x320")
        # Let user resize both ways in case of scaling
        self.resizable(True, True)

        self.mod_folder_path = tk.StringVar()
        self.create_assets_folder = tk.BooleanVar(value=True)

        self._build_ui()

    def _build_ui(self):
        main = ttk.Frame(self, padding=10)
        main.pack(fill="both", expand=True)

        # ---------- Title / description ----------
        ttk.Label(
            main,
            text="Create empty manifest.json and i18n/default.json",
            font=("Segoe UI", 11, "bold")
        ).pack(anchor="w", pady=(0, 6))

        ttk.Label(
            main,
            text=(
                "This tool will create in the selected folder:\n"
                " • manifest.json      -> {}\n"
                " • i18n/default.json  -> {}"
            ),
            justify="left"
        ).pack(anchor="w", pady=(0, 10))

        # ---------- Folder selection ----------
        folder_frame = ttk.LabelFrame(main, text="Mod Folder Location")
        folder_frame.pack(fill="x", pady=(0, 8))

        ttk.Label(folder_frame, text="Mod folder (will be created if missing):").grid(
            row=0, column=0, padx=5, pady=5, sticky="w"
        )

        ttk.Entry(folder_frame, textvariable=self.mod_folder_path, width=55).grid(
            row=1, column=0, padx=5, pady=5, sticky="w"
        )

        ttk.Button(folder_frame, text="Browse...", command=self._browse_folder).grid(
            row=1, column=1, padx=5, pady=5
        )

        # ---------- Optional folders ----------
        optional_frame = ttk.LabelFrame(main, text="Optional Folders")
        optional_frame.pack(fill="x", pady=(0, 8))

        ttk.Checkbutton(
            optional_frame,
            text='Create "assets" folder (for sprites / data / etc.)',
            variable=self.create_assets_folder
        ).grid(row=0, column=0, padx=5, pady=5, sticky="w")

        # ---------- Bottom buttons (Create / Quit) ----------
        button_frame = ttk.Frame(main)
        button_frame.pack(fill="x", pady=(15, 0))

        # Spacer on left so buttons are clearly on the right
        ttk.Label(button_frame, text="").pack(side="left", expand=True)

        ttk.Button(button_frame, text="Quit", command=self.destroy).pack(
            side="right", padx=5
        )
        ttk.Button(button_frame, text="Create Files", command=self._create_files).pack(
            side="right", padx=5
        )

    # ---------- Handlers ----------
    def _browse_folder(self):
        folder = filedialog.askdirectory(title="Select or create your mod folder")
        if folder:
            self.mod_folder_path.set(folder)

    def _validate(self):
        if not self.mod_folder_path.get():
            messagebox.showerror("Missing folder", "Please choose your mod folder path.")
            return False
        return True

    def _create_files(self):
        if not self._validate():
            return

        folder = self.mod_folder_path.get()

        try:
            os.makedirs(folder, exist_ok=True)
            created_paths = []

            # manifest.json => {}
            manifest_path = os.path.join(folder, "manifest.json")
            with open(manifest_path, "w", encoding="utf-8") as f:
                json.dump({}, f, indent=2, ensure_ascii=False)
            created_paths.append(manifest_path)

            # i18n/default.json => {}
            i18n_folder = os.path.join(folder, "i18n")
            os.makedirs(i18n_folder, exist_ok=True)

            default_path = os.path.join(i18n_folder, "default.json")
            with open(default_path, "w", encoding="utf-8") as f:
                json.dump({}, f, indent=2, ensure_ascii=False)
            created_paths.append(default_path)

            # Optional assets folder
            if self.create_assets_folder.get():
                assets_folder = os.path.join(folder, "assets")
                os.makedirs(assets_folder, exist_ok=True)
                created_paths.append(assets_folder + os.sep)

            messagebox.showinfo(
                "Success",
                "Created:\n\n" + "\n".join(created_paths) +
                "\n\nmanifest.json and default.json both contain empty JSON: {}"
            )
        except Exception as exc:
            messagebox.showerror("Error", f"Something went wrong while creating files:\n{exc}")


if __name__ == "__main__":
    app = EmptyStardewModScaffolder()
    app.mainloop()
