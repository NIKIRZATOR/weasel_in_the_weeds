import json
import tkinter as tk
import xml.etree.ElementTree as ET
from copy import deepcopy
from pathlib import Path
from tkinter import messagebox, ttk

from PIL import Image, ImageDraw, ImageTk


PROJECT_DIR = Path(__file__).resolve().parents[2]
LEVELS_DIR = PROJECT_DIR / "levels"
ASSETS_DIR = PROJECT_DIR / "assets"
CATALOGS_DIR = Path(__file__).resolve().with_name("catalogs")

PALETTE_CATEGORIES = (
    ("enemies", "Enemies"),
    ("bosses", "Bosses"),
    ("npc", "NPC"),
    ("pickable", "Pickable"),
    ("containers", "Containers"),
    ("gatherable", "Gatherable"),
    ("solid", "Solid"),
    ("passable", "Passable"),
    ("zones", "Zones"),
)

CONTAINER_SPRITES = {
    "crate": "world_objects/container_object/crate.png",
    "chest": "world_objects/container_object/chest.png",
    "large_chest": "world_objects/container_object/large_chest.png",
}

GATHERABLE_TEMPLATE_SPRITES = {
    "berry_bush_small": "world_objects/gatherable_object/berry_bush_full.png",
    "fallen_log_small": "world_objects/gatherable_object/fallen_log_full.png",
    "stone_pile_small": "world_objects/gatherable_object/stone_pile_full.png",
    "bug_remains_small": "world_objects/gatherable_object/stump_full.png",
}

PICKABLE_SPRITES = {
    "coin": "world_objects/pickable_object/coin.png",
    "stick": "world_objects/pickable_object/stick.png",
}

SOLID_OBJECT_SPRITES = {
    "stone block": "world_objects/solid_object/stone_block.png",
    "bush": "world_objects/solid_object/bush.png",
    "blue flower": "world_objects/solid_object/flower_blue.png",
    "pink flower": "world_objects/solid_object/flower_pink.png",
    "red white flower": "world_objects/solid_object/flower_red_white.png",
    "white flower": "world_objects/solid_object/flower_white.png",
    "yellow flower": "world_objects/solid_object/flower_yellow.png",
    "stone pile": "world_objects/solid_object/small_stone_pile.png",
}

ENEMY_PREVIEW_SPRITES = {
    "enemy_beetle": ("enemies/beatle/beatle_idle.png", 64, 64),
    "enemy_spider": ("enemies/spider/spider_idle.png", 64, 64),
    "enemy_melee": ("enemies/goat_warrior/goat_idle.png", 64, 64),
    "enemy_ranged": ("enemies/wasp_archer/wasp_idle_moves.png", 64, 64),
    "enemy_boss_forest_guardian": ("bosses/forest_guardian/forest_guardian_idle.png", 64, 64),
}

TILE_COLORS = {
    0: "#1f8f2a",
    1: "#5a4030",
    2: "#456fa8",
    3: "#3f8f32",
}

OBJECT_COLORS = {
    "enemy_beetle": "#b56a2a",
    "enemy_spider": "#735a96",
    "enemy_melee": "#d35a4a",
    "enemy_ranged": "#d7a748",
    "enemy_boss_forest_guardian": "#4f8f73",
    "npc_object": "#7bc6a4",
    "checkpoint_object": "#73a6ff",
    "container_object": "#b98243",
    "pickable_object": "#ffe16a",
    "gatherable_object": "#65b65b",
    "solid_object": "#888888",
    "passable_object": "#b5b5b5",
    "grass_hide_zone": "#54c450",
    "interactable_object": "#9fa8da",
    "level_transition": "#f18ec2",
}

ENEMY_EDITOR_DEFAULTS = {
    "enemy_melee": {
        "detection_radius": 150,
        "patrol_radius": 140,
        "attack_radius_key": "melee_range",
        "attack_radius": 60,
        "body_hitbox": {"width": 48, "height": 64, "offset_x": 8, "offset_y": 8},
        "hurtbox": {"width": 48, "height": 64, "offset_x": 8, "offset_y": 8},
        "collision_circle": {"radius": 10.5},
    },
    "enemy_ranged": {
        "detection_radius": 280,
        "patrol_radius": 160,
        "attack_radius_key": "attack_range",
        "attack_radius": 260,
        "body_hitbox": {"width": 40, "height": 40, "offset_x": 6, "offset_y": 11},
        "hurtbox": {"width": 40, "height": 40, "offset_x": 7, "offset_y": 10},
        "attack_hitbox": {"width": 16, "height": 14, "offset_x": 18, "offset_y": 13, "mirror_with_facing": True},
        "collision_circle": {"radius": 10},
    },
    "enemy_spider": {
        "detection_radius": 260,
        "patrol_radius": 150,
        "attack_radius_key": "spit_range",
        "attack_radius": 250,
        "body_hitbox": {"width": 20, "height": 16, "offset_x": 6, "offset_y": 12},
        "hurtbox": {"width": 18, "height": 16, "offset_x": 7, "offset_y": 12},
        "attack_hitbox": {"width": 18, "height": 12, "offset_x": 18, "offset_y": 14, "mirror_with_facing": True},
        "collision_circle": {"radius": 10},
    },
    "enemy_beetle": {
        "detection_radius": 230,
        "patrol_radius": 140,
        "attack_radius_key": "charge_range",
        "attack_radius": 210,
        "body_hitbox": {"width": 22, "height": 18, "offset_x": 5, "offset_y": 11},
        "hurtbox": {"width": 20, "height": 18, "offset_x": 6, "offset_y": 11},
        "attack_hitbox": {"width": 20, "height": 14, "offset_x": 18, "offset_y": 13, "mirror_with_facing": True},
        "collision_circle": {"radius": 11},
    },
    "enemy_boss_forest_guardian": {
        "detection_radius": 420,
        "patrol_radius": 80,
        "attack_radius_key": "melee_range",
        "attack_radius": 66,
        "body_hitbox": {"width": 100, "height": 100, "offset_x": 16, "offset_y": 16},
        "hurtbox": {"width": 100, "height": 100, "offset_x": 16, "offset_y": 16},
        "attack_hitbox": {"width": 90, "height": 90, "offset_x": 16, "offset_y": 16, "mirror_with_facing": True},
        "collision_circle": {"radius": 16, "offset_x": 64, "offset_y": 64},
    },
    "boss_forest_guardian": {
        "detection_radius": 420,
        "patrol_radius": 80,
        "attack_radius_key": "melee_range",
        "attack_radius": 66,
        "body_hitbox": {"width": 100, "height": 100, "offset_x": 16, "offset_y": 16},
        "hurtbox": {"width": 100, "height": 100, "offset_x": 16, "offset_y": 16},
        "attack_hitbox": {"width": 90, "height": 90, "offset_x": 16, "offset_y": 16, "mirror_with_facing": True},
        "collision_circle": {"radius": 16, "offset_x": 64, "offset_y": 64},
    },
}

def _load_object_presets():
    presets = []
    if not CATALOGS_DIR.exists():
        return presets
    for path in sorted(CATALOGS_DIR.glob("*.json")):
        raw_entries = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(raw_entries, list):
            raise ValueError(f"Catalog file must contain a list: {path}")
        for entry in raw_entries:
            if not isinstance(entry, dict) or "label" not in entry or "object" not in entry:
                raise ValueError(f"Invalid preset entry in {path}")
            presets.append(entry)
    return presets


