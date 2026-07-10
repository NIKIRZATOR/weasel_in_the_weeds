# Decor Generation

Для автогенерации декоративных объектов из `TMX` используются свойства тайла в `tileset`.

Минимальные свойства:

- `decor_set` - один набор объектов из каталога.
- `decor_sets` - несколько наборов через запятую. Все объекты из этих наборов объединяются в один пул для выбора.
- `water_decor_set` - отдельный набор для тайлов воды.
- `decor_chance` - шанс генерации на каждом тайле от `0.0` до `1.0`.

Или можно указать конкретный объект:

- `decor_object` - id объекта из `game/objects/solid_object_catalog.json`.

Дополнительно:

- `decor_jitter` - случайный сдвиг в пикселях по `x/y`.
- `decor_offset_x` - фиксированный сдвиг по `x` в пикселях.
- `decor_offset_y` - фиксированный сдвиг по `y` в пикселях.

Готовые наборы:

- `meadow_ground_decor` - луг: цветы, травинки, камешки, кусты.
- `forest_ground_decor` - второй уровень: травинки, камни, валуны, кусты, мало цветов.
- `lake_water_decor` - водные тайлы озера: водные растения/камыши.

Наборы по типам:

- `meadow_flowers`
- `meadow_grass`
- `meadow_pebbles`
- `meadow_bushes`
- `forest_rocks`
- `forest_sparse_flowers`
- `forest_bushes`
- `lake_water_decor`

Каталог объектов:

- `flower_blue`
- `flower_pink`
- `flower_red_white`
- `flower_white`
- `flower_yellow`
- `grass_patch_1`
- `grass_patch_2`
- `grass_patch_3`
- `stone_pile_small`
- `bush_small`
- `bush_small_2`
- `bush_small_3`
- `bush_small_4`
- `bush_small_5`
- `stone_block`
- `water_flower_1`
- `water_flower_2`

Пример для луга:

- `decor_set = meadow_ground_decor`
- `decor_chance = 0.08`
- `decor_jitter = 3`

Пример для луга с несколькими типами отдельно:

- `decor_sets = meadow_flowers, meadow_grass, meadow_pebbles, meadow_bushes`
- `decor_chance = 0.08`

Пример для второго уровня:

- `decor_set = forest_ground_decor`
- `decor_chance = 0.05`

Пример для тайла воды озера:

- `water_decor_set = lake_water_decor`
- `decor_chance = 0.04`
- `decor_jitter = 1`

Пример для каменистого тайла:

- `decor_sets = meadow_pebbles, forest_rocks`
- `decor_chance = 0.06`
