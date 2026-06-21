# Forest Guardian

`ForestGuardianBoss` находится в [forest_guardian.py](/C:/Users/user/Desktop/vs_code_projects/weasel_in_the_weeds/game/entities/enemies/bosses/forest_guardian.py) и наследуется от `BaseBossEnemy`.

Это первый полноценный босс проекта. Он построен не как обычный `Enemy` с увеличенными статами, а как state-driven противник с фазами, собственными cooldown, телеграфами и набором решений по дистанции до игрока.

## Где подключается

- Загрузка босса из уровня происходит в [game/scenes/game_scene.py](/C:/Users/user/Desktop/vs_code_projects/weasel_in_the_weeds/game/scenes/game_scene.py).
- Поддерживаемые типы объекта уровня:
  - `enemy_boss_forest_guardian`
  - `boss_forest_guardian`
  - `enemy_boss_deer`

То есть в JSON уровня достаточно создать объект одного из этих типов, и `GameScene` создаст `ForestGuardianBoss`.

## Базовые параметры

Параметры по умолчанию задаются в `__init__`:

- `max_health=180`
- `speed=88`
- `damage=12`
- `melee_range=66`
- `charge_range=240`
- `charge_speed=300`
- `attack_cooldown=1.0`
- `detection_radius=420`
- `xp_reward=90`

Важно:

- визуальный размер босса принудительно не меньше `76x64`;
- в уровне эти параметры можно переопределять через `properties`.

## Лут

Таблица дропа:

- `feather`: `2-4`, шанс `1.0`
- `bone`: `1-2`, шанс `0.8`
- `knowledge_shards`: `5`, шанс `1.0`
- `coins`: `14`, шанс `1.0`

После смерти дроп обрабатывается общим кодом сцены, как и у остальных врагов.

## Фазы

У босса две фазы.

### Фаза 1

Доступны:

- ближняя атака;
- таран;
- shockwave, если игрок слишком долго держится рядом.

Поведение:

- подходит к игроку;
- ходит по орбите вокруг игрока;
- отскакивает или уходит в evade;
- не стоит как болванка на месте.

### Фаза 2

Включается при здоровье `<= 50%`.

Дополнительно открывается:

- дальняя атака `spike volley`.

При входе во вторую фазу:

- ставится state `phase_shift`;
- немного сбрасываются cooldown;
- меняется визуальный tint;
- запускается краткий glow.

## Архитектура состояния

Основные поля, которые управляют логикой:

- `phase`
- `action_state`
- `action_timer`
- `combat_cooldowns`
- `strafe_clockwise`
- `proximity_pressure_timer`
- `shockwave_committed`

Основные action-state:

- `idle`
- `orbit`
- `approach`
- `retreat`
- `evade`
- `recover`
- `phase_shift`
- `melee_windup`
- `charge_windup`
- `charge`
- `shockwave_windup`
- `shockwave_burst`
- `spike_windup`
- `spike_volley`

`BaseBossEnemy` даёт:

- фазовую модель;
- action timer;
- per-action cooldown;
- orbit movement;
- evade movement;
- boss HP bar;
- иммунитет к stun/knockback от игрока.

## Важное отличие от обычных врагов

В [base_boss.py](/C:/Users/user/Desktop/vs_code_projects/weasel_in_the_weeds/game/entities/enemies/bosses/base_boss.py) переопределён `apply_hit_reaction()`.

Это значит:

- игрок наносит боссу урон;
- hit flash остаётся;
- но атаки игрока не станят босса;
- не толкают его;
- не сбивают его текущий action-state.

То есть `ЛКМ/ПКМ/charged` не ломают charge, spike volley, shockwave и другие действия босса.

## Хитбоксы

### Body hitbox

Используется для коллизии и базовой физики:

- `width=48`
- `height=34`
- `offset_x=14`
- `offset_y=24`

### Hurtbox

Используется, когда игрок наносит урон боссу:

- `width=44`
- `height=30`
- `offset_x=16`
- `offset_y=23`

### Attack hitbox

Используется для направленных контактных атак босса:

- `width=28`
- `height=20`
- `offset_x=44`
- `offset_y=22`
- `mirror_with_facing=True`

### Collision circle

Используется для circle-based distance calculation:

- `radius=16`
- `offset_x=38`
- `offset_y=41`

## Логика принятия решений

Каждый апдейт босс:

1. обновляет таймеры;
2. обновляет свои projectiles;
3. считает дистанцию до игрока;
4. накапливает pressure по близости;
5. проверяет, не пора ли запускать shockwave;
6. если уже находится в конкретном action-state, продолжает именно его;
7. если нет, принимает новое решение по дистанции и cooldown.

### Движение по дистанции

Если игрок далеко:

- босс идёт `approach`.

Если игрок слишком близко:

- босс уходит в `retreat`.

Если дистанция средняя:

- босс двигается по орбите вокруг игрока.

Это делается через `move_orbit(...)` и `move_evade(...)` из `BaseBossEnemy`.

## Evade

Если игрок атакует рядом и не началось накопление под shockwave:

- босс может уйти в `evade`;
- это короткое уклонение;
- направление strafe выбирается случайно;
- cooldown уклонения: `2.2`.

Важно:

- если `proximity_pressure_timer > 0`, evade не включается;
- это сделано специально, чтобы атаки игрока не сбивали накопление shockwave.

## Ближняя атака

State:

- `melee_windup`

Поведение:

- босс смотрит на игрока;
- немного подшагивает;
- после windup активирует `attack_hitbox`;
- если игрок пересёкся с attack hitbox, получает урон.

Текущие цифры:

- windup: `0.22`
- active hitbox duration: `0.12`
- cooldown после удара: `1.35`
- затем `recover` на `0.34`