OBJECT_PRESETS = _load_object_presets()


class MapObjectEditor(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Map Object Editor")
        self.geometry("1480x900")
        self.minsize(1180, 720)

        self.level_entries = self._find_levels()
        self.level_var = tk.StringVar(value=self.level_entries[0]["label"] if self.level_entries else "")
        self.zoom_var = tk.StringVar(value="1.0")
        self.status_var = tk.StringVar(value="Ready")

        self.level_path = None
        self.objects_path = None
        self.map_data = None
        self.objects = []
        self.selected_object_index = None
        self.selected_preset_index = 0
        self.tile_size = 32
        self.zoom = 1.0
        self.tile_images = []
        self.map_image = None
        self.object_canvas_ids = []
        self.object_sprite_images = []
        self.palette_canvases = {}
        self.palette_images = []
        self.sprite_image_cache = {}
        self.is_panning = False
        self.dragging_object_index = None
        self.drag_offset_tiles = (0, 0)
        self.drag_last_position = None

        self._init_form_vars()
        self._build_ui()
        if self.level_entries:
            self._load_selected_level()

    def _init_form_vars(self):
        self.type_var = tk.StringVar()
        self.name_var = tk.StringVar()
        self.id_var = tk.StringVar()
        self.x_var = tk.StringVar(value="0")
        self.y_var = tk.StringVar(value="0")
        self.width_var = tk.StringVar(value="1")
        self.height_var = tk.StringVar(value="1")
        self.solid_var = tk.BooleanVar(value=False)
        self.enemy_detection_radius_var = tk.StringVar()
        self.enemy_patrol_radius_var = tk.StringVar()
        self.enemy_attack_radius_var = tk.StringVar()
        self.enemy_stationary_var = tk.BooleanVar(value=False)
        self.enemy_body_width_var = tk.StringVar()
        self.enemy_body_height_var = tk.StringVar()
        self.enemy_body_offset_x_var = tk.StringVar()
        self.enemy_body_offset_y_var = tk.StringVar()
        self.enemy_hurt_width_var = tk.StringVar()
        self.enemy_hurt_height_var = tk.StringVar()
        self.enemy_hurt_offset_x_var = tk.StringVar()
        self.enemy_hurt_offset_y_var = tk.StringVar()
        self.enemy_attack_width_var = tk.StringVar()
        self.enemy_attack_height_var = tk.StringVar()
        self.enemy_attack_offset_x_var = tk.StringVar()
        self.enemy_attack_offset_y_var = tk.StringVar()
        self.enemy_attack_mirror_var = tk.BooleanVar(value=True)
        self.enemy_collision_radius_var = tk.StringVar()
        self.enemy_collision_offset_x_var = tk.StringVar()
        self.enemy_collision_offset_y_var = tk.StringVar()

    def _build_ui(self):
        self.columnconfigure(1, weight=1)
        self.rowconfigure(1, weight=1)

        toolbar = ttk.Frame(self, padding=8)
        toolbar.grid(row=0, column=0, columnspan=3, sticky="ew")
        toolbar.columnconfigure(8, weight=1)

        ttk.Label(toolbar, text="Level").grid(row=0, column=0, padx=(0, 4))
        self.level_combo = ttk.Combobox(toolbar, textvariable=self.level_var, values=[e["label"] for e in self.level_entries], width=34, state="readonly")
        self.level_combo.grid(row=0, column=1, padx=2)
        self.level_combo.bind("<<ComboboxSelected>>", lambda _event: self._load_selected_level())
        ttk.Button(toolbar, text="Reload", command=self._load_selected_level).grid(row=0, column=2, padx=(12, 2))
        ttk.Button(toolbar, text="Save", command=self._save_objects).grid(row=0, column=3, padx=2)
        ttk.Label(toolbar, text="Zoom").grid(row=0, column=4, padx=(18, 4))
        ttk.Combobox(toolbar, textvariable=self.zoom_var, values=("0.5", "0.75", "1.0", "1.5", "2.0"), width=6, state="readonly").grid(row=0, column=5, padx=2)
        ttk.Button(toolbar, text="Apply Zoom", command=self._apply_zoom).grid(row=0, column=6, padx=2)
        ttk.Label(toolbar, textvariable=self.status_var).grid(row=0, column=8, sticky="e")

        left = ttk.Frame(self, padding=(8, 0, 4, 8))
        left.grid(row=1, column=0, sticky="ns")
        left.rowconfigure(1, weight=1)
        left.rowconfigure(4, weight=1)

        ttk.Label(left, text="Palette").grid(row=0, column=0, sticky="w")
        self.palette_notebook = ttk.Notebook(left)
        self.palette_notebook.grid(row=1, column=0, sticky="nsew")
        self._build_palette_tabs()

        ttk.Label(left, text="Objects").grid(row=3, column=0, sticky="w", pady=(12, 0))
        self.object_list = tk.Listbox(left, width=30, exportselection=False)
        self.object_list.grid(row=4, column=0, sticky="nsew")
        self.object_list.bind("<<ListboxSelect>>", self._on_object_selected)

        object_buttons = ttk.Frame(left)
        object_buttons.grid(row=5, column=0, sticky="ew", pady=(8, 0))
        ttk.Button(object_buttons, text="Duplicate", command=self._duplicate_object).grid(row=0, column=0, padx=2)
        ttk.Button(object_buttons, text="Delete", command=self._delete_selected_object).grid(row=0, column=1, padx=2)

        canvas_frame = ttk.Frame(self, padding=(4, 0, 4, 8))
        canvas_frame.grid(row=1, column=1, sticky="nsew")
        canvas_frame.columnconfigure(0, weight=1)
        canvas_frame.rowconfigure(0, weight=1)
        self.canvas = tk.Canvas(canvas_frame, background="#141414", highlightthickness=0)
        self.canvas.grid(row=0, column=0, sticky="nsew")
        x_scroll = ttk.Scrollbar(canvas_frame, orient="horizontal", command=self.canvas.xview)
        y_scroll = ttk.Scrollbar(canvas_frame, orient="vertical", command=self.canvas.yview)
        x_scroll.grid(row=1, column=0, sticky="ew")
        y_scroll.grid(row=0, column=1, sticky="ns")
        self.canvas.configure(xscrollcommand=x_scroll.set, yscrollcommand=y_scroll.set)
        self.canvas.bind("<ButtonPress-1>", self._on_canvas_left_press)
        self.canvas.bind("<B1-Motion>", self._on_canvas_left_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_canvas_left_release)
        self.canvas.bind("<Button-3>", self._on_canvas_right_click)
        self.canvas.bind("<ButtonPress-2>", self._on_canvas_pan_start)
        self.canvas.bind("<B2-Motion>", self._on_canvas_pan_move)
        self.canvas.bind("<ButtonRelease-2>", self._on_canvas_pan_end)
        self.canvas.bind("<Motion>", self._on_canvas_motion)

        right = ttk.Frame(self, padding=(4, 0, 8, 8))
        right.grid(row=1, column=2, sticky="nsew")
        right.columnconfigure(0, weight=1)
        right.rowconfigure(2, weight=1)
        form = ttk.LabelFrame(right, text="Object", padding=8)
        form.grid(row=0, column=0, sticky="ew")
        for column in (1, 3):
            form.columnconfigure(column, weight=1)
        self._add_entry(form, "Type", self.type_var, 0, 0)
        self._add_entry(form, "Name", self.name_var, 0, 2)
        self._add_entry(form, "ID", self.id_var, 1, 0)
        ttk.Checkbutton(form, text="Solid", variable=self.solid_var).grid(row=1, column=2, sticky="w")
        self._add_entry(form, "X", self.x_var, 2, 0)
        self._add_entry(form, "Y", self.y_var, 2, 2)
        self._add_entry(form, "Width", self.width_var, 3, 0)
        self._add_entry(form, "Height", self.height_var, 3, 2)

        actions = ttk.Frame(right)
        actions.grid(row=1, column=0, sticky="ew", pady=(8, 0))
        ttk.Button(actions, text="Apply", command=self._apply_form_to_selected).grid(row=0, column=0, padx=2)
        ttk.Button(actions, text="New From Form", command=self._new_from_form).grid(row=0, column=1, padx=2)

        self.enemy_form = ttk.LabelFrame(right, text="Enemy Settings", padding=8)
        self.enemy_form.grid(row=2, column=0, sticky="ew", pady=(8, 0))
        for column in (1, 3):
            self.enemy_form.columnconfigure(column, weight=1)
        self._add_entry(self.enemy_form, "Detect", self.enemy_detection_radius_var, 0, 0)
        self._add_entry(self.enemy_form, "Patrol", self.enemy_patrol_radius_var, 0, 2)
        self._add_entry(self.enemy_form, "Attack", self.enemy_attack_radius_var, 1, 0)
        ttk.Checkbutton(self.enemy_form, text="Stationary", variable=self.enemy_stationary_var).grid(row=1, column=2, sticky="w")
        self._add_entry(self.enemy_form, "Body W", self.enemy_body_width_var, 2, 0)
        self._add_entry(self.enemy_form, "Body H", self.enemy_body_height_var, 2, 2)
        self._add_entry(self.enemy_form, "Body X", self.enemy_body_offset_x_var, 3, 0)
        self._add_entry(self.enemy_form, "Body Y", self.enemy_body_offset_y_var, 3, 2)
        self._add_entry(self.enemy_form, "Hurt W", self.enemy_hurt_width_var, 4, 0)
        self._add_entry(self.enemy_form, "Hurt H", self.enemy_hurt_height_var, 4, 2)
        self._add_entry(self.enemy_form, "Hurt X", self.enemy_hurt_offset_x_var, 5, 0)
        self._add_entry(self.enemy_form, "Hurt Y", self.enemy_hurt_offset_y_var, 5, 2)
        self._add_entry(self.enemy_form, "Atk W", self.enemy_attack_width_var, 6, 0)
        self._add_entry(self.enemy_form, "Atk H", self.enemy_attack_height_var, 6, 2)
        self._add_entry(self.enemy_form, "Atk X", self.enemy_attack_offset_x_var, 7, 0)
        self._add_entry(self.enemy_form, "Atk Y", self.enemy_attack_offset_y_var, 7, 2)
        ttk.Checkbutton(self.enemy_form, text="Mirror attack", variable=self.enemy_attack_mirror_var).grid(row=8, column=0, sticky="w")
        self._add_entry(self.enemy_form, "Coll R", self.enemy_collision_radius_var, 9, 0)
        self._add_entry(self.enemy_form, "Coll X", self.enemy_collision_offset_x_var, 9, 2)
        self._add_entry(self.enemy_form, "Coll Y", self.enemy_collision_offset_y_var, 10, 0)

        props = ttk.LabelFrame(right, text="Properties JSON", padding=8)
        props.grid(row=3, column=0, sticky="nsew", pady=(8, 0))
        props.columnconfigure(0, weight=1)
        props.rowconfigure(0, weight=1)
        self.properties_text = tk.Text(props, width=42, height=20, wrap="none")
        self.properties_text.grid(row=0, column=0, sticky="nsew")
        self._refresh_palette()

    def _add_entry(self, parent, label, variable, row, column):
        ttk.Label(parent, text=label).grid(row=row, column=column, sticky="w", pady=2)
        ttk.Entry(parent, textvariable=variable).grid(row=row, column=column + 1, sticky="ew", padx=(4, 12), pady=2)

    def _build_palette_tabs(self):
        for category_id, title in PALETTE_CATEGORIES:
            tab = ttk.Frame(self.palette_notebook)
            tab.columnconfigure(0, weight=1)
            tab.rowconfigure(0, weight=1)
            canvas = tk.Canvas(tab, width=220, height=250, background="#f3f3f3", highlightthickness=0)
            scrollbar = ttk.Scrollbar(tab, orient="vertical", command=canvas.yview)
            canvas.configure(yscrollcommand=scrollbar.set)
            canvas.grid(row=0, column=0, sticky="nsew")
            scrollbar.grid(row=0, column=1, sticky="ns")
            self.palette_notebook.add(tab, text=title)
            self.palette_canvases[category_id] = canvas

    def _refresh_palette(self):
        self.palette_images = []
        for category_id, canvas in self.palette_canvases.items():
            canvas.delete("all")
            preset_indices = [
                index
                for index, preset in enumerate(OBJECT_PRESETS)
                if self._preset_category(preset) == category_id
            ]
            row_height = 38
            for row, preset_index in enumerate(preset_indices):
                preset = OBJECT_PRESETS[preset_index]
                y = row * row_height
                selected = preset_index == self.selected_preset_index
                fill = "#6aa8f7" if selected else "#ffffff"
                outline = "#2a72c8" if selected else "#c8c8c8"
                tag = f"preset_{preset_index}"
                canvas.create_rectangle(2, y + 2, 214, y + row_height - 2, fill=fill, outline=outline, tags=(tag,))
                icon = self._make_object_preview_photo(preset["object"], (28, 28))
                if icon is not None:
                    self.palette_images.append(icon)
                    canvas.create_image(8, y + 5, anchor="nw", image=icon, tags=(tag,))
                canvas.create_text(42, y + row_height / 2, anchor="w", text=preset["label"], fill="#111111", tags=(tag,))
                canvas.tag_bind(tag, "<Button-1>", lambda _event, index=preset_index: self._select_preset(index))
            canvas.configure(scrollregion=(0, 0, 216, max(row_height, len(preset_indices) * row_height)))

    def _select_preset(self, preset_index):
        self.selected_preset_index = preset_index
        self._refresh_palette()

    def _preset_category(self, preset):
        object_type = str(preset["object"].get("type", ""))
        if object_type.startswith("enemy_boss_") or object_type.startswith("boss_"):
            return "bosses"
        if object_type.startswith("enemy_"):
            return "enemies"
        if object_type == "npc_object":
            return "npc"
        if object_type == "pickable_object":
            return "pickable"
        if object_type == "container_object":
            return "containers"
        if object_type == "gatherable_object":
            return "gatherable"
        if object_type == "solid_object":
            return "solid"
        if object_type == "passable_object":
            return "passable"
        return "zones"

    def _is_enemy_type(self, object_type):
        return str(object_type).startswith("enemy_") or str(object_type).startswith("boss_")

    def _enemy_attack_radius_property_name(self, object_type):
        mapping = {
            "enemy_melee": "melee_range",
            "enemy_boss_forest_guardian": "melee_range",
            "boss_forest_guardian": "melee_range",
            "enemy_ranged": "attack_range",
            "enemy_spider": "spit_range",
            "enemy_beetle": "charge_range",
        }
        return mapping.get(str(object_type))

    def _enemy_defaults(self, object_type):
        return deepcopy(ENEMY_EDITOR_DEFAULTS.get(str(object_type), {}))

    def _resolved_enemy_properties(self, obj):
        object_type = str(obj.get("type", ""))
        properties = obj.get("properties", {})
        if not isinstance(properties, dict):
            properties = {}
        defaults = self._enemy_defaults(object_type)
        resolved = deepcopy(properties)
        if defaults.get("detection_radius") is not None and resolved.get("detection_radius") is None:
            resolved["detection_radius"] = defaults["detection_radius"]
        if defaults.get("patrol_radius") is not None and resolved.get("patrol_radius") is None:
            resolved["patrol_radius"] = defaults["patrol_radius"]
        attack_radius_key = self._enemy_attack_radius_property_name(object_type)
        if attack_radius_key and resolved.get(attack_radius_key) is None and defaults.get("attack_radius") is not None:
            resolved[attack_radius_key] = defaults["attack_radius"]
        for key in ("body_hitbox", "hurtbox", "attack_hitbox", "collision_circle"):
            default_value = defaults.get(key)
            current_value = resolved.get(key)
            if isinstance(default_value, dict):
                merged = deepcopy(default_value)
                if isinstance(current_value, dict):
                    merged.update(current_value)
                resolved[key] = merged
            elif current_value is None and default_value is not None:
                resolved[key] = deepcopy(default_value)
        return resolved

    def _set_enemy_form_state(self, enabled):
        state = "normal" if enabled else "disabled"
        for child in self.enemy_form.winfo_children():
            try:
                child.configure(state=state)
            except tk.TclError:
                continue

    def _apply_enemy_properties_to_form(self, object_type, properties):
        collision_circle = properties.get("collision_circle") if isinstance(properties.get("collision_circle"), dict) else {}
        self.enemy_detection_radius_var.set("" if properties.get("detection_radius") is None else str(properties.get("detection_radius")))
        self.enemy_patrol_radius_var.set("" if properties.get("patrol_radius") is None else str(properties.get("patrol_radius")))
        attack_radius_key = self._enemy_attack_radius_property_name(object_type)
        attack_radius_value = properties.get(attack_radius_key) if attack_radius_key is not None else None
        self.enemy_attack_radius_var.set("" if attack_radius_value is None else str(attack_radius_value))
        self.enemy_stationary_var.set(bool(properties.get("stationary", False)))
        body = properties.get("body_hitbox") if isinstance(properties.get("body_hitbox"), dict) else {}
        hurt = properties.get("hurtbox") if isinstance(properties.get("hurtbox"), dict) else {}
        attack = properties.get("attack_hitbox") if isinstance(properties.get("attack_hitbox"), dict) else {}
        self.enemy_body_width_var.set("" if body.get("width") is None else str(body.get("width")))
        self.enemy_body_height_var.set("" if body.get("height") is None else str(body.get("height")))
        self.enemy_body_offset_x_var.set("" if body.get("offset_x") is None else str(body.get("offset_x")))
        self.enemy_body_offset_y_var.set("" if body.get("offset_y") is None else str(body.get("offset_y")))
        self.enemy_hurt_width_var.set("" if hurt.get("width") is None else str(hurt.get("width")))
        self.enemy_hurt_height_var.set("" if hurt.get("height") is None else str(hurt.get("height")))
        self.enemy_hurt_offset_x_var.set("" if hurt.get("offset_x") is None else str(hurt.get("offset_x")))
        self.enemy_hurt_offset_y_var.set("" if hurt.get("offset_y") is None else str(hurt.get("offset_y")))
        self.enemy_attack_width_var.set("" if attack.get("width") is None else str(attack.get("width")))
        self.enemy_attack_height_var.set("" if attack.get("height") is None else str(attack.get("height")))
        self.enemy_attack_offset_x_var.set("" if attack.get("offset_x") is None else str(attack.get("offset_x")))
        self.enemy_attack_offset_y_var.set("" if attack.get("offset_y") is None else str(attack.get("offset_y")))
        self.enemy_attack_mirror_var.set(bool(attack.get("mirror_with_facing", True)))
        self.enemy_collision_radius_var.set("" if collision_circle.get("radius") is None else str(collision_circle.get("radius")))
        self.enemy_collision_offset_x_var.set("" if collision_circle.get("offset_x") is None else str(collision_circle.get("offset_x")))
        self.enemy_collision_offset_y_var.set("" if collision_circle.get("offset_y") is None else str(collision_circle.get("offset_y")))
        self._set_enemy_form_state(self._is_enemy_type(object_type))

    def _clear_enemy_form(self):
        self.enemy_detection_radius_var.set("")
        self.enemy_patrol_radius_var.set("")
        self.enemy_attack_radius_var.set("")
        self.enemy_stationary_var.set(False)
        self.enemy_body_width_var.set("")
        self.enemy_body_height_var.set("")
        self.enemy_body_offset_x_var.set("")
        self.enemy_body_offset_y_var.set("")
        self.enemy_hurt_width_var.set("")
        self.enemy_hurt_height_var.set("")
        self.enemy_hurt_offset_x_var.set("")
        self.enemy_hurt_offset_y_var.set("")
        self.enemy_attack_width_var.set("")
        self.enemy_attack_height_var.set("")
        self.enemy_attack_offset_x_var.set("")
        self.enemy_attack_offset_y_var.set("")
        self.enemy_attack_mirror_var.set(True)
        self.enemy_collision_radius_var.set("")
        self.enemy_collision_offset_x_var.set("")
        self.enemy_collision_offset_y_var.set("")
        self._set_enemy_form_state(False)

    def _apply_enemy_form_to_properties(self, object_type, properties):
        if not self._is_enemy_type(object_type):
            return
        attack_radius_key = self._enemy_attack_radius_property_name(object_type)
        self._set_or_remove_numeric_property(properties, "detection_radius", self.enemy_detection_radius_var.get())
        self._set_or_remove_numeric_property(properties, "patrol_radius", self.enemy_patrol_radius_var.get())
        if attack_radius_key is not None:
            self._set_or_remove_numeric_property(properties, attack_radius_key, self.enemy_attack_radius_var.get())
        properties["stationary"] = bool(self.enemy_stationary_var.get())
        self._set_or_remove_hitbox_property(
            properties,
            "body_hitbox",
            self.enemy_body_width_var.get(),
            self.enemy_body_height_var.get(),
            self.enemy_body_offset_x_var.get(),
            self.enemy_body_offset_y_var.get(),
        )
        self._set_or_remove_hitbox_property(
            properties,
            "hurtbox",
            self.enemy_hurt_width_var.get(),
            self.enemy_hurt_height_var.get(),
            self.enemy_hurt_offset_x_var.get(),
            self.enemy_hurt_offset_y_var.get(),
        )
        self._set_or_remove_hitbox_property(
            properties,
            "attack_hitbox",
            self.enemy_attack_width_var.get(),
            self.enemy_attack_height_var.get(),
            self.enemy_attack_offset_x_var.get(),
            self.enemy_attack_offset_y_var.get(),
            mirror_with_facing=self.enemy_attack_mirror_var.get(),
        )
        self._set_or_remove_collision_circle_property(
            properties,
            self.enemy_collision_radius_var.get(),
            self.enemy_collision_offset_x_var.get(),
            self.enemy_collision_offset_y_var.get(),
        )

    def _set_or_remove_numeric_property(self, properties, key, value):
        text = str(value).strip()
        if not text:
            properties.pop(key, None)
            return
        numeric = float(text)
        properties[key] = int(numeric) if numeric.is_integer() else numeric

    def _set_or_remove_hitbox_property(self, properties, key, width, height, offset_x, offset_y, mirror_with_facing=None):
        hitbox = {}
        if str(width).strip():
            hitbox["width"] = self._safe_int(width, 0)
        if str(height).strip():
            hitbox["height"] = self._safe_int(height, 0)
        if str(offset_x).strip():
            hitbox["offset_x"] = self._safe_int(offset_x, 0)
        if str(offset_y).strip():
            hitbox["offset_y"] = self._safe_int(offset_y, 0)
        if mirror_with_facing is not None and hitbox:
            hitbox["mirror_with_facing"] = bool(mirror_with_facing)
        elif mirror_with_facing is not None and key == "attack_hitbox":
            hitbox["mirror_with_facing"] = bool(mirror_with_facing)
        if hitbox:
            properties[key] = hitbox
        else:
            properties.pop(key, None)

    def _set_or_remove_collision_circle_property(self, properties, radius, offset_x, offset_y):
        collision_circle = {}
        if str(radius).strip():
            collision_circle["radius"] = float(radius) if "." in str(radius) else self._safe_int(radius, 0)
        if str(offset_x).strip():
            collision_circle["offset_x"] = float(offset_x) if "." in str(offset_x) else self._safe_int(offset_x, 0)
        if str(offset_y).strip():
            collision_circle["offset_y"] = float(offset_y) if "." in str(offset_y) else self._safe_int(offset_y, 0)
        if collision_circle:
            properties["collision_circle"] = collision_circle
        else:
            properties.pop("collision_circle", None)

    def _find_levels(self):
        entries = []
        if not LEVELS_DIR.exists():
            return entries
        for path in sorted(LEVELS_DIR.iterdir()):
            if path.is_dir() and (path / f"{path.name}.tmx").exists():
                entries.append({"label": path.name, "path": path})
            elif path.suffix == ".json":
                entries.append({"label": path.name, "path": path})
        return entries

    def _load_selected_level(self):
        entry = self._selected_level_entry()
        if entry is None:
            return
        self.level_path = entry["path"]
        self.map_data = self._load_map_data(self.level_path)
        self.objects_path = self._resolve_objects_path(self.level_path)
        self.objects = self._load_objects(self.level_path, self.objects_path)
        self.selected_object_index = None
        self.tile_size = int(self.map_data["tile_size"])
        self._render_map()
        self._refresh_object_list()
        self._clear_form()
        self._set_status(f"Loaded {entry['label']}")

    def _selected_level_entry(self):
        label = self.level_var.get()
        for entry in self.level_entries:
            if entry["label"] == label:
                return entry
        return self.level_entries[0] if self.level_entries else None

    def _load_map_data(self, path):
        if path.is_dir():
            return self._load_tmx_map_data(path / f"{path.name}.tmx")
        raw = json.loads(path.read_text(encoding="utf-8"))
        tile_size = int(raw.get("tile_size", 64))
        return {"tile_size": tile_size, "ground_layer": raw["layers"]["ground"], "tileset_image": None, "tileset_firstgid": 1, "tileset_columns": 0, "tileset_tile_width": tile_size, "tileset_tile_height": tile_size}

    def _load_tmx_map_data(self, tmx_path):
        root = ET.fromstring(tmx_path.read_text(encoding="utf-8"))
        width = int(root.attrib["width"])
        tile_width = int(root.attrib["tilewidth"])
        tile_height = int(root.attrib["tileheight"])
        layer = root.find("layer")
        data = layer.find("data") if layer is not None else None
        if data is None or data.attrib.get("encoding") != "csv":
            raise ValueError("Only CSV TMX layers are supported")
        values = [int(value.strip()) for value in (data.text or "").replace("\n", "").split(",") if value.strip()]
        ground_layer = [values[start:start + width] for start in range(0, len(values), width)]
        tileset = root.find("tileset")
        image_path = None
        firstgid = 1
        columns = 0
        if tileset is not None:
            firstgid = int(tileset.attrib.get("firstgid", 1))
            columns = int(tileset.attrib.get("columns", 0))
            image = tileset.find("image")
            if image is not None:
                candidate = (tmx_path.parent / image.attrib.get("source", "")).resolve()
                if candidate.exists() and candidate.suffix.lower() != ".aseprite":
                    image_path = candidate
            fallback = tmx_path.parent / "world_tile_set.png"
            if image_path is None and fallback.exists():
                image_path = fallback
        return {"tile_size": tile_width, "ground_layer": ground_layer, "tileset_image": image_path, "tileset_firstgid": firstgid, "tileset_columns": columns, "tileset_tile_width": tile_width, "tileset_tile_height": tile_height}

    def _resolve_objects_path(self, level_path):
        return level_path / "objects.json" if level_path.is_dir() else level_path

    def _load_objects(self, level_path, objects_path):
        if level_path.is_dir():
            if not objects_path.exists():
                return []
            return json.loads(objects_path.read_text(encoding="utf-8")).get("objects", [])
        return json.loads(level_path.read_text(encoding="utf-8")).get("objects", [])

    def _render_map(self):
        self.canvas.delete("all")
        self.tile_images = []
        self.map_image = None
        layer = self.map_data["ground_layer"]
        rows = len(layer)
        cols = len(layer[0]) if rows else 0
        display_tile_size = max(4, int(self.tile_size * self.zoom))
        tileset_path = self.map_data.get("tileset_image")
        tileset = Image.open(tileset_path).convert("RGBA") if tileset_path else None
        background = Image.new("RGBA", (cols * display_tile_size, rows * display_tile_size), "#141414")
        draw = ImageDraw.Draw(background)
        tile_cache = {}
        for y, row in enumerate(layer):
            for x, gid in enumerate(row):
                left = x * display_tile_size
                top = y * display_tile_size
                if tileset is None or gid <= 0:
                    draw.rectangle((left, top, left + display_tile_size, top + display_tile_size), fill=TILE_COLORS.get(gid, "#888888"))
                    continue
                tile = tile_cache.get(gid)
                if tile is None:
                    tile = self._make_tile_image(tileset, gid, display_tile_size)
                    tile_cache[gid] = tile
                if tile is not None:
                    background.alpha_composite(tile, (left, top))
        self.map_image = ImageTk.PhotoImage(background)
        self.canvas.create_image(0, 0, anchor="nw", image=self.map_image)
        for x in range(cols + 1):
            px = x * display_tile_size
            self.canvas.create_line(px, 0, px, rows * display_tile_size, fill="#000000", width=1)
        for y in range(rows + 1):
            py = y * display_tile_size
            self.canvas.create_line(0, py, cols * display_tile_size, py, fill="#000000", width=1)
        self.canvas.configure(scrollregion=(0, 0, cols * display_tile_size, rows * display_tile_size))
        self._render_objects()

    def _make_tile_image(self, tileset, gid, display_tile_size):
        local_id = gid - int(self.map_data["tileset_firstgid"])
        columns = int(self.map_data.get("tileset_columns") or 0)
        if local_id < 0 or columns <= 0:
            return None
        tile_width = int(self.map_data["tileset_tile_width"])
        tile_height = int(self.map_data["tileset_tile_height"])
        source_x = (local_id % columns) * tile_width
        source_y = (local_id // columns) * tile_height
        if source_x + tile_width > tileset.width or source_y + tile_height > tileset.height:
            return None
        tile = tileset.crop((source_x, source_y, source_x + tile_width, source_y + tile_height))
        if display_tile_size != tile_width:
            tile = tile.resize((display_tile_size, display_tile_size), Image.Resampling.NEAREST)
        return tile

    def _make_object_preview_photo(self, obj, size):
        sprite_info = self._resolve_object_sprite_info(obj)
        if sprite_info is None:
            return None
        sprite_path, frame_width, frame_height = sprite_info
        cache_key = (sprite_path, frame_width, frame_height, int(size[0]), int(size[1]))
        if cache_key in self.sprite_image_cache:
            return self.sprite_image_cache[cache_key]
        image_path = ASSETS_DIR / sprite_path
        if not image_path.exists():
            return None
        image = Image.open(image_path).convert("RGBA")
        if frame_width and frame_height:
            image = image.crop((0, 0, min(frame_width, image.width), min(frame_height, image.height)))
        image.thumbnail((max(1, int(size[0])), max(1, int(size[1]))), Image.Resampling.NEAREST)
        preview = Image.new("RGBA", (max(1, int(size[0])), max(1, int(size[1]))), (0, 0, 0, 0))
        left = (preview.width - image.width) // 2
        top = (preview.height - image.height) // 2
        preview.alpha_composite(image, (left, top))
        photo = ImageTk.PhotoImage(preview)
        self.sprite_image_cache[cache_key] = photo
        return photo

    def _resolve_object_sprite_info(self, obj):
        properties = obj.get("properties", {})
        if not isinstance(properties, dict):
            properties = {}
        object_type = str(obj.get("type", ""))
        name = str(obj.get("name", ""))

        sprite_path = properties.get("sprite_path")
        if sprite_path:
            return str(sprite_path), None, None

        sprite_sheet_path = properties.get("sprite_sheet_path")
        if sprite_sheet_path:
            frame_width = self._safe_int(properties.get("animation_frame_width"), 64)
            frame_height = self._safe_int(properties.get("animation_frame_height"), 64)
            return str(sprite_sheet_path), frame_width, frame_height

        if object_type in ENEMY_PREVIEW_SPRITES:
            return ENEMY_PREVIEW_SPRITES[object_type]

        if object_type == "npc_object":
            npc_id = str(properties.get("npc_id", "")).strip().lower()
            if npc_id == "hermit_mouse" or name.strip().lower() == "hermit mouse":
                return "npc/hermit_mouse/hermit_mouse_idle.png", 64, 64

        if object_type == "checkpoint_object":
            return "world_objects/checkpoint_object/checkpoint_stone_no_active.png", None, None

        if object_type == "container_object":
            container_type = str(properties.get("container_type", "")).strip().lower()
            sprite_path = CONTAINER_SPRITES.get(container_type)
            if sprite_path:
                return sprite_path, None, None

        if object_type == "gatherable_object":
            template_id = str(properties.get("template_id") or properties.get("template") or "").strip().lower()
            sprite_path = GATHERABLE_TEMPLATE_SPRITES.get(template_id)
            if sprite_path:
                return sprite_path, None, None

        if object_type in {"solid_object", "passable_object"}:
            sprite_path = SOLID_OBJECT_SPRITES.get(name.strip().lower())
            if sprite_path:
                return sprite_path, None, None

        if object_type == "grass_hide_zone":
            return "world_objects/grass_hide_zone/big_grass.png", None, None

        if object_type == "pickable_object":
            item_id = str(properties.get("item_id") or name).strip().lower()
            sprite_path = PICKABLE_SPRITES.get(item_id)
            if sprite_path:
                return sprite_path, None, None

        return None

    def _render_objects(self):
        for canvas_id in self.object_canvas_ids:
            self.canvas.delete(canvas_id)
        self.object_canvas_ids = []
        self.object_sprite_images = []
        display_tile_size = max(4, int(self.tile_size * self.zoom))
        for index, obj in enumerate(self.objects):
            x = int(obj.get("x", 0)) * display_tile_size
            y = int(obj.get("y", 0)) * display_tile_size
            width = max(1, int(obj.get("width", 1))) * display_tile_size
            height = max(1, int(obj.get("height", 1))) * display_tile_size
            color = OBJECT_COLORS.get(str(obj.get("type", "object")), "#ffffff")
            outline = "#00ffff" if index == self.selected_object_index else "#111111"
            sprite = self._make_object_preview_photo(obj, (width, height))
            if sprite is not None:
                self.object_sprite_images.append(sprite)
                image_id = self.canvas.create_image(x + width / 2, y + height / 2, image=sprite)
                rect_id = self.canvas.create_rectangle(
                    x + 2,
                    y + 2,
                    x + width - 2,
                    y + height - 2,
                    fill="",
                    outline=outline,
                    width=3 if index == self.selected_object_index else 1,
                )
                self.object_canvas_ids.extend([image_id, rect_id])
            else:
                rect_id = self.canvas.create_rectangle(x + 2, y + 2, x + width - 2, y + height - 2, fill=color, outline=outline, width=3 if index == self.selected_object_index else 2, stipple="" if index == self.selected_object_index else "gray50")
                text_id = self.canvas.create_text(x + width / 2, y + height / 2, text=self._object_short_label(obj), fill="#ffffff", font=("TkDefaultFont", max(7, min(11, display_tile_size // 3)), "bold"))
                self.object_canvas_ids.extend([rect_id, text_id])
        self._render_selected_enemy_debug()

    def _render_selected_enemy_debug(self):
        if self.selected_object_index is None or not (0 <= self.selected_object_index < len(self.objects)):
            return
        obj = self.objects[self.selected_object_index]
        if not self._is_enemy_type(obj.get("type", "")):
            return
        display_tile_size = max(4, int(self.tile_size * self.zoom))
        tile_scale = display_tile_size / max(1, self.tile_size)
        x = int(obj.get("x", 0)) * display_tile_size
        y = int(obj.get("y", 0)) * display_tile_size
        width = max(1, int(obj.get("width", 1))) * display_tile_size
        height = max(1, int(obj.get("height", 1))) * display_tile_size
        properties = self._resolved_enemy_properties(obj)

        body = properties.get("body_hitbox") if isinstance(properties.get("body_hitbox"), dict) else {}
        hurt = properties.get("hurtbox") if isinstance(properties.get("hurtbox"), dict) else {}
        attack = properties.get("attack_hitbox") if isinstance(properties.get("attack_hitbox"), dict) else {}
        collision_circle = properties.get("collision_circle") if isinstance(properties.get("collision_circle"), dict) else {}

        body_rect = self._scaled_enemy_rect(x, y, body, width, height, tile_scale)
        hurt_rect = self._scaled_enemy_rect(x, y, hurt, width, height, tile_scale)
        attack_rect = self._scaled_enemy_rect(x, y, attack, width, height, tile_scale)
        center_x, center_y = self._enemy_zone_center(x, y, width, height, body_rect, collision_circle, tile_scale)

        detection_radius = self._safe_float(properties.get("detection_radius"), 0.0) * tile_scale
        patrol_radius = self._safe_float(properties.get("patrol_radius"), 0.0) * tile_scale
        attack_radius_key = self._enemy_attack_radius_property_name(obj.get("type", ""))
        attack_radius = self._safe_float(properties.get(attack_radius_key), 0.0) * tile_scale if attack_radius_key else 0.0
        collision_radius = self._safe_float(collision_circle.get("radius"), 0.0) * tile_scale

        if patrol_radius > 0:
            self.object_canvas_ids.extend(self._create_canvas_circle(center_x, center_y, patrol_radius, outline="#f7d774", fill="#f7d774", alpha="gray75", width=1))
        if detection_radius > 0:
            self.object_canvas_ids.extend(self._create_canvas_circle(center_x, center_y, detection_radius, outline="#ffb7a8", fill="#ff8a80", alpha="gray50", width=2))
        if attack_radius > 0:
            self.object_canvas_ids.extend(self._create_canvas_circle(center_x, center_y, attack_radius, outline="#ffd180", fill="#ffcc80", alpha="gray75", width=2))
        if collision_radius > 0:
            self.object_canvas_ids.extend(self._create_canvas_circle(center_x, center_y, collision_radius, outline="#80deea", fill="", alpha="", width=2))
        if body_rect is not None:
            self.object_canvas_ids.append(self.canvas.create_rectangle(*body_rect, outline="#00e5ff", width=2))
        if hurt_rect is not None:
            self.object_canvas_ids.append(self.canvas.create_rectangle(*hurt_rect, outline="#6dff8b", width=2))
        if attack_rect is not None:
            self.object_canvas_ids.append(self.canvas.create_rectangle(*attack_rect, outline="#ffb74d", width=2, dash=(4, 2)))

    def _scaled_enemy_rect(self, base_x, base_y, rect_data, fallback_width, fallback_height, scale):
        if not rect_data:
            return None
        rect_width = self._safe_float(rect_data.get("width"), fallback_width / scale) * scale
        rect_height = self._safe_float(rect_data.get("height"), fallback_height / scale) * scale
        rect_x = base_x + self._safe_float(rect_data.get("offset_x"), (fallback_width - rect_width) / max(scale, 0.001) / 2) * scale
        rect_y = base_y + self._safe_float(rect_data.get("offset_y"), (fallback_height - rect_height) / max(scale, 0.001) / 2) * scale
        return (
            rect_x,
            rect_y,
            rect_x + rect_width,
            rect_y + rect_height,
        )

    def _enemy_zone_center(self, base_x, base_y, width, height, body_rect, collision_circle, scale):
        if collision_circle and collision_circle.get("offset_x") is not None and collision_circle.get("offset_y") is not None:
            return (
                base_x + self._safe_float(collision_circle.get("offset_x"), width / scale / 2) * scale,
                base_y + self._safe_float(collision_circle.get("offset_y"), height / scale / 2) * scale,
            )
        if body_rect is not None:
            return ((body_rect[0] + body_rect[2]) / 2, (body_rect[1] + body_rect[3]) / 2)
        return (base_x + width / 2, base_y + height / 2)

    def _create_canvas_circle(self, center_x, center_y, radius, outline, fill, alpha, width):
        if radius <= 0:
            return []
        ids = []
        ids.append(
            self.canvas.create_oval(
                center_x - radius,
                center_y - radius,
                center_x + radius,
                center_y + radius,
                outline=outline,
                width=width,
                fill=fill,
                stipple=alpha,
            )
        )
        return ids

    def _object_short_label(self, obj):
        object_type = str(obj.get("type", ""))
        name = str(obj.get("name", ""))
        labels = {"npc_object": "NPC", "checkpoint_object": "CP", "container_object": "BOX", "level_transition": "GO"}
        if object_type.startswith("enemy_"):
            return "EN"
        return labels.get(object_type, name[:3].upper() if name else object_type[:3].upper())

    def _refresh_object_list(self):
        self.object_list.delete(0, tk.END)
        for index, obj in enumerate(self.objects):
            self.object_list.insert(tk.END, f"{index:03d} {obj.get('type', 'object')} {obj.get('name', '')} ({obj.get('x', 0)}, {obj.get('y', 0)})")
        self._select_object_in_list()
        self._render_objects()

    def _on_preset_selected(self, _event=None):
        selection = self.palette_list.curselection()
        if selection:
            self.selected_preset_index = selection[0]

    def _on_object_selected(self, _event=None):
        selection = self.object_list.curselection()
        if not selection:
            return
        self.selected_object_index = selection[0]
        self._load_object_into_form(self.objects[self.selected_object_index])
        self._render_objects()

    def _load_object_into_form(self, obj):
        self.type_var.set(obj.get("type", ""))
        self.name_var.set(obj.get("name", ""))
        self.id_var.set(obj.get("id", ""))
        self.x_var.set(str(obj.get("x", 0)))
        self.y_var.set(str(obj.get("y", 0)))
        self.width_var.set(str(obj.get("width", 1)))
        self.height_var.set(str(obj.get("height", 1)))
        self.solid_var.set(bool(obj.get("solid", False)))
        properties = obj.get("properties", {})
        if not isinstance(properties, dict):
            properties = {}
        self._apply_enemy_properties_to_form(obj.get("type", ""), self._resolved_enemy_properties(obj))
        self.properties_text.delete("1.0", tk.END)
        self.properties_text.insert("1.0", json.dumps(properties, ensure_ascii=False, indent=2))

    def _clear_form(self):
        self.type_var.set("")
        self.name_var.set("")
        self.id_var.set("")
        self.x_var.set("0")
        self.y_var.set("0")
        self.width_var.set("1")
        self.height_var.set("1")
        self.solid_var.set(False)
        self._clear_enemy_form()
        self.properties_text.delete("1.0", tk.END)
        self.properties_text.insert("1.0", "{}")

    def _select_object_in_list(self):
        self.object_list.selection_clear(0, tk.END)
        if self.selected_object_index is not None and 0 <= self.selected_object_index < self.object_list.size():
            self.object_list.selection_set(self.selected_object_index)
            self.object_list.see(self.selected_object_index)

    def _on_canvas_left_press(self, event):
        tile_x, tile_y = self._event_to_tile(event)
        clicked_index = self._find_object_at_tile(tile_x, tile_y)
        if clicked_index is not None:
            self.selected_object_index = clicked_index
            obj = self.objects[clicked_index]
            self.dragging_object_index = clicked_index
            self.drag_offset_tiles = (
                tile_x - int(obj.get("x", 0)),
                tile_y - int(obj.get("y", 0)),
            )
            self.drag_last_position = (int(obj.get("x", 0)), int(obj.get("y", 0)))
            self._load_object_into_form(self.objects[clicked_index])
            self._refresh_object_list()
            self.canvas.configure(cursor="hand2")
            return
        self._add_preset_at(tile_x, tile_y)

    def _on_canvas_left_drag(self, event):
        if self.dragging_object_index is None or not (0 <= self.dragging_object_index < len(self.objects)):
            return
        tile_x, tile_y = self._event_to_tile(event)
        offset_x, offset_y = self.drag_offset_tiles
        obj = self.objects[self.dragging_object_index]
        new_x = tile_x - offset_x
        new_y = tile_y - offset_y
        new_x, new_y = self._clamp_object_position(obj, new_x, new_y)
        if self.drag_last_position == (new_x, new_y):
            return
        obj["x"] = new_x
        obj["y"] = new_y
        self.drag_last_position = (new_x, new_y)
        if self.selected_object_index == self.dragging_object_index:
            self.x_var.set(str(new_x))
            self.y_var.set(str(new_y))
        self._refresh_object_list()
        self._set_status(f"Moving object to {new_x}, {new_y}")

    def _on_canvas_left_release(self, _event):
        if self.dragging_object_index is not None:
            self._set_status("Object moved")
        self.dragging_object_index = None
        self.drag_last_position = None
        self.canvas.configure(cursor="")

    def _on_canvas_right_click(self, event):
        tile_x, tile_y = self._event_to_tile(event)
        clicked_index = self._find_object_at_tile(tile_x, tile_y)
        if clicked_index is None:
            return
        del self.objects[clicked_index]
        self.selected_object_index = None
        self._refresh_object_list()
        self._set_status("Object deleted")

    def _on_canvas_motion(self, event):
        if self.is_panning or self.dragging_object_index is not None:
            return
        tile_x, tile_y = self._event_to_tile(event)
        self._set_status(f"Tile: {tile_x}, {tile_y} | Objects: {len(self.objects)}")

    def _on_canvas_pan_start(self, event):
        self.is_panning = True
        self.canvas.scan_mark(event.x, event.y)
        self.canvas.configure(cursor="fleur")
        self._set_status("Panning map")

    def _on_canvas_pan_move(self, event):
        if not self.is_panning:
            return
        self.canvas.scan_dragto(event.x, event.y, gain=1)

    def _on_canvas_pan_end(self, _event):
        self.is_panning = False
        self.canvas.configure(cursor="")

    def _event_to_tile(self, event):
        display_tile_size = max(4, int(self.tile_size * self.zoom))
        return int(self.canvas.canvasx(event.x) // display_tile_size), int(self.canvas.canvasy(event.y) // display_tile_size)

    def _clamp_object_position(self, obj, tile_x, tile_y):
        layer = self.map_data.get("ground_layer", []) if self.map_data else []
        rows = len(layer)
        cols = len(layer[0]) if rows else 0
        width = max(1, int(obj.get("width", 1)))
        height = max(1, int(obj.get("height", 1)))
        max_x = max(0, cols - width)
        max_y = max(0, rows - height)
        return max(0, min(int(tile_x), max_x)), max(0, min(int(tile_y), max_y))

    def _find_object_at_tile(self, tile_x, tile_y):
        for index in range(len(self.objects) - 1, -1, -1):
            obj = self.objects[index]
            x = int(obj.get("x", 0))
            y = int(obj.get("y", 0))
            width = max(1, int(obj.get("width", 1)))
            height = max(1, int(obj.get("height", 1)))
            if x <= tile_x < x + width and y <= tile_y < y + height:
                return index
        return None

    def _add_preset_at(self, tile_x, tile_y):
        obj = deepcopy(OBJECT_PRESETS[self.selected_preset_index]["object"])
        obj["x"] = int(tile_x)
        obj["y"] = int(tile_y)
        if "id" in obj:
            obj["id"] = self._unique_object_id(str(obj["id"]))
        self.objects.append(obj)
        self.selected_object_index = len(self.objects) - 1
        self._load_object_into_form(obj)
        self._refresh_object_list()

    def _unique_object_id(self, base):
        existing = {str(obj.get("id", "")) for obj in self.objects}
        if base not in existing:
            return base
        index = 2
        while f"{base}_{index}" in existing:
            index += 1
        return f"{base}_{index}"

    def _apply_form_to_selected(self):
        if self.selected_object_index is None or not (0 <= self.selected_object_index < len(self.objects)):
            messagebox.showwarning("No object", "Select an object first.")
            return False
        obj = self._read_object_from_form()
        if obj is None:
            return False
        self.objects[self.selected_object_index] = obj
        self._refresh_object_list()
        self._set_status("Object applied")
        return True

    def _new_from_form(self):
        obj = self._read_object_from_form()
        if obj is None:
            return
        if "id" in obj:
            obj["id"] = self._unique_object_id(str(obj["id"]))
        self.objects.append(obj)
        self.selected_object_index = len(self.objects) - 1
        self._refresh_object_list()

    def _read_object_from_form(self):
        object_type = self.type_var.get().strip()
        if not object_type:
            messagebox.showerror("Invalid object", "Type is required.")
            return None
        try:
            properties = json.loads(self.properties_text.get("1.0", tk.END).strip() or "{}")
            if not isinstance(properties, dict):
                raise ValueError("properties must be a JSON object")
        except (json.JSONDecodeError, ValueError) as error:
            messagebox.showerror("Invalid properties", str(error))
            return None
        obj = {
            "type": object_type,
            "name": self.name_var.get().strip() or object_type,
            "x": self._safe_int(self.x_var.get(), 0),
            "y": self._safe_int(self.y_var.get(), 0),
            "width": max(1, self._safe_int(self.width_var.get(), 1)),
            "height": max(1, self._safe_int(self.height_var.get(), 1)),
        }
        object_id = self.id_var.get().strip()
        if object_id:
            obj["id"] = object_id
        if self.solid_var.get():
            obj["solid"] = True
        self._apply_enemy_form_to_properties(object_type, properties)
        if properties:
            obj["properties"] = properties
        return obj

    def _duplicate_object(self):
        if self.selected_object_index is None or not (0 <= self.selected_object_index < len(self.objects)):
            return
        obj = deepcopy(self.objects[self.selected_object_index])
        obj["x"] = int(obj.get("x", 0)) + 1
        if "id" in obj:
            obj["id"] = self._unique_object_id(str(obj["id"]))
        self.objects.append(obj)
        self.selected_object_index = len(self.objects) - 1
        self._load_object_into_form(obj)
        self._refresh_object_list()

    def _delete_selected_object(self):
        if self.selected_object_index is None or not (0 <= self.selected_object_index < len(self.objects)):
            return
        del self.objects[self.selected_object_index]
        self.selected_object_index = None
        self._clear_form()
        self._refresh_object_list()

    def _save_objects(self):
        if self.level_path is None or self.objects_path is None:
            return
        if self.selected_object_index is not None:
            if not self._apply_form_to_selected():
                return
        if self.level_path.is_dir():
            self.objects_path.write_text(json.dumps({"objects": self.objects}, ensure_ascii=False, indent=2), encoding="utf-8")
        else:
            raw = json.loads(self.level_path.read_text(encoding="utf-8"))
            raw["objects"] = self.objects
            self.level_path.write_text(json.dumps(raw, ensure_ascii=False, indent=2), encoding="utf-8")
        self._set_status(f"Saved {self.objects_path}")

    def _apply_zoom(self):
        try:
            self.zoom = float(self.zoom_var.get())
        except ValueError:
            self.zoom = 1.0
            self.zoom_var.set("1.0")
        self._render_map()

    def _safe_int(self, value, default=0):
        try:
            return int(float(value))
        except (TypeError, ValueError):
            return default

    def _safe_float(self, value, default=0.0):
        try:
            return float(value)
        except (TypeError, ValueError):
            return default

    def _set_status(self, text):
        self.status_var.set(text)


if __name__ == "__main__":
    MapObjectEditor().mainloop()
