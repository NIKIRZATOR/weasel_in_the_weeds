# `dev_tools`

В этой папке находятся вспомогательные редакторы данных проекта.

## Доступные инструменты

- `dialog_editor/` - редактор диалогов.
- `item_recipe_editor/` - редактор предметов и рецептов.
- `map_object_editor/` - редактор объектов на уровне.
- `quest_editor/` - редактор квестов.

## Запуск

Запускать инструменты нужно из корня проекта:

```bash
python dev_tools/dialog_editor/dialogue_editor.py
python dev_tools/item_recipe_editor/item_recipe_editor.py
python dev_tools/map_object_editor/map_object_editor.py
python dev_tools/quest_editor/quest_editor.py
```

## Для чего это нужно

Эти инструменты позволяют быстро обновлять контент без ручного редактирования больших JSON-файлов.