Урон:

- `self.damage`

## Таран

States:

- `charge_windup`
- `charge`

### Charge windup

Во время подготовки:

- босс фиксирует направление на игрока;
- немного двигается по орбите;
- рисует длинный телеграф-линии.

После подготовки:

- запоминает направление;
- включает attack hitbox;
- переходит в `charge`.

### Charge

Во время тарана:

- босс летит по `charge_direction`;
- использует `charge_speed * charge_speed_multiplier`;
- наносит урон при контакте;
- после попадания или завершения времени уходит в `recover`.

Текущие цифры:

- `charge_range = 240`
- `charge_speed = 300`
- `charge_speed_multiplier = 1.3`
- `charge_duration = 0.62 * 1.5 = 0.93`
- `charge cooldown = 3.2`
- `recover = 0.52`

Урон:

- `int(self.damage * 1.5)`

## Shockwave

Это anti-facehug механика.

Если игрок слишком долго стоит рядом с боссом, босс вызывает волну отталкивания.

### Что считается "слишком долго рядом"

Поля:

- `shockwave_trigger_radius = 130.0`
- `shockwave_trigger_time = 1.5`

Логика:

- пока игрок в этом радиусе, растёт `proximity_pressure_timer`;
- если выходит, таймер постепенно спадает;
- если таймер достиг порога, босс коммитит shockwave.

### Важные детали shockwave

- Если волна уже начала заряжаться, используется `shockwave_committed = True`.
- После этого выход игрока из радиуса уже не отменяет волну.
- Атаки игрока тоже не сбивают накопление и не уводят босса в `evade`.

### Когда shockwave может прерывать другие состояния

Shockwave имеет высокий приоритет и может влезать поверх:

- `recover`
- `evade`
- `orbit`
- `approach`
- `retreat`
- `melee_windup`
- `spike_windup`

Но не прерывает:

- `charge`
- `charge_windup`
- `shockwave_windup`
- `shockwave_burst`
- `spike_volley`

### Shockwave windup

State:

- `shockwave_windup`

Во время подготовки:

- босс разворачивается к игроку;
- рисуется видимая боевая волна;
- сама атака уже гарантированно дойдёт до burst.

Текущая длительность:

- `shockwave_windup_duration = 0.24`

### Shockwave burst

State:

- `shockwave_burst`

Во время burst:

- проверяется расстояние до игрока;
- если игрок внутри радиуса волны, он получает урон, stun и knockback.

Поля:

- `shockwave_radius = 130.0`
- `shockwave_burst_duration = 0.12`
- cooldown после применения: `4.8`

Эффекты по игроку:

- урон: `int(self.damage * 1.25)`
- force: `2300.0`
- stun: `0.65`

После завершения:

- `shockwave_committed` сбрасывается;
- босс уходит в `recover` на `0.36`.

## Spike Volley

Доступна только во второй фазе.

States:

- `spike_windup`
- `spike_volley`

### Windup

- босс смотрит на игрока;
- немного ходит по орбите;
- затем запускает volley.

Текущая длительность:

- `0.5`

### Volley

Босс делает `3` залпа.

Каждый залп выпускает `3` шипа:

- один прямо;
- один на `-30` градусов;
- один на `+30` градусов.

Текущие параметры:

- `volley_shots_remaining = 3`
- `volley_burst_timer = 0.26`
- `volley_spread_degrees = 30.0`
- скорость шипов: `280`
- радиус шипа: `6`
- урон шипа: `max(4, int(self.damage * 0.7))`
- cooldown после volley: `4.4`
- затем `recover = 0.4`

Шипы создаются как `SpikeProjectile`.

## Recover

После большинства действий босс входит в `recover`.

Поведение в recover:

- в первой фазе чаще отходит;
- во второй фазе чаще продолжает орбиту.

Это создаёт ощущение, что босс не просто бьёт по таймеру, а меняет давление на игрока между фазами.

## Визуальные телеграфы

У босса есть два типа визуала.

### Игровые телеграфы

Они видны всегда и не зависят от debug-флагов:

- линия charge;
- круг spike windup;
- shockwave telegraph.

Это часть честного геймплея.

### Debug-радиусы

Они зависят от:

- `DEV_MODE`
- `DEBUG_SHOW_ENEMY_ATTACK_RADII`
- `SHOW_ENEMY_ATTACK_RADII`

Под этот флаг сейчас попадает:

- proximity ring вокруг босса;
- общие служебные радиусы из базового `Enemy`.

То есть в плейтест-сборке можно скрыть debug-круги, но оставить боевые телеграфы.

## Проигрывание волн и projectiles

У босса есть собственный список:

- `self.projectiles`

Он обновляется в `_update_projectiles(...)` и рисуется в `draw(...)`.

Сейчас туда попадают только `SpikeProjectile`.

## XP и смерть

После смерти:

- босс исчезает как обычный enemy;
- сцена выдаёт `xp_reward`;
- спавнится лут по `LOOT_TABLE`.

## Что тюнить в первую очередь

Если босс кажется слишком слабым или слишком душным, в первую очередь имеет смысл тюнить:

- `shockwave_trigger_radius`
- `shockwave_trigger_time`
- `shockwave_radius`
- `shockwave_windup_duration`
- `charge_duration`
- `charge_speed_multiplier`
- `volley_burst_timer`
- `volley_spread_degrees`
- `damage`
- `recover`-тайминги

## Коротко по дизайну

Forest Guardian сейчас играет роль босса, который:

- наказывает за слишком долгий facehug;
- в первой фазе давит телом и тараном;
- во второй фазе начинает держать пространство за счёт шипов;
- не ломается от спама атак игрока;
- имеет читаемые телеграфы и понятные окна опасности.
