Отмечать тут что сделано
https://disk.yandex.ru/edit/disk/disk%2FПункты%20для%20сдачи%20игры.xlsx?source=docs

Собрать один цельный вертикальный срез игры:
- 3 рабочие локации;
- 1 NPC с диалогом и наградой;
- 1 крафтовый цикл;
- 1 босс;
- переходы между локациями;
- базовый набор спрайтов и иконок для всего, что видит игрок.

## План На Неделю

### День 1. Заморозить скоуп
- Утвердить финальный маршрут: `луг -> опушка -> дремучий лес -> босс`.
- Убрать или спрятать тестовые сущности из ранних уровней.
- Проверить, что по уровням правильно расставлены:
- чекпоинты;
- переходы;
- NPC;
- трава-укрытия;
- контейнеры;
- враги;
- gatherable-объекты.

### День 2. Довести прогрессию
- Привязать сюжет к флагам.
- После разговора с мышью игрок должен получить:
- `small_backpack`;
- `map`;
- доступ к следующему этапу прогрессии.
- Привязать проходы к нужным условиям.
- Открытие следующего пути после босса должно работать стабильно.

### День 3. Иконки предметов и UI
- Нарисовать и подключить все иконки предметов.
- Нарисовать иконки статус-эффектов.
- Проверить HUD, хотбар, инвентарь, крафт, карту.

### День 4. Спрайты существ и объектов мира
- Нарисовать игрока, NPC, врагов, босса.
- Нарисовать ключевые world objects.
- Нарисовать gatherable-объекты и контейнеры.

### День 5. Сборка локаций
- Привести 3 локации к читаемому виду.
- Развести биомы по визуалу:
- луг;
- опушка;
- дремучий лес;
- боссовая зона.

### День 6. Баланс и багфикс
- Проверить:
- дроп;
- крафт;
- расходники;
- реген;
- переходы;
- диалоги;
- карту;
- босса;
- респавн;
- чекпоинты.

### День 7. Резерв
- Только правки, недостающие иконки, фиксы коллизий, фиксы логики.
- Новые механики не добавлять.

## Обязательно К Сдаче

- 3 рабочие локации с разным визуалом.
- 1 NPC с рабочим диалогом.
- 1 рабочая цепочка прогрессии через флаги.
- 1 рабочий босс.
- 1 открытие прохода после босса.
- Рабочие:
- карта;
- инвентарь;
- хотбар;
- расходники;
- крафт;
- чекпоинты;
- переходы между уровнями.
- Иконки всех предметов, которые видит или использует игрок.
- Спрайты всех врагов и ключевых объектов мира.

## Контент: Персонажи

### Игрок
- Обязательно:
- `idle`
- Желательно:
- `run`
- `attack`
- `dash`
- `hurt`

### NPC
- `Hermit Mouse`

## Контент: Враги

- `melee enemy / goblin grunt`
- `ranged enemy / archer`
- `spider`
- `beetle`
- `forest guardian boss`

## Контент: Предметы

### Валюта
+ `coin`
+ `knowledge_shard`

### Оружие
+ `sword`
- `rusty_knife`
+ `stone_spear`
+ `short_bow`

### Расходники
+ `forest_bandage`
+ `healing_tonic`
+ `healing_infusion`
+ `stamina_tonic`
+ `stamina_infusion`
+ `berry`
+ `mushroom`

### Материалы
+ `stick`
+ `grass_blade`
+ `stone_pebble`
- `seed`
+ `bark`
+ `feather`
- `bone`
+ `beetle_shell`
+ `web`
- `web_wrap`

### Экипировка / аксессуары
- `beetle_charm`

### Квестовые предметы
+ `small_backpack`
+ `map`

## Контент: Объекты Мира

+ `checkpoint stone`
+ `grass hide zone`
+ `container crate`
+ `container chest`
+ `container large chest`
- `pickable object` визуалы предметов на земле
- `level transition` маркер прохода
- `interactable object` если оставляем механику

### Gatherable-объекты
+ `stone_pile_small`
+ `grass_patch_small`
+ `berry_bush_small`
+ `fallen_log_small`
- `bug_remains_small`

## Контент: UI И Эффекты

### Иконки эффектов
- `health_regeneration`
- `stamina_regeneration`
- `armor_increased`
- `damage_increased`
- `slowed`
- `damage_reduced`
- `fatigue`

### UI
- портрет игрока для HUD
- иконка карты
- иконка монет
- иконка осколков знаний
- при наличии времени: полоска босса

## Контент: Окружение По Локациям

