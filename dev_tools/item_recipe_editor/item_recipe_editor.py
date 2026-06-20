import json
import tkinter as tk
from copy import deepcopy
from pathlib import Path
from tkinter import messagebox, ttk


PROJECT_DIR = Path(__file__).resolve().parents[2]
ITEMS_PATH = PROJECT_DIR / "game" / "items" / "catalog_data.json"
RECIPES_PATH = PROJECT_DIR / "game" / "crafting" / "recipes_data.json"

ITEM_KINDS = [
    "consumable",
    "weapon",
    "armor",
    "accessory",
    "quest",
    "material",
    "currency",
]

EQUIP_SLOTS = [
    "",
    "helmet",
    "chest",
    "boots",
    "weapon",
    "accessory",
    "accessory_1",
    "accessory_2",
]

UNLOCK_TYPES = [
    "default",
    "knowledge",
    "quest",
    "npc",
]


class ItemRecipeEditor(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Редактор предметов и рецептов")
        self.geometry("1420x860")
        self.minsize(1220, 760)

        self.items_data = self._load_json(ITEMS_PATH)
        self.recipes_data = self._load_json(RECIPES_PATH)
        self.current_item_id = None
        self.current_recipe_id = None

        self.status_var = tk.StringVar(value="Готово")

        self._init_item_vars()
        self._init_recipe_vars()
        self._build_ui()
        self._refresh_item_list()
        self._refresh_recipe_list()
        self._new_item()
        self._new_recipe()

    def _init_item_vars(self):
        self.item_id_var = tk.StringVar()
        self.item_name_var = tk.StringVar()
        self.item_kind_var = tk.StringVar(value=ITEM_KINDS[0])
        self.item_stackable_var = tk.BooleanVar(value=True)
        self.item_max_stack_var = tk.StringVar(value="99")
        self.item_price_var = tk.StringVar(value="0")
        self.item_icon_var = tk.StringVar()
        self.item_wallet_key_var = tk.StringVar()
        self.item_equip_slot_var = tk.StringVar()
        self.item_capacity_bonus_var = tk.StringVar(value="0")
        self.item_attack_var = tk.StringVar(value="0")
        self.item_defense_var = tk.StringVar(value="0")
        self.item_speed_var = tk.StringVar(value="0")
        self.item_max_health_var = tk.StringVar(value="0")
        self.item_max_stamina_var = tk.StringVar(value="0")

    def _init_recipe_vars(self):
        self.recipe_id_var = tk.StringVar()
        self.recipe_name_var = tk.StringVar()
        self.recipe_category_var = tk.StringVar(value="tools")
        self.recipe_result_item_var = tk.StringVar()
        self.recipe_result_qty_var = tk.StringVar(value="1")
        self.recipe_unlock_type_var = tk.StringVar(value="default")
        self.recipe_knowledge_cost_var = tk.StringVar(value="0")
        self.recipe_sort_order_var = tk.StringVar(value="0")

    def _build_ui(self):
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        toolbar = ttk.Frame(self, padding=8)
        toolbar.grid(row=0, column=0, sticky="ew")
        toolbar.columnconfigure(3, weight=1)
        ttk.Button(toolbar, text="Сохранить предметы", command=self._save_items).grid(row=0, column=0, padx=2)
        ttk.Button(toolbar, text="Сохранить рецепты", command=self._save_recipes).grid(row=0, column=1, padx=2)
        ttk.Button(toolbar, text="Сохранить все", command=self._save_all).grid(row=0, column=2, padx=2)
        ttk.Label(toolbar, textvariable=self.status_var).grid(row=0, column=3, sticky="e")

        notebook = ttk.Notebook(self)
        notebook.grid(row=1, column=0, sticky="nsew", padx=8, pady=(0, 8))

        self.items_tab = ttk.Frame(notebook, padding=8)
        self.recipes_tab = ttk.Frame(notebook, padding=8)
        notebook.add(self.items_tab, text="Предметы")
        notebook.add(self.recipes_tab, text="Рецепты")

        self._build_items_tab()
        self._build_recipes_tab()

    def _build_items_tab(self):
        tab = self.items_tab
        tab.columnconfigure(1, weight=1)
        tab.rowconfigure(0, weight=1)

        left = ttk.Frame(tab)
        left.grid(row=0, column=0, sticky="ns", padx=(0, 8))
        left.rowconfigure(1, weight=1)

        ttk.Label(left, text="Список предметов").grid(row=0, column=0, sticky="w")
        self.item_list = tk.Listbox(left, width=32, exportselection=False)
        self.item_list.grid(row=1, column=0, sticky="ns")
        self.item_list.bind("<<ListboxSelect>>", self._on_item_selected)

        buttons = ttk.Frame(left)
        buttons.grid(row=2, column=0, sticky="ew", pady=(8, 0))
        ttk.Button(buttons, text="Новый", command=self._new_item).grid(row=0, column=0, padx=2)
        ttk.Button(buttons, text="Копия", command=self._duplicate_item).grid(row=0, column=1, padx=2)
        ttk.Button(buttons, text="Удалить", command=self._delete_item).grid(row=0, column=2, padx=2)
        ttk.Button(buttons, text="Применить", command=self._apply_item).grid(row=0, column=3, padx=2)

        main = ttk.Frame(tab)
        main.grid(row=0, column=1, sticky="nsew")
        main.columnconfigure(0, weight=1)
        main.rowconfigure(2, weight=1)

        top = ttk.LabelFrame(main, text="Основные поля", padding=8)
        top.grid(row=0, column=0, sticky="ew")
        for col in (1, 3):
            top.columnconfigure(col, weight=1)

        self._add_entry(top, "ID", self.item_id_var, 0, 0)
        self._add_entry(top, "Название", self.item_name_var, 0, 2)
        self._add_combo(top, "Тип", self.item_kind_var, ITEM_KINDS, 1, 0)
        self._add_combo(top, "Слот экипировки", self.item_equip_slot_var, EQUIP_SLOTS, 1, 2)
        ttk.Checkbutton(top, text="Стакается", variable=self.item_stackable_var).grid(row=2, column=0, sticky="w", pady=(8, 0))
        self._add_entry(top, "Макс. стек", self.item_max_stack_var, 2, 2)
        self._add_entry(top, "Цена", self.item_price_var, 3, 0)
        self._add_entry(top, "Бонус вместимости", self.item_capacity_bonus_var, 3, 2)
        self._add_entry(top, "Путь к иконке", self.item_icon_var, 4, 0, colspan=3)
        self._add_entry(top, "Ключ кошелька", self.item_wallet_key_var, 5, 0)

        mid = ttk.LabelFrame(main, text="Характеристики", padding=8)
        mid.grid(row=1, column=0, sticky="ew", pady=(8, 0))
        for col in (1, 3, 5):
            mid.columnconfigure(col, weight=1)
        self._add_entry(mid, "ATK", self.item_attack_var, 0, 0)
        self._add_entry(mid, "DEF", self.item_defense_var, 0, 2)
        self._add_entry(mid, "SPD", self.item_speed_var, 0, 4)
        self._add_entry(mid, "Max HP", self.item_max_health_var, 1, 0)
        self._add_entry(mid, "Max ST", self.item_max_stamina_var, 1, 2)

        bottom = ttk.LabelFrame(main, text="Описание", padding=8)
        bottom.grid(row=2, column=0, sticky="nsew", pady=(8, 0))
        bottom.columnconfigure(0, weight=1)
        bottom.rowconfigure(0, weight=1)
        self.item_description_box = tk.Text(bottom, height=8, wrap="word")
        self.item_description_box.grid(row=0, column=0, sticky="nsew")

    def _build_recipes_tab(self):
        tab = self.recipes_tab
        tab.columnconfigure(1, weight=1)
        tab.rowconfigure(0, weight=1)

        left = ttk.Frame(tab)
        left.grid(row=0, column=0, sticky="ns", padx=(0, 8))
        left.rowconfigure(1, weight=1)

        ttk.Label(left, text="Список рецептов").grid(row=0, column=0, sticky="w")
        self.recipe_list = tk.Listbox(left, width=32, exportselection=False)
        self.recipe_list.grid(row=1, column=0, sticky="ns")
        self.recipe_list.bind("<<ListboxSelect>>", self._on_recipe_selected)

        buttons = ttk.Frame(left)
        buttons.grid(row=2, column=0, sticky="ew", pady=(8, 0))
        ttk.Button(buttons, text="Новый", command=self._new_recipe).grid(row=0, column=0, padx=2)
        ttk.Button(buttons, text="Копия", command=self._duplicate_recipe).grid(row=0, column=1, padx=2)
        ttk.Button(buttons, text="Удалить", command=self._delete_recipe).grid(row=0, column=2, padx=2)
        ttk.Button(buttons, text="Применить", command=self._apply_recipe).grid(row=0, column=3, padx=2)

        main = ttk.Frame(tab)
        main.grid(row=0, column=1, sticky="nsew")
        main.columnconfigure(0, weight=1)
        main.rowconfigure(2, weight=1)

        top = ttk.LabelFrame(main, text="Основные поля", padding=8)
        top.grid(row=0, column=0, sticky="ew")
        for col in (1, 3):
            top.columnconfigure(col, weight=1)

        self._add_entry(top, "ID", self.recipe_id_var, 0, 0)
        self._add_entry(top, "Название", self.recipe_name_var, 0, 2)
        self._add_entry(top, "Категория", self.recipe_category_var, 1, 0)
        self._add_combo(top, "Тип открытия", self.recipe_unlock_type_var, UNLOCK_TYPES, 1, 2)
        self._add_combo(top, "Результат", self.recipe_result_item_var, self._item_ids_with_empty(), 2, 0)
        self._add_entry(top, "Кол-во результата", self.recipe_result_qty_var, 2, 2)
        self._add_entry(top, "Цена знаний", self.recipe_knowledge_cost_var, 3, 0)
        self._add_entry(top, "Порядок сортировки", self.recipe_sort_order_var, 3, 2)

        middle = ttk.Frame(main)
        middle.grid(row=1, column=0, sticky="nsew", pady=(8, 0))
        middle.columnconfigure(0, weight=1)
        middle.columnconfigure(1, weight=1)
        middle.rowconfigure(0, weight=1)

        ingredients_frame = ttk.LabelFrame(middle, text="Ингредиенты", padding=8)
        ingredients_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 4))
        ingredients_frame.columnconfigure(0, weight=1)
        ingredients_frame.rowconfigure(1, weight=1)
        ttk.Label(ingredients_frame, text="Формат: item_id:количество, по одному на строку").grid(row=0, column=0, sticky="w")
        self.recipe_ingredients_box = tk.Text(ingredients_frame, height=10, wrap="none")
        self.recipe_ingredients_box.grid(row=1, column=0, sticky="nsew")

        flags_frame = ttk.LabelFrame(middle, text="Требуемые флаги", padding=8)
        flags_frame.grid(row=0, column=1, sticky="nsew", padx=(4, 0))
        flags_frame.columnconfigure(0, weight=1)
        flags_frame.rowconfigure(1, weight=1)
        ttk.Label(flags_frame, text="По одному флагу на строку").grid(row=0, column=0, sticky="w")
        self.recipe_flags_box = tk.Text(flags_frame, height=10, wrap="none")
        self.recipe_flags_box.grid(row=1, column=0, sticky="nsew")

        bottom = ttk.LabelFrame(main, text="Описание", padding=8)
        bottom.grid(row=2, column=0, sticky="nsew", pady=(8, 0))
        bottom.columnconfigure(0, weight=1)
        bottom.rowconfigure(0, weight=1)
        self.recipe_description_box = tk.Text(bottom, height=8, wrap="word")
        self.recipe_description_box.grid(row=0, column=0, sticky="nsew")

    def _add_entry(self, parent, label, variable, row, col, colspan=1):
        ttk.Label(parent, text=label).grid(row=row, column=col, sticky="w", pady=(0 if row == 0 else 6, 0))
        ttk.Entry(parent, textvariable=variable).grid(
            row=row,
            column=col + 1,
            columnspan=colspan,
            sticky="ew",
            padx=(4, 12),
            pady=(0 if row == 0 else 6, 0),
        )

    def _add_combo(self, parent, label, variable, values, row, col):
        ttk.Label(parent, text=label).grid(row=row, column=col, sticky="w", pady=(6, 0))
        ttk.Combobox(parent, textvariable=variable, values=values, state="readonly").grid(
            row=row,
            column=col + 1,
            sticky="ew",
            padx=(4, 12),
            pady=(6, 0),
        )

    def _item_ids_with_empty(self):
        return [""] + sorted(self.items_data)

    def _load_json(self, path):
        if not path.exists():
            return {}
        return json.loads(path.read_text(encoding="utf-8"))

    def _save_json(self, path, data):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    def _refresh_item_list(self):
        self.item_list.delete(0, tk.END)
        for item_id in sorted(self.items_data):
            self.item_list.insert(tk.END, item_id)

    def _refresh_recipe_list(self):
        self.recipe_list.delete(0, tk.END)
        for recipe_id in sorted(self.recipes_data):
            self.recipe_list.insert(tk.END, recipe_id)

    def _refresh_item_dependent_controls(self):
        values = self._item_ids_with_empty()
        for widget in self.recipes_tab.winfo_children():
            self._update_combobox_values_recursive(widget, values)

    def _update_combobox_values_recursive(self, widget, values):
        if isinstance(widget, ttk.Combobox):
            current_values = list(widget.cget("values"))
            if current_values and set(current_values).issubset(set(values)):
                widget["values"] = values
        for child in widget.winfo_children():
            self._update_combobox_values_recursive(child, values)

    def _new_item(self):
        self.current_item_id = None
        self.item_id_var.set("new_item")
        self.item_name_var.set("")
        self.item_kind_var.set("material")
        self.item_stackable_var.set(True)
        self.item_max_stack_var.set("99")
        self.item_price_var.set("0")
        self.item_icon_var.set("")
        self.item_wallet_key_var.set("")
        self.item_equip_slot_var.set("")
        self.item_capacity_bonus_var.set("0")
        self.item_attack_var.set("0")
        self.item_defense_var.set("0")
        self.item_speed_var.set("0")
        self.item_max_health_var.set("0")
        self.item_max_stamina_var.set("0")
        self._set_text(self.item_description_box, "")

    def _duplicate_item(self):
        if self.current_item_id not in self.items_data:
            return
        self._apply_item(silent=True)
        source = deepcopy(self.items_data[self.current_item_id])
        new_id = self._unique_key(self.items_data, f"{self.current_item_id}_copy")
        self.items_data[new_id] = source
        self.current_item_id = new_id
        self._refresh_item_list()
        self._load_item_into_form(new_id)
        self._set_status(f"Создана копия предмета: {new_id}")

    def _delete_item(self):
        if self.current_item_id not in self.items_data:
            return
        if not messagebox.askyesno("Удаление", f"Удалить предмет '{self.current_item_id}'?"):
            return
        deleted = self.current_item_id
        del self.items_data[deleted]
        if any(recipe.get("result", {}).get("item_id") == deleted for recipe in self.recipes_data.values()):
            self._set_status("Внимание: удаленный предмет используется в рецептах")
        self.current_item_id = None
        self._refresh_item_list()
        self._refresh_item_dependent_controls()
        self._new_item()

    def _on_item_selected(self, _event=None):
        selection = self.item_list.curselection()
        if not selection:
            return
        self._apply_item(silent=True)
        item_id = self.item_list.get(selection[0])
        self._load_item_into_form(item_id)

    def _load_item_into_form(self, item_id):
        if item_id not in self.items_data:
            return
        self.current_item_id = item_id
        item = self.items_data[item_id]
        self.item_id_var.set(item_id)
        self.item_name_var.set(item.get("name", ""))
        self.item_kind_var.set(item.get("kind", "material"))
        self.item_stackable_var.set(bool(item.get("stackable", True)))
        self.item_max_stack_var.set(str(item.get("max_stack", 99)))
        self.item_price_var.set(str(item.get("price", 0)))
        self.item_icon_var.set(item.get("icon_path", ""))
        self.item_wallet_key_var.set(item.get("wallet_key", ""))
        self.item_equip_slot_var.set(item.get("equip_slot", ""))
        self.item_capacity_bonus_var.set(str(item.get("inventory_capacity_bonus", 0)))
        stats = item.get("stats", {})
        self.item_attack_var.set(str(stats.get("attack", 0)))
        self.item_defense_var.set(str(stats.get("defense", 0)))
        self.item_speed_var.set(str(stats.get("speed", 0)))
        self.item_max_health_var.set(str(stats.get("max_health", 0)))
        self.item_max_stamina_var.set(str(stats.get("max_stamina", 0)))
        self._set_text(self.item_description_box, item.get("description", ""))

    def _apply_item(self, silent=False):
        old_id = self.current_item_id
        new_id = self.item_id_var.get().strip()
        if not new_id:
            if not silent:
                messagebox.showerror("Ошибка", "ID предмета обязателен.")
            return False
        if new_id != old_id and new_id in self.items_data:
            if not silent:
                messagebox.showerror("Ошибка", f"Предмет '{new_id}' уже существует.")
            return False

        data = {
            "name": self.item_name_var.get().strip() or new_id,
            "kind": self.item_kind_var.get().strip() or "material",
            "stackable": bool(self.item_stackable_var.get()),
            "max_stack": max(1, self._safe_int(self.item_max_stack_var.get(), 99)),
            "price": max(0, self._safe_int(self.item_price_var.get(), 0)),
            "description": self._get_text(self.item_description_box).strip(),
        }

        icon_path = self.item_icon_var.get().strip()
        if icon_path:
            data["icon_path"] = icon_path
        wallet_key = self.item_wallet_key_var.get().strip()
        if wallet_key:
            data["wallet_key"] = wallet_key
        equip_slot = self.item_equip_slot_var.get().strip()
        if equip_slot:
            data["equip_slot"] = equip_slot
        inventory_capacity_bonus = self._safe_int(self.item_capacity_bonus_var.get(), 0)
        if inventory_capacity_bonus > 0:
            data["inventory_capacity_bonus"] = inventory_capacity_bonus

        stats = {}
        for key, value in (
            ("attack", self.item_attack_var.get()),
            ("defense", self.item_defense_var.get()),
            ("speed", self.item_speed_var.get()),
            ("max_health", self.item_max_health_var.get()),
            ("max_stamina", self.item_max_stamina_var.get()),
        ):
            parsed = self._safe_int(value, 0)
            if parsed != 0:
                stats[key] = parsed
        if stats:
            data["stats"] = stats

        if new_id != old_id and old_id in self.items_data:
            del self.items_data[old_id]
            self._replace_item_references(old_id, new_id)

        self.items_data[new_id] = data
        self.current_item_id = new_id
        self._refresh_item_list()
        self._select_in_list(self.item_list, new_id)
        self._refresh_item_dependent_controls()
        if not silent:
            self._set_status(f"Применен предмет: {new_id}")
        return True

    def _replace_item_references(self, old_id, new_id):
        for recipe in self.recipes_data.values():
            if recipe.get("result", {}).get("item_id") == old_id:
                recipe["result"]["item_id"] = new_id
            for ingredient in recipe.get("ingredients", []):
                if ingredient.get("item_id") == old_id:
                    ingredient["item_id"] = new_id

    def _save_items(self):
        if not self._apply_item(silent=True):
            return
        self._save_json(ITEMS_PATH, self.items_data)
        self._set_status(f"Сохранены предметы: {ITEMS_PATH.name}")

    def _new_recipe(self):
        self.current_recipe_id = None
        self.recipe_id_var.set("new_recipe")
        self.recipe_name_var.set("")
        self.recipe_category_var.set("tools")
        self.recipe_result_item_var.set("")
        self.recipe_result_qty_var.set("1")
        self.recipe_unlock_type_var.set("default")
        self.recipe_knowledge_cost_var.set("0")
        self.recipe_sort_order_var.set("0")
        self._set_text(self.recipe_description_box, "")
        self._set_text(self.recipe_ingredients_box, "")
        self._set_text(self.recipe_flags_box, "")

    def _duplicate_recipe(self):
        if self.current_recipe_id not in self.recipes_data:
            return
        self._apply_recipe(silent=True)
        source = deepcopy(self.recipes_data[self.current_recipe_id])
        new_id = self._unique_key(self.recipes_data, f"{self.current_recipe_id}_copy")
        self.recipes_data[new_id] = source
        self.current_recipe_id = new_id
        self._refresh_recipe_list()
        self._load_recipe_into_form(new_id)
        self._set_status(f"Создана копия рецепта: {new_id}")

    def _delete_recipe(self):
        if self.current_recipe_id not in self.recipes_data:
            return
        if not messagebox.askyesno("Удаление", f"Удалить рецепт '{self.current_recipe_id}'?"):
            return
        del self.recipes_data[self.current_recipe_id]
        self.current_recipe_id = None
        self._refresh_recipe_list()
        self._new_recipe()

    def _on_recipe_selected(self, _event=None):
        selection = self.recipe_list.curselection()
        if not selection:
            return
        self._apply_recipe(silent=True)
        recipe_id = self.recipe_list.get(selection[0])
        self._load_recipe_into_form(recipe_id)

    def _load_recipe_into_form(self, recipe_id):
        if recipe_id not in self.recipes_data:
            return
        self.current_recipe_id = recipe_id
        recipe = self.recipes_data[recipe_id]
        self.recipe_id_var.set(recipe_id)
        self.recipe_name_var.set(recipe.get("name", ""))
        self.recipe_category_var.set(recipe.get("category", "tools"))
        self.recipe_result_item_var.set(recipe.get("result", {}).get("item_id", ""))
        self.recipe_result_qty_var.set(str(recipe.get("result", {}).get("quantity", 1)))
        self.recipe_unlock_type_var.set(recipe.get("unlock_type", "default"))
        self.recipe_knowledge_cost_var.set(str(recipe.get("knowledge_cost", 0)))
        self.recipe_sort_order_var.set(str(recipe.get("sort_order", 0)))
        self._set_text(self.recipe_description_box, recipe.get("description", ""))
        self._set_text(self.recipe_ingredients_box, self._format_ingredients(recipe.get("ingredients", [])))
        self._set_text(self.recipe_flags_box, "\n".join(recipe.get("required_flags", [])))

    def _apply_recipe(self, silent=False):
        old_id = self.current_recipe_id
        new_id = self.recipe_id_var.get().strip()
        if not new_id:
            if not silent:
                messagebox.showerror("Ошибка", "ID рецепта обязателен.")
            return False
        if new_id != old_id and new_id in self.recipes_data:
            if not silent:
                messagebox.showerror("Ошибка", f"Рецепт '{new_id}' уже существует.")
            return False

        result_item = self.recipe_result_item_var.get().strip()
        if not result_item:
            if not silent:
                messagebox.showerror("Ошибка", "Нужно указать предмет результата.")
            return False
        if result_item not in self.items_data:
            if not silent:
                messagebox.showerror("Ошибка", f"Предмет результата '{result_item}' не найден.")
            return False

        ingredients = self._parse_ingredients(self._get_text(self.recipe_ingredients_box))
        if ingredients is None:
            if not silent:
                messagebox.showerror("Ошибка", "Проверьте формат ингредиентов. Нужен item_id:количество.")
            return False

        data = {
            "name": self.recipe_name_var.get().strip() or new_id,
            "category": self.recipe_category_var.get().strip() or "tools",
            "description": self._get_text(self.recipe_description_box).strip(),
            "ingredients": ingredients,
            "result": {
                "item_id": result_item,
                "quantity": max(1, self._safe_int(self.recipe_result_qty_var.get(), 1)),
            },
            "unlock_type": self.recipe_unlock_type_var.get().strip() or "default",
            "sort_order": self._safe_int(self.recipe_sort_order_var.get(), 0),
        }

        knowledge_cost = self._safe_int(self.recipe_knowledge_cost_var.get(), 0)
        if knowledge_cost > 0:
            data["knowledge_cost"] = knowledge_cost

        flags = [line.strip() for line in self._get_text(self.recipe_flags_box).splitlines() if line.strip()]
        if flags:
            data["required_flags"] = flags

        if new_id != old_id and old_id in self.recipes_data:
            del self.recipes_data[old_id]
        self.recipes_data[new_id] = data
        self.current_recipe_id = new_id
        self._refresh_recipe_list()
        self._select_in_list(self.recipe_list, new_id)
        if not silent:
            self._set_status(f"Применен рецепт: {new_id}")
        return True

    def _save_recipes(self):
        if not self._apply_recipe(silent=True):
            return
        self._save_json(RECIPES_PATH, self.recipes_data)
        self._set_status(f"Сохранены рецепты: {RECIPES_PATH.name}")

    def _save_all(self):
        if not self._apply_item(silent=True):
            return
        if not self._apply_recipe(silent=True):
            return
        self._save_json(ITEMS_PATH, self.items_data)
        self._save_json(RECIPES_PATH, self.recipes_data)
        self._set_status("Сохранены предметы и рецепты")

    def _parse_ingredients(self, text):
        ingredients = []
        for raw_line in text.splitlines():
            line = raw_line.strip()
            if not line:
                continue
            if ":" not in line:
                return None
            item_id, quantity = line.split(":", 1)
            item_id = item_id.strip()
            if item_id not in self.items_data:
                return None
            ingredients.append(
                {
                    "item_id": item_id,
                    "quantity": max(1, self._safe_int(quantity.strip(), 1)),
                }
            )
        return ingredients

    def _format_ingredients(self, ingredients):
        return "\n".join(f"{entry.get('item_id', '')}:{entry.get('quantity', 1)}" for entry in ingredients)

    def _select_in_list(self, widget, value):
        values = list(widget.get(0, tk.END))
        if value not in values:
            return
        index = values.index(value)
        widget.selection_clear(0, tk.END)
        widget.selection_set(index)
        widget.see(index)

    def _unique_key(self, mapping, base):
        candidate = base
        index = 1
        while candidate in mapping:
            candidate = f"{base}_{index}"
            index += 1
        return candidate

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
    ItemRecipeEditor().mainloop()
