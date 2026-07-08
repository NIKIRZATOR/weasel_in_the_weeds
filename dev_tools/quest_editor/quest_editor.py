import json
import tkinter as tk
from copy import deepcopy
from pathlib import Path
from tkinter import messagebox, ttk


PROJECT_DIR = Path(__file__).resolve().parents[2]
LEVELS_DIR = PROJECT_DIR / "levels"
QUESTS_FILE_NAME = "quests.json"

OBJECTIVE_KINDS = [
    "event",
    "flag",
    "item",
]


class QuestEditor(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Редактор квестов")
        self.geometry("1500x920")
        self.minsize(1260, 780)

        self.level_keys = self._discover_level_keys()
        self.level_quests = self._load_all_level_quests()
        self.current_quest_id = None
        self.current_objective_index = None
        self.current_objectives = []
        self.status_var = tk.StringVar(value="Готово")

        self._init_vars()
        self._build_ui()
        self._refresh_quest_list()
        self._new_quest()

    def _init_vars(self):
        default_level = self.level_keys[0] if self.level_keys else "level_01"
        self.quest_id_var = tk.StringVar()
        self.level_key_var = tk.StringVar(value=default_level)
        self.title_key_var = tk.StringVar()
        self.description_key_var = tk.StringVar()
        self.category_var = tk.StringVar(value="main")
        self.sort_order_var = tk.StringVar(value="0")
        self.activation_dialogue_file_var = tk.StringVar()

        self.objective_id_var = tk.StringVar()
        self.objective_kind_var = tk.StringVar(value=OBJECTIVE_KINDS[0])
        self.objective_text_key_var = tk.StringVar()
        self.objective_target_var = tk.StringVar()
        self.objective_required_var = tk.StringVar(value="1")
        self.objective_legacy_flag_var = tk.StringVar()

    def _build_ui(self):
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        toolbar = ttk.Frame(self, padding=8)
        toolbar.grid(row=0, column=0, sticky="ew")
        toolbar.columnconfigure(2, weight=1)
        ttk.Button(toolbar, text="Сохранить все", command=self._save_all).grid(row=0, column=0, padx=2)
        ttk.Button(toolbar, text="Применить текущий", command=self._apply_quest).grid(row=0, column=1, padx=2)
        ttk.Label(toolbar, textvariable=self.status_var).grid(row=0, column=2, sticky="e")

        root = ttk.Frame(self, padding=8)
        root.grid(row=1, column=0, sticky="nsew")
        root.columnconfigure(1, weight=1)
        root.rowconfigure(0, weight=1)

        left = ttk.Frame(root)
        left.grid(row=0, column=0, sticky="ns", padx=(0, 8))
        left.rowconfigure(1, weight=1)

        ttk.Label(left, text="Квесты").grid(row=0, column=0, sticky="w")
        self.quest_list = tk.Listbox(left, width=40, exportselection=False)
        self.quest_list.grid(row=1, column=0, sticky="ns")
        self.quest_list.bind("<<ListboxSelect>>", self._on_quest_selected)

        quest_buttons = ttk.Frame(left)
        quest_buttons.grid(row=2, column=0, sticky="ew", pady=(8, 0))
        ttk.Button(quest_buttons, text="Новый", command=self._new_quest).grid(row=0, column=0, padx=2)
        ttk.Button(quest_buttons, text="Копия", command=self._duplicate_quest).grid(row=0, column=1, padx=2)
        ttk.Button(quest_buttons, text="Удалить", command=self._delete_quest).grid(row=0, column=2, padx=2)

        main = ttk.Frame(root)
        main.grid(row=0, column=1, sticky="nsew")
        main.columnconfigure(0, weight=1)
        main.rowconfigure(2, weight=1)

        quest_frame = ttk.LabelFrame(main, text="Основные поля", padding=8)
        quest_frame.grid(row=0, column=0, sticky="ew")
        for column in (1, 3):
            quest_frame.columnconfigure(column, weight=1)
        self._add_entry(quest_frame, "ID", self.quest_id_var, 0, 0)
        self._add_combo(quest_frame, "Уровень", self.level_key_var, self.level_keys or ["level_01"], 0, 2)
        self._add_entry(quest_frame, "Title key", self.title_key_var, 1, 0)
        self._add_entry(quest_frame, "Description key", self.description_key_var, 1, 2)
        self._add_entry(quest_frame, "Category", self.category_var, 2, 0)
        self._add_entry(quest_frame, "Sort order", self.sort_order_var, 2, 2)
        self._add_entry(quest_frame, "Activation dialogue", self.activation_dialogue_file_var, 3, 0, colspan=3)

        flags_frame = ttk.LabelFrame(main, text="Required flags", padding=8)
        flags_frame.grid(row=1, column=0, sticky="ew", pady=(8, 0))
        flags_frame.columnconfigure(0, weight=1)
        ttk.Label(flags_frame, text="По одному флагу на строку").grid(row=0, column=0, sticky="w")
        self.required_flags_box = tk.Text(flags_frame, height=5, wrap="none")
        self.required_flags_box.grid(row=1, column=0, sticky="ew", pady=(6, 0))

        objectives_frame = ttk.Frame(main)
        objectives_frame.grid(row=2, column=0, sticky="nsew", pady=(8, 0))
        objectives_frame.columnconfigure(1, weight=1)
        objectives_frame.rowconfigure(0, weight=1)

        objective_list_frame = ttk.LabelFrame(objectives_frame, text="Цели", padding=8)
        objective_list_frame.grid(row=0, column=0, sticky="ns", padx=(0, 8))
        objective_list_frame.rowconfigure(1, weight=1)
        self.objective_list = tk.Listbox(objective_list_frame, width=38, exportselection=False)
        self.objective_list.grid(row=1, column=0, sticky="ns")
        self.objective_list.bind("<<ListboxSelect>>", self._on_objective_selected)

        objective_buttons = ttk.Frame(objective_list_frame)
        objective_buttons.grid(row=2, column=0, sticky="ew", pady=(8, 0))
        ttk.Button(objective_buttons, text="Новая", command=self._new_objective).grid(row=0, column=0, padx=2)
        ttk.Button(objective_buttons, text="Копия", command=self._duplicate_objective).grid(row=0, column=1, padx=2)
        ttk.Button(objective_buttons, text="Удалить", command=self._delete_objective).grid(row=0, column=2, padx=2)

        objective_form = ttk.LabelFrame(objectives_frame, text="Поля цели", padding=8)
        objective_form.grid(row=0, column=1, sticky="nsew")
        for column in (1, 3):
            objective_form.columnconfigure(column, weight=1)
        self._add_entry(objective_form, "ID", self.objective_id_var, 0, 0)
        self._add_combo(objective_form, "Kind", self.objective_kind_var, OBJECTIVE_KINDS, 0, 2)
        self._add_entry(objective_form, "Text key", self.objective_text_key_var, 1, 0, colspan=3)
        self._add_entry(objective_form, "Target", self.objective_target_var, 2, 0)
        self._add_entry(objective_form, "Required", self.objective_required_var, 2, 2)
        self._add_entry(objective_form, "Legacy flag", self.objective_legacy_flag_var, 3, 0, colspan=3)
        ttk.Button(objective_form, text="Применить цель", command=self._apply_current_objective).grid(
            row=4,
            column=0,
            columnspan=4,
            sticky="w",
            pady=(10, 0),
        )

    def _add_entry(self, parent, label, variable, row, col, colspan=1):
        pady = (0 if row == 0 else 6, 0)
        ttk.Label(parent, text=label).grid(row=row, column=col, sticky="w", pady=pady)
        ttk.Entry(parent, textvariable=variable).grid(
            row=row,
            column=col + 1,
            columnspan=colspan,
            sticky="ew",
            padx=(4, 12),
            pady=pady,
        )

    def _add_combo(self, parent, label, variable, values, row, col):
        ttk.Label(parent, text=label).grid(row=row, column=col, sticky="w")
        ttk.Combobox(parent, textvariable=variable, values=values, state="readonly").grid(
            row=row,
            column=col + 1,
            sticky="ew",
            padx=(4, 12),
        )

    def _discover_level_keys(self):
        if not LEVELS_DIR.exists():
            return []
        level_keys = sorted(path.stem for path in LEVELS_DIR.glob("level_*.json"))
        for directory in sorted(path.name for path in LEVELS_DIR.iterdir() if path.is_dir() and path.name.startswith("level_")):
            if directory not in level_keys:
                level_keys.append(directory)
        return level_keys

    def _load_all_level_quests(self):
        data = {}
        for level_key in self.level_keys:
            level_path = LEVELS_DIR / level_key / QUESTS_FILE_NAME
            if level_path.exists():
                data[level_key] = json.loads(level_path.read_text(encoding="utf-8"))
            else:
                data[level_key] = {}
        return data

    def _refresh_quest_list(self):
        self.quest_list.delete(0, tk.END)
        for quest_id in self._ordered_quest_refs():
            level_key = self._quest_level_for_id(quest_id)
            self.quest_list.insert(tk.END, f"{level_key} :: {quest_id}")

    def _ordered_quest_refs(self):
        refs = []
        for level_key, quests in self.level_quests.items():
            for quest_id, quest in quests.items():
                refs.append((level_key, int(quest.get("sort_order", 0)), quest_id))
        refs.sort(key=lambda entry: (entry[0], entry[1], entry[2]))
        return [quest_id for _level_key, _sort_order, quest_id in refs]

    def _quest_level_for_id(self, quest_id):
        for level_key, quests in self.level_quests.items():
            if quest_id in quests:
                return level_key
        return self.level_key_var.get().strip() or (self.level_keys[0] if self.level_keys else "level_01")

    def _new_quest(self):
        self.current_quest_id = None
        self.quest_id_var.set("new_quest")
        self.level_key_var.set(self.level_keys[0] if self.level_keys else "level_01")
        self.title_key_var.set("")
        self.description_key_var.set("")
        self.category_var.set("main")
        self.sort_order_var.set("0")
        self.activation_dialogue_file_var.set("")
        self._set_text(self.required_flags_box, "")
        self.current_objectives = []
        self.current_objective_index = None
        self._refresh_objective_list()
        self._load_objective_form(None)

    def _duplicate_quest(self):
        if self.current_quest_id is None:
            return
        if not self._apply_quest(silent=True):
            return
        level_key = self._quest_level_for_id(self.current_quest_id)
        source = deepcopy(self.level_quests[level_key][self.current_quest_id])
        new_id = self._unique_key(self._all_quest_ids(), f"{self.current_quest_id}_copy")
        self.level_quests[level_key][new_id] = source
        self._refresh_quest_list()
        self._load_quest_into_form(level_key, new_id)
        self._set_status(f"Создана копия квеста: {new_id}")

    def _delete_quest(self):
        if self.current_quest_id is None:
            return
        if not messagebox.askyesno("Удаление", f"Удалить квест '{self.current_quest_id}'?"):
            return
        level_key = self._quest_level_for_id(self.current_quest_id)
        del self.level_quests[level_key][self.current_quest_id]
        self._refresh_quest_list()
        self._new_quest()
        self._set_status(f"Удален квест: {level_key}/{self.current_quest_id}")

    def _on_quest_selected(self, _event=None):
        selection = self.quest_list.curselection()
        if not selection:
            return
        self._apply_quest(silent=True)
        label = self.quest_list.get(selection[0])
        level_key, quest_id = label.split(" :: ", 1)
        self._load_quest_into_form(level_key, quest_id)

    def _load_quest_into_form(self, level_key, quest_id):
        quest = deepcopy(self.level_quests.get(level_key, {}).get(quest_id))
        if quest is None:
            return
        self.current_quest_id = quest_id
        self.quest_id_var.set(quest_id)
        self.level_key_var.set(level_key)
        self.title_key_var.set(quest.get("title_key", ""))
        self.description_key_var.set(quest.get("description_key", ""))
        self.category_var.set(quest.get("category", "main"))
        self.sort_order_var.set(str(quest.get("sort_order", 0)))
        self.activation_dialogue_file_var.set(quest.get("activation_dialogue_file", ""))
        self._set_text(self.required_flags_box, "\n".join(quest.get("required_flags", [])))
        self.current_objectives = quest.get("objectives", [])
        self.current_objective_index = 0 if self.current_objectives else None
        self._refresh_objective_list()
        self._load_objective_form(self.current_objective_index)
        self._select_quest_in_list(level_key, quest_id)

    def _apply_quest(self, silent=False):
        self._apply_current_objective(silent=True)

        old_id = self.current_quest_id
        old_level_key = self._quest_level_for_id(old_id) if old_id is not None else None
        new_id = self.quest_id_var.get().strip()
        level_key = self.level_key_var.get().strip() or (self.level_keys[0] if self.level_keys else "level_01")
        if not new_id:
            if not silent:
                messagebox.showerror("Ошибка", "ID квеста обязателен.")
            return False
        if new_id != old_id and new_id in self._all_quest_ids():
            if not silent:
                messagebox.showerror("Ошибка", f"Квест '{new_id}' уже существует.")
            return False

        self.level_quests.setdefault(level_key, {})
        data = {
            "title_key": self.title_key_var.get().strip(),
            "description_key": self.description_key_var.get().strip(),
            "category": self.category_var.get().strip() or "main",
            "sort_order": self._safe_int(self.sort_order_var.get(), 0),
            "required_flags": [line.strip() for line in self._get_text(self.required_flags_box).splitlines() if line.strip()],
            "objectives": deepcopy(self.current_objectives),
        }
        activation_dialogue_file = self.activation_dialogue_file_var.get().strip()
        if activation_dialogue_file:
            data["activation_dialogue_file"] = activation_dialogue_file

        if old_id is not None and old_level_key is not None:
            if old_id in self.level_quests.get(old_level_key, {}):
                del self.level_quests[old_level_key][old_id]
        self.level_quests[level_key][new_id] = data
        self.current_quest_id = new_id
        self._refresh_quest_list()
        self._select_quest_in_list(level_key, new_id)
        if not silent:
            self._set_status(f"Применен квест: {level_key}/{new_id}")
        return True

    def _refresh_objective_list(self):
        self.objective_list.delete(0, tk.END)
        for index, objective in enumerate(self.current_objectives):
            objective_id = objective.get("id", f"objective_{index + 1}")
            objective_kind = objective.get("kind", "event")
            self.objective_list.insert(tk.END, f"{objective_id} [{objective_kind}]")

    def _new_objective(self):
        self._apply_current_objective(silent=True)
        self.current_objective_index = None
        self._load_objective_form(None)

    def _duplicate_objective(self):
        if self.current_objective_index is None or not (0 <= self.current_objective_index < len(self.current_objectives)):
            return
        self._apply_current_objective(silent=True)
        source = deepcopy(self.current_objectives[self.current_objective_index])
        source["id"] = self._unique_objective_id(source.get("id", "objective_copy"))
        self.current_objectives.append(source)
        self.current_objective_index = len(self.current_objectives) - 1
        self._refresh_objective_list()
        self._load_objective_form(self.current_objective_index)
        self.objective_list.selection_clear(0, tk.END)
        self.objective_list.selection_set(self.current_objective_index)
        self._set_status(f"Создана копия цели: {source['id']}")

    def _delete_objective(self):
        if self.current_objective_index is None or not (0 <= self.current_objective_index < len(self.current_objectives)):
            return
        deleted_id = self.current_objectives[self.current_objective_index].get("id", "objective")
        del self.current_objectives[self.current_objective_index]
        if self.current_objectives:
            self.current_objective_index = min(self.current_objective_index, len(self.current_objectives) - 1)
        else:
            self.current_objective_index = None
        self._refresh_objective_list()
        self._load_objective_form(self.current_objective_index)
        self._set_status(f"Удалена цель: {deleted_id}")

    def _on_objective_selected(self, _event=None):
        selection = self.objective_list.curselection()
        if not selection:
            return
        self._apply_current_objective(silent=True)
        self.current_objective_index = selection[0]
        self._load_objective_form(self.current_objective_index)

    def _load_objective_form(self, index):
        if index is None or not (0 <= index < len(self.current_objectives)):
            self.objective_id_var.set("objective_id")
            self.objective_kind_var.set(OBJECTIVE_KINDS[0])
            self.objective_text_key_var.set("")
            self.objective_target_var.set("")
            self.objective_required_var.set("1")
            self.objective_legacy_flag_var.set("")
            self.objective_list.selection_clear(0, tk.END)
            return

        objective = self.current_objectives[index]
        self.objective_id_var.set(objective.get("id", ""))
        self.objective_kind_var.set(objective.get("kind", OBJECTIVE_KINDS[0]))
        self.objective_text_key_var.set(objective.get("text_key", ""))
        self.objective_target_var.set(objective.get("target", ""))
        self.objective_required_var.set(str(objective.get("required", 1)))
        self.objective_legacy_flag_var.set(objective.get("legacy_flag", ""))
        self.objective_list.selection_clear(0, tk.END)
        self.objective_list.selection_set(index)
        self.objective_list.see(index)

    def _apply_current_objective(self, silent=False):
        objective_id = self.objective_id_var.get().strip()
        text_key = self.objective_text_key_var.get().strip()
        target = self.objective_target_var.get().strip()
        legacy_flag = self.objective_legacy_flag_var.get().strip()

        if not objective_id:
            if self.current_objective_index is None:
                return True
            if not silent:
                messagebox.showerror("Ошибка", "ID цели обязателен.")
            return False
        if not text_key:
            if not silent:
                messagebox.showerror("Ошибка", "Text key цели обязателен.")
            return False

        objective = {
            "id": objective_id,
            "kind": self.objective_kind_var.get().strip() or "event",
            "text_key": text_key,
            "required": max(1, self._safe_int(self.objective_required_var.get(), 1)),
        }
        if target:
            objective["target"] = target
        if legacy_flag:
            objective["legacy_flag"] = legacy_flag

        if self.current_objective_index is None:
            self.current_objectives.append(objective)
            self.current_objective_index = len(self.current_objectives) - 1
        else:
            self.current_objectives[self.current_objective_index] = objective

        self._refresh_objective_list()
        self._load_objective_form(self.current_objective_index)
        if not silent:
            self._set_status(f"Применена цель: {objective_id}")
        return True

    def _save_all(self):
        if not self._apply_quest(silent=True):
            return
        for level_key in self.level_keys:
            level_dir = LEVELS_DIR / level_key
            level_dir.mkdir(parents=True, exist_ok=True)
            level_path = level_dir / QUESTS_FILE_NAME
            level_data = self.level_quests.get(level_key, {})
            ordered = {
                quest_id: level_data[quest_id]
                for quest_id in sorted(level_data, key=lambda current_id: (int(level_data[current_id].get("sort_order", 0)), current_id))
            }
            level_path.write_text(json.dumps(ordered, ensure_ascii=False, indent=2), encoding="utf-8")
            self.level_quests[level_key] = ordered
        self._refresh_quest_list()
        if self.current_quest_id is not None:
            self._select_quest_in_list(self._quest_level_for_id(self.current_quest_id), self.current_quest_id)
        self._set_status("Сохранены все уровневые файлы квестов")

    def _all_quest_ids(self):
        result = set()
        for quests in self.level_quests.values():
            result.update(quests.keys())
        return result

    def _unique_key(self, existing_values, base):
        candidate = base
        index = 1
        while candidate in existing_values:
            candidate = f"{base}_{index}"
            index += 1
        return candidate

    def _unique_objective_id(self, base):
        existing_ids = {objective.get("id", "") for objective in self.current_objectives}
        candidate = base
        index = 1
        while candidate in existing_ids:
            candidate = f"{base}_{index}"
            index += 1
        return candidate

    def _select_quest_in_list(self, level_key, quest_id):
        target = f"{level_key} :: {quest_id}"
        values = list(self.quest_list.get(0, tk.END))
        if target not in values:
            return
        index = values.index(target)
        self.quest_list.selection_clear(0, tk.END)
        self.quest_list.selection_set(index)
        self.quest_list.see(index)

    def _set_text(self, widget, value):
        widget.delete("1.0", tk.END)
        widget.insert("1.0", value)

    def _get_text(self, widget):
        return widget.get("1.0", tk.END).strip()

    def _safe_int(self, value, default=0):
        try:
            return int(value)
        except (TypeError, ValueError):
            return default

    def _set_status(self, text):
        self.status_var.set(text)


if __name__ == "__main__":
    QuestEditor().mainloop()