### 1. Луг
- трава
- мелкие камни
- берег реки
- вода
- кувшинка
- кусты
- редкие деревья

### 2. Опушка
- тропа
- кусты
- редкие деревья
- переходная растительность
- место встречи с мышью

### 3. Дремучий лес
- большие деревья
- поваленные стволы
- кусты
- ямы
- обрывы
- завал / перегородка у прохода
- зона босса

## Чеклист По Ассетам

### Уже есть
- `assets/characters/player/idle.png`
- `assets/items/consumables/berry.png`

### Нужно добавить обязательно

#### Characters
- `assets/characters/player/run.png` или набор кадров
- `assets/characters/player/attack.png` или набор кадров
- `assets/characters/player/dash.png`
- `assets/characters/player/hurt.png`
- `assets/characters/npc/hermit_mouse.png`

#### Enemies
- `assets/characters/enemies/melee_enemy.png`
- `assets/characters/enemies/ranged_enemy.png`
- `assets/characters/enemies/spider.png`
- `assets/characters/enemies/beetle.png`
- `assets/characters/enemies/forest_guardian.png`

#### Item icons
- `assets/items/currency/coin.png`
- `assets/items/currency/knowledge_shard.png`
- `assets/items/weapons/training_blade.png`
- `assets/items/weapons/rusty_knife.png`
- `assets/items/weapons/stone_spear.png`
- `assets/items/weapons/short_bow.png`
- `assets/items/consumables/forest_bandage.png`
- `assets/items/consumables/healing_tonic.png`
- `assets/items/consumables/healing_infusion.png`
- `assets/items/consumables/stamina_tonic.png`
- `assets/items/consumables/stamina_infusion.png`
- `assets/items/consumables/mushroom.png`
- `assets/items/materials/stick.png`
- `assets/items/materials/grass_blade.png`
- `assets/items/materials/stone_pebble.png`
- `assets/items/materials/seed.png`
- `assets/items/materials/bark.png`
- `assets/items/materials/feather.png`
- `assets/items/materials/bone.png`
- `assets/items/materials/beetle_shell.png`
- `assets/items/materials/web.png`
- `assets/items/materials/web_wrap.png`
- `assets/items/accessories/beetle_charm.png`
- `assets/items/quest/small_backpack.png`
- `assets/items/quest/map.png`

#### Effect icons
- `assets/ui/effects/health_regeneration.png`
- `assets/ui/effects/stamina_regeneration.png`
- `assets/ui/effects/armor_increased.png`
- `assets/ui/effects/damage_increased.png`
- `assets/ui/effects/slowed.png`
- `assets/ui/effects/damage_reduced.png`
- `assets/ui/effects/fatigue.png`

#### World props
- `assets/tiles/props/checkpoint_stone.png`
- `assets/tiles/props/grass_hide_zone.png`
- `assets/tiles/props/crate.png`
- `assets/tiles/props/chest.png`
- `assets/tiles/props/large_chest.png`
- `assets/tiles/props/stone_pile_small.png`
- `assets/tiles/props/grass_patch_small.png`
- `assets/tiles/props/berry_bush_small.png`
- `assets/tiles/props/fallen_log_small.png`
- `assets/tiles/props/bug_remains_small.png`
- `assets/tiles/props/level_transition_marker.png`

## Что Можно Оставить Плейсхолдером

- Сложные анимации всех врагов.
- Уникальные VFX для каждого удара.
- Полноценные push/pull пазлы.
- Продвинутую boss intro/victory sequence.
- Полный набор декоративных тайлов, если базовый биом уже читается.

## Приоритет По Важности

### Критично
- Игрок
- NPC
- Все враги
- Босс
- Все предметы из инвентаря, крафта, дропа и квестов
- Чекпоинт
- Контейнеры
- Gatherable-объекты

### Важно
- Эффекты статусов
- Маркер перехода между уровнями
- Портрет игрока
- Базовые элементы окружения для трех локаций

### Если останется время
- Дополнительные анимации
- Улучшенные эффекты
- Уникальные вариации окружения
- Дополнительные декоративные пропсы

## Финальная Проверка Перед Сдачей

- Все предметы имеют иконки.
- Все враги имеют спрайты.
- Все объекты мира имеют читаемый визуал.
- Карта открывается после получения `map`.
- Мышь выдает `small_backpack` и `map`.
- Крафт работает.
- Расходники работают.
- Чекпоинт меняет точку респавна.
- Игрок скрывается в траве.
- Босс побеждается.
- После босса открывается путь дальше или явно считается завершением вертикального среза.
