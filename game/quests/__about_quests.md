# game/quests

Подсистема квестов теперь хранит отдельный сохраняемый прогресс игрока и больше не опирается только на `story_flags`.

## Что здесь находится

- `models.py` - модели квестов и целей.
- `catalog.py` - загрузка квестов из `levels/<level_key>/quests.json`.
- `levels/<level_key>/quests.json` - уровневой каталог квестов.
- `manager.py` - runtime-логика: статусы, журнал, запись событий прогресса.

## Как устроен прогресс

У игрока есть `Player.quest_progress`.

Формат состояния по квесту:

```json
{
  "quest_id": {
    "started": true,
    "completed": false,
    "objectives": {
      "objective_id": {
        "current": 1,
        "required": 1,
        "completed": true
      }
    }
  }
}
```

Это состояние сохраняется в save-файл вместе с остальным прогрессом.

## Типы целей

Сейчас поддерживаются:

- `event` - явный прогресс по игровым событиям.
- `flag` - цель завершается, если у игрока есть нужный `story_flag`.
- `item` - цель считает количество предметов в инвентаре и сюжетном инвентаре.

Для `event`-целей используются поля:

- `id`
- `kind`
- `text_key`
- `target`
- `required`
- `legacy_flag` - необязательный мост для старых сохранений и старой логики на флагах.

## Откуда берутся события

`QuestManager` подписывается на `Player.quest_event_callback`.

Сейчас событие автоматически отправляется, когда игрок получает новый сюжетный флаг:

- `flag:met_mouse_hermit`
- `flag:entered_forest_edge`
- `flag:entered_dart_forest`
- `flag:boss_defeated`

Это позволяет:

- не дублировать старую сюжетную логику мира;
- хранить отдельный прогресс квестов;
- поддерживать старые сохранения через `legacy_flag`.

## Как редактировать квесты

Источник правды - `levels/<level_key>/quests.json`.

Править его можно:

- вручную;
- через `python dev_tools/quest_editor/quest_editor.py`.
