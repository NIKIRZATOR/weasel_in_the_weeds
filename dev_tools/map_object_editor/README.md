# Map Object Editor

Редактор размещает игровые объекты поверх уже готовой карты уровня.

Запускать из корня проекта:

```bash
python dev_tools/map_object_editor/map_object_editor.py
```

Что редактирует:

- для TMX-уровней пишет `levels/<level>/objects.json`;
- для старых JSON-уровней обновляет поле `objects` внутри файла уровня.

Основной порядок работы:

1. Выбрать уровень в поле `Level`.
2. Выбрать объект в `Palette`.
3. Кликнуть по клетке карты, чтобы поставить объект.
4. Выбрать объект в списке или на карте, если нужно изменить поля.
5. Нажать `Apply`, затем `Save`.

Управление:

- ЛКМ по пустой клетке - поставить выбранный объект.
- ЛКМ по объекту - выбрать объект.
- ПКМ по объекту - удалить объект.
- `Duplicate` - создать копию выбранного объекта рядом.
- `Save` - сохранить список объектов уровня.

Сложные настройки объекта редактируются через поле `Properties JSON`.
Palette catalogs:

- `dev_tools/map_object_editor/catalogs/`
- each `*.json` file stores preset entries for the editor palette
- the editor loads all files from that directory on startup
