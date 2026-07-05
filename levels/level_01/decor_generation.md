# Decor Generation

Для автогенерации декоративных объектов из `TMX` используются свойства тайла в `tileset`.

Минимальные свойства:

- `decor_set` - набор объектов из каталога. Сейчас доступны: `grass_decor`, `stone_decor`, `bush_decor`.
- `decor_chance` - шанс генерации на каждом тайле от `0.0` до `1.0`.

Или можно указать конкретный объект:

- `decor_object` - id объекта из `game/objects/solid_object_catalog.json`.

Дополнительно:

- `decor_jitter` - случайный сдвиг в пикселях по `x/y`.
- `decor_offset_x` - фиксированный сдвиг по `x` в пикселях.
- `decor_offset_y` - фиксированный сдвиг по `y` в пикселях.

Каталог объектов:

- `flower_blue`
- `flower_pink`
- `flower_red_white`
- `flower_white`
- `flower_yellow`
- `stone_pile_small`
- `bush_small`
- `bush_small_2`
- `bush_small_3`
- `stone_block`

Пример для травяного тайла:

- `decor_set = grass_decor`
- `decor_chance = 0.08`
- `decor_jitter = 3`

Пример для каменистого тайла:

- `decor_set = stone_decor`
- `decor_chance = 0.06`
