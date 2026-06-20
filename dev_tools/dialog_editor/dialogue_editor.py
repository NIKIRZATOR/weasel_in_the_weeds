import json
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk


PROJECT_DIR = Path(__file__).resolve().parents[1]
DIALOGUES_DIR = PROJECT_DIR / "dialogues"


class DialogueEditor(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Редактор диалогов")
        self.geometry("1120x720")
        self.minsize(980, 620)

        self.file_path = None
        self.nodes = {}
        self.current_node_id = None

        self.dialogue_id_var = tk.StringVar(value="new_dialogue")
        self.start_var = tk.StringVar()
        self.node_id_var = tk.StringVar()
        self.speaker_var = tk.StringVar(value="npc")
        self.next_var = tk.StringVar()
        self.choice_text_var = tk.StringVar()
        self.choice_next_var = tk.StringVar()
        self.coins_var = tk.StringVar(value="0")
        self.status_var = tk.StringVar(value="Готово")

        self._build_ui()
        self._new_dialogue()

    def _build_ui(self):
        self.columnconfigure(1, weight=1)
        self.rowconfigure(1, weight=1)

        toolbar = ttk.Frame(self, padding=8)
        toolbar.grid(row=0, column=0, columnspan=2, sticky="ew")
        toolbar.columnconfigure(9, weight=1)

        ttk.Button(toolbar, text="Новый", command=self._new_dialogue).grid(row=0, column=0, padx=2)
        ttk.Button(toolbar, text="Открыть", command=self._open_dialogue).grid(row=0, column=1, padx=2)
        ttk.Button(toolbar, text="Сохранить", command=self._save_dialogue).grid(row=0, column=2, padx=2)
        ttk.Button(toolbar, text="Сохранить как", command=self._save_dialogue_as).grid(row=0, column=3, padx=2)

        ttk.Label(toolbar, text="ID диалога").grid(row=0, column=4, padx=(16, 4))
        ttk.Entry(toolbar, textvariable=self.dialogue_id_var, width=22).grid(row=0, column=5, padx=2)

        ttk.Label(toolbar, text="Старт").grid(row=0, column=6, padx=(16, 4))
        self.start_combo = ttk.Combobox(toolbar, textvariable=self.start_var, width=22)
        self.start_combo.grid(row=0, column=7, padx=2)

        ttk.Button(toolbar, text="Проверить", command=self._validate_dialogue).grid(row=0, column=8, padx=(16, 2))

        left = ttk.Frame(self, padding=(8, 0, 4, 8))
        left.grid(row=1, column=0, sticky="ns")
        left.rowconfigure(1, weight=1)

        ttk.Label(left, text="Узлы").grid(row=0, column=0, sticky="w")
        self.node_list = tk.Listbox(left, width=30, exportselection=False)
        self.node_list.grid(row=1, column=0, sticky="ns")
        self.node_list.bind("<<ListboxSelect>>", self._on_node_selected)

        node_buttons = ttk.Frame(left)
        node_buttons.grid(row=2, column=0, sticky="ew", pady=(8, 0))
        ttk.Button(node_buttons, text="Добавить", command=self._add_node).grid(row=0, column=0, padx=2)
        ttk.Button(node_buttons, text="Копия", command=self._duplicate_node).grid(row=0, column=1, padx=2)
        ttk.Button(node_buttons, text="Удалить", command=self._delete_node).grid(row=0, column=2, padx=2)

        main = ttk.Frame(self, padding=(4, 0, 8, 8))
        main.grid(row=1, column=1, sticky="nsew")
        main.columnconfigure(0, weight=1)
        main.rowconfigure(2, weight=1)

        node_header = ttk.LabelFrame(main, text="Узел", padding=8)
        node_header.grid(row=0, column=0, sticky="ew")
        for column in (1, 3, 5):
            node_header.columnconfigure(column, weight=1)

        ttk.Label(node_header, text="ID").grid(row=0, column=0, sticky="w")
        ttk.Entry(node_header, textvariable=self.node_id_var).grid(row=0, column=1, sticky="ew", padx=(4, 12))

        ttk.Label(node_header, text="Кто говорит").grid(row=0, column=2, sticky="w")
        ttk.Combobox(
            node_header,
            textvariable=self.speaker_var,
            values=("npc", "player"),
            width=10,
            state="readonly",
        ).grid(row=0, column=3, sticky="ew", padx=(4, 12))

        ttk.Label(node_header, text="Следующий").grid(row=0, column=4, sticky="w")
        self.next_combo = ttk.Combobox(node_header, textvariable=self.next_var)
        self.next_combo.grid(row=0, column=5, sticky="ew", padx=(4, 0))

        text_frame = ttk.LabelFrame(main, text="Текст реплики", padding=8)
        text_frame.grid(row=1, column=0, sticky="nsew", pady=(8, 0))
        text_frame.columnconfigure(0, weight=1)
        self.text_box = tk.Text(text_frame, height=5, wrap="word")
        self.text_box.grid(row=0, column=0, sticky="nsew")

        bottom = ttk.Frame(main)
        bottom.grid(row=2, column=0, sticky="nsew", pady=(8, 0))
        bottom.columnconfigure(0, weight=2)
        bottom.columnconfigure(1, weight=1)
        bottom.rowconfigure(0, weight=1)

        choices = ttk.LabelFrame(bottom, text="Варианты ответа", padding=8)
        choices.grid(row=0, column=0, sticky="nsew", padx=(0, 4))
        choices.columnconfigure(0, weight=1)
        choices.rowconfigure(0, weight=1)

        self.choice_list = tk.Listbox(choices, height=8, exportselection=False)
        self.choice_list.grid(row=0, column=0, columnspan=4, sticky="nsew")
        self.choice_list.bind("<<ListboxSelect>>", self._on_choice_selected)

        ttk.Label(choices, text="Текст").grid(row=1, column=0, sticky="w", pady=(8, 0))
        ttk.Entry(choices, textvariable=self.choice_text_var).grid(row=2, column=0, sticky="ew", padx=(0, 4))
        ttk.Label(choices, text="Следующий").grid(row=1, column=1, sticky="w", pady=(8, 0))
        self.choice_next_combo = ttk.Combobox(choices, textvariable=self.choice_next_var, width=18)
        self.choice_next_combo.grid(row=2, column=1, sticky="ew", padx=(0, 4))
        ttk.Button(choices, text="Добавить/обновить", command=self._add_or_update_choice).grid(row=2, column=2, padx=2)
        ttk.Button(choices, text="Убрать", command=self._remove_choice).grid(row=2, column=3, padx=2)

        rewards = ttk.LabelFrame(bottom, text="Награды", padding=8)
        rewards.grid(row=0, column=1, sticky="nsew", padx=(4, 0))
        rewards.columnconfigure(0, weight=1)
        rewards.rowconfigure(3, weight=1)
        rewards.rowconfigure(5, weight=1)

        ttk.Label(rewards, text="Монеты").grid(row=0, column=0, sticky="w")
        ttk.Entry(rewards, textvariable=self.coins_var).grid(row=1, column=0, sticky="ew")

        ttk.Label(rewards, text="Предметы: item_id или item_id:количество, по одному на строку").grid(row=2, column=0, sticky="w", pady=(8, 0))
        self.items_box = tk.Text(rewards, height=5, wrap="none")
        self.items_box.grid(row=3, column=0, sticky="nsew")

        ttk.Label(rewards, text="Флаги, по одному на строку").grid(row=4, column=0, sticky="w", pady=(8, 0))
        self.flags_box = tk.Text(rewards, height=5, wrap="none")
        self.flags_box.grid(row=5, column=0, sticky="nsew")

        actions = ttk.Frame(main)
        actions.grid(row=3, column=0, sticky="ew", pady=(8, 0))
        actions.columnconfigure(2, weight=1)
        ttk.Button(actions, text="Применить узел", command=self._apply_current_node).grid(row=0, column=0, padx=2)
        ttk.Button(actions, text="Очистить награды", command=self._clear_rewards).grid(row=0, column=1, padx=2)
        ttk.Label(actions, textvariable=self.status_var).grid(row=0, column=2, sticky="e")

    def _new_dialogue(self):
        self.file_path = None
        self.dialogue_id_var.set("new_dialogue")
        self.nodes = {
            "start": {
                "speaker": "npc",
                "text": "Hello, traveler.",
                "next": None,
            }
        }
        self.start_var.set("start")
        self.current_node_id = "start"
        self._refresh_node_list()
        self._load_node_into_form("start")
        self._set_status("Новый диалог")

    def _open_dialogue(self):
        path = filedialog.askopenfilename(
            initialdir=DIALOGUES_DIR,
            filetypes=(("JSON диалога", "*.json"), ("Все файлы", "*.*")),
        )
        if not path:
            return

        data = json.loads(Path(path).read_text(encoding="utf-8"))
        self.file_path = Path(path)
        self.dialogue_id_var.set(data.get("id", self.file_path.stem))
        self.nodes = data.get("nodes", {})
        self.start_var.set(data.get("start", next(iter(self.nodes), "")))
        self.current_node_id = self.start_var.get() if self.start_var.get() in self.nodes else next(iter(self.nodes), None)
        self._refresh_node_list()
        self._load_node_into_form(self.current_node_id)
        self._set_status(f"Открыт файл: {self.file_path.name}")

    def _save_dialogue(self):
        if self.file_path is None:
            self._save_dialogue_as()
            return
        self._write_dialogue(self.file_path)

    def _save_dialogue_as(self):
        DIALOGUES_DIR.mkdir(parents=True, exist_ok=True)
        path = filedialog.asksaveasfilename(
            initialdir=DIALOGUES_DIR,
            initialfile=f"{self.dialogue_id_var.get() or 'dialogue'}.json",
            defaultextension=".json",
            filetypes=(("JSON диалога", "*.json"), ("Все файлы", "*.*")),
        )
        if not path:
            return
        self.file_path = Path(path)
        self._write_dialogue(self.file_path)

    def _write_dialogue(self, path):
        self._apply_current_node(silent=True)
        errors = self._get_validation_errors()
        if errors and not messagebox.askyesno("Предупреждения проверки", "\n".join(errors) + "\n\nВсе равно сохранить?"):
            return

        data = {
            "id": self.dialogue_id_var.get().strip() or path.stem,
            "start": self.start_var.get().strip() or None,
            "nodes": self.nodes,
        }
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        self._set_status(f"Сохранено: {path.name}")

    def _add_node(self):
        node_id = self._unique_node_id("node")
        self.nodes[node_id] = {"speaker": "npc", "text": "", "next": None}
        if not self.start_var.get():
            self.start_var.set(node_id)
        self.current_node_id = node_id
        self._refresh_node_list()
        self._load_node_into_form(node_id)

    def _duplicate_node(self):
        if self.current_node_id not in self.nodes:
            return
        node_id = self._unique_node_id(f"{self.current_node_id}_copy")
        self.nodes[node_id] = json.loads(json.dumps(self.nodes[self.current_node_id]))
        self.current_node_id = node_id
        self._refresh_node_list()
        self._load_node_into_form(node_id)

    def _delete_node(self):
        if self.current_node_id not in self.nodes:
            return
        if not messagebox.askyesno("Удаление узла", f"Удалить узел '{self.current_node_id}'?"):
            return

        deleted = self.current_node_id
        del self.nodes[deleted]
        for node in self.nodes.values():
            if node.get("next") == deleted:
                node["next"] = None
            for choice in node.get("choices", []):
                if choice.get("next") == deleted:
                    choice["next"] = None
        if self.start_var.get() == deleted:
            self.start_var.set(next(iter(self.nodes), ""))
        self.current_node_id = next(iter(self.nodes), None)
        self._refresh_node_list()
        self._load_node_into_form(self.current_node_id)

    def _on_node_selected(self, _event=None):
        selection = self.node_list.curselection()
        if not selection:
            return
        self._apply_current_node(silent=True)
        node_id = self.node_list.get(selection[0])
        self.current_node_id = node_id
        self._load_node_into_form(node_id)

    def _load_node_into_form(self, node_id):
        self._clear_form()
        if node_id is None or node_id not in self.nodes:
            return

        node = self.nodes[node_id]
        self.node_id_var.set(node_id)
        self.speaker_var.set(node.get("speaker", "npc"))
        self.next_var.set(node.get("next") or "")
        self.text_box.insert("1.0", node.get("text", ""))

        for choice in node.get("choices", []):
            self.choice_list.insert(tk.END, self._format_choice(choice))

        rewards = node.get("rewards", {})
        self.coins_var.set(str(rewards.get("coins", 0)))
        self._set_text_lines(self.items_box, self._format_items(rewards.get("items", [])))
        self._set_text_lines(self.flags_box, rewards.get("flags", []))
        self._refresh_combos()

    def _apply_current_node(self, silent=False):
        if self.current_node_id is None:
            return False

        old_id = self.current_node_id
        new_id = self.node_id_var.get().strip()
        if not new_id:
            if not silent:
                messagebox.showerror("Некорректный узел", "ID узла обязателен.")
            return False
        if new_id != old_id and new_id in self.nodes:
            if not silent:
                messagebox.showerror("Некорректный узел", f"Узел '{new_id}' уже существует.")
            return False

        node = {
            "speaker": self.speaker_var.get() or "npc",
            "text": self.text_box.get("1.0", tk.END).strip(),
        }

        choices = self._read_choices()
        next_node = self.next_var.get().strip()
        if choices:
            node["choices"] = choices
        elif next_node:
            node["next"] = next_node
        else:
            node["next"] = None

        rewards = self._read_rewards()
        if rewards:
            node["rewards"] = rewards

        if new_id != old_id:
            self.nodes[new_id] = node
            del self.nodes[old_id]
            self._replace_node_references(old_id, new_id)
            if self.start_var.get() == old_id:
                self.start_var.set(new_id)
            self.current_node_id = new_id
        else:
            self.nodes[old_id] = node

        self._refresh_node_list()
        self._select_node_in_list(self.current_node_id)
        self._refresh_combos()
        if not silent:
            self._set_status(f"Применен узел: {self.current_node_id}")
        return True

    def _replace_node_references(self, old_id, new_id):
        for node in self.nodes.values():
            if node.get("next") == old_id:
                node["next"] = new_id
            for choice in node.get("choices", []):
                if choice.get("next") == old_id:
                    choice["next"] = new_id

    def _add_or_update_choice(self):
        text = self.choice_text_var.get().strip()
        if not text:
            messagebox.showerror("Некорректный вариант", "Текст варианта обязателен.")
            return

        choice = {
            "text": text,
            "next": self.choice_next_var.get().strip() or None,
        }
        selection = self.choice_list.curselection()
        if selection:
            index = selection[0]
            self.choice_list.delete(index)
            self.choice_list.insert(index, self._format_choice(choice))
            self.choice_list.selection_set(index)
        else:
            self.choice_list.insert(tk.END, self._format_choice(choice))
        self.choice_text_var.set("")
        self.choice_next_var.set("")

    def _remove_choice(self):
        selection = self.choice_list.curselection()
        if selection:
            self.choice_list.delete(selection[0])
        self.choice_text_var.set("")
        self.choice_next_var.set("")

    def _on_choice_selected(self, _event=None):
        selection = self.choice_list.curselection()
        if not selection:
            return
        choice = self._parse_choice(self.choice_list.get(selection[0]))
        self.choice_text_var.set(choice["text"])
        self.choice_next_var.set(choice.get("next") or "")

    def _clear_rewards(self):
        self.coins_var.set("0")
        self.items_box.delete("1.0", tk.END)
        self.flags_box.delete("1.0", tk.END)

    def _validate_dialogue(self):
        self._apply_current_node(silent=True)
        errors = self._get_validation_errors()
        if errors:
            messagebox.showwarning("Проверка", "\n".join(errors))
            self._set_status("Есть предупреждения")
        else:
            messagebox.showinfo("Проверка", "Диалог выглядит корректно.")
            self._set_status("Проверка пройдена")

    def _get_validation_errors(self):
        errors = []
        start = self.start_var.get().strip()
        if not start:
            errors.append("Стартовый узел не указан.")
        elif start not in self.nodes:
            errors.append(f"Стартовый узел '{start}' не существует.")

        for node_id, node in self.nodes.items():
            next_node = node.get("next")
            if next_node and next_node not in self.nodes:
                errors.append(f"Узел '{node_id}' ведет к несуществующему узлу '{next_node}'.")
            for choice in node.get("choices", []):
                choice_next = choice.get("next")
                if choice_next and choice_next not in self.nodes:
                    errors.append(f"Вариант в узле '{node_id}' ведет к несуществующему узлу '{choice_next}'.")
        return errors

    def _read_choices(self):
        return [self._parse_choice(self.choice_list.get(index)) for index in range(self.choice_list.size())]

    def _read_rewards(self):
        rewards = {}
        coins = self._safe_int(self.coins_var.get())
        if coins > 0:
            rewards["coins"] = coins

        items = self._parse_items(self._get_text_lines(self.items_box))
        if items:
            rewards["items"] = items

        flags = self._get_text_lines(self.flags_box)
        if flags:
            rewards["flags"] = flags

        return rewards

    def _parse_items(self, lines):
        items = []
        for line in lines:
            if ":" not in line:
                items.append(line)
                continue
            item_id, quantity = line.split(":", 1)
            item_id = item_id.strip()
            quantity = self._safe_int(quantity, default=1)
            if item_id:
                items.append({"item_id": item_id, "quantity": max(1, quantity)})
        return items

    def _format_items(self, items):
        lines = []
        for item in items:
            if isinstance(item, str):
                lines.append(item)
            else:
                lines.append(f"{item.get('item_id', '')}:{item.get('quantity', 1)}")
        return lines

    def _parse_choice(self, value):
        text, separator, next_node = value.partition(" -> ")
        return {
            "text": text,
            "next": next_node if separator and next_node else None,
        }

    def _format_choice(self, choice):
        text = choice.get("text", "")
        next_node = choice.get("next")
        if next_node:
            return f"{text} -> {next_node}"
        return text

    def _refresh_node_list(self):
        self.node_list.delete(0, tk.END)
        for node_id in sorted(self.nodes):
            self.node_list.insert(tk.END, node_id)
        self._select_node_in_list(self.current_node_id)
        self._refresh_combos()

    def _refresh_combos(self):
        values = [""] + sorted(self.nodes)
        self.start_combo["values"] = sorted(self.nodes)
        self.next_combo["values"] = values
        self.choice_next_combo["values"] = values

    def _select_node_in_list(self, node_id):
        if not node_id:
            return
        values = list(self.node_list.get(0, tk.END))
        if node_id not in values:
            return
        index = values.index(node_id)
        self.node_list.selection_clear(0, tk.END)
        self.node_list.selection_set(index)
        self.node_list.see(index)

    def _clear_form(self):
        self.node_id_var.set("")
        self.speaker_var.set("npc")
        self.next_var.set("")
        self.text_box.delete("1.0", tk.END)
        self.choice_list.delete(0, tk.END)
        self.choice_text_var.set("")
        self.choice_next_var.set("")
        self._clear_rewards()

    def _unique_node_id(self, base):
        candidate = base
        index = 1
        while candidate in self.nodes:
            candidate = f"{base}_{index}"
            index += 1
        return candidate

    def _set_text_lines(self, widget, lines):
        widget.delete("1.0", tk.END)
        widget.insert("1.0", "\n".join(str(line) for line in lines))

    def _get_text_lines(self, widget):
        return [line.strip() for line in widget.get("1.0", tk.END).splitlines() if line.strip()]

    def _safe_int(self, value, default=0):
        try:
            return int(value)
        except (TypeError, ValueError):
            return default

    def _set_status(self, text):
        self.status_var.set(text)


if __name__ == "__main__":
    DialogueEditor().mainloop()
