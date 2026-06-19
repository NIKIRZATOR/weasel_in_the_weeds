# NPC and dialogues

NPC создаются как объекты уровня с типом `npc_object`.

Диалоги лучше хранить отдельными JSON-файлами в папке `dialogues/`, а в уровне оставлять только ссылку через `properties.dialogue_file`.

NPC:

- находится в `world_objects`;
- имеет `health` и `max_health`;
- является интерактивным объектом;
- не получает урон от обычной атаки игрока, потому что атака игрока сейчас применяется только к списку `enemies`;
- может иметь диалог в `properties.dialogue`.

## Минимальный NPC с отдельным файлом диалога

```json
{
  "type": "npc_object",
  "name": "Hermit Mouse",
  "x": 5,
  "y": 3,
  "width": 1,
  "height": 1,
  "properties": {
    "health": 35,
    "dialogue_file": "hermit_mouse.json"
  }
}
```

Файл будет загружен из:

```text
dialogues/hermit_mouse.json
```

Старый встроенный формат `properties.dialogue` тоже поддерживается, но для больших диалогов лучше использовать отдельные файлы.

## Структура диалога

Формат JSON-файла диалога:

```json
{
  "id": "hermit_mouse",
  "start": "hello",
  "nodes": {
    "hello": {
      "speaker": "npc",
      "text": "Hello, traveler.",
      "next": null
    }
  }
}
```

`start` - id первого узла.

`nodes` - словарь узлов, где ключ это id узла.

Узел может содержать:

- `speaker` - `"npc"` или `"player"`;
- `text` - текст реплики;
- `next` - id следующего узла или `null`, если диалог заканчивается;
- `choices` - варианты ответа;
- `rewards` - награды за попадание в этот узел.

## Линейная реплика

```json
"about": {
  "speaker": "npc",
  "text": "The forest is old, and old things remember.",
  "next": "question"
}
```

## Варианты ответа

```json
"greeting": {
  "speaker": "npc",
  "text": "What do you need?",
  "choices": [
    {
      "text": "Who are you?",
      "next": "about"
    },
    {
      "text": "Goodbye.",
      "next": null
    }
  ]
}
```

В диалоговом окне:

- `Enter`, `Space`, `E` - продолжить или выбрать текущий вариант;
- `W`/`Up` и `S`/`Down` - переключать варианты;
- `1-9` - выбрать вариант по номеру;
- `Esc` - закрыть диалог.

## Награды

Награды выдаются при входе в узел один раз для конкретного NPC.

```json
"gift": {
  "speaker": "npc",
  "text": "Take this. It may help.",
  "rewards": {
    "items": [
      "map",
      {
        "item_id": "stick",
        "quantity": 2
      }
    ],
    "coins": 3,
    "flags": [
      "met_mouse_hermit",
      "has_map"
    ]
  },
  "next": null
}
```

Поддерживается:

- `items` - предметы из `game/items/catalog.py`;
- `coins` - монеты;
- `flags` - сюжетные флаги игрока.

## Где сейчас пример

Пример NPC находится в `levels/level_02.json`: `Hermit Mouse`.

Его диалог лежит отдельно:

```text
dialogues/hermit_mouse.json
```

Он выдает:

- `small_backpack`;
- `map`;
- 3 монеты;
- флаги `met_mouse_hermit` и `has_map`.

## Что можно улучшить позже

- Добавить условия показа вариантов ответа.
- Добавить проверку флагов и предметов внутри узлов.
- Добавить портреты из файлов, а не простые цветные карточки.
- Добавить печать текста по буквам.
- Добавить локализацию текста.
