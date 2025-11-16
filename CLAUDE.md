# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Can't Stop (贪骰无厌) is a dice-based board game bot with multiple interfaces (CLI, GUI, QQ bot). Players advance on 16 columns (numbered 3-18) by rolling 6 dice, forming two 3-dice sums, and strategically placing markers. The goal is to reach the top of any 3 columns to win.

## Core Architecture

### Layer Structure
The codebase follows a clean 3-layer architecture:

1. **Core Layer** (`src/core/`) - Game logic engine
   - `game_engine.py`: Core game state machine, handles all game rules, dice rolling, marker movement, win conditions
   - `trap_system.py` + `trap_plugin_system.py`: Trap effects triggered at specific board positions
   - `achievement_system.py` + `achievement_manager.py`: Achievement tracking and rewards
   - `event_system.py`: Event emission and handling system

2. **Service Layer** (`src/services/`) - Business logic orchestration
   - `game_service.py`: Orchestrates between GameEngine and database operations
   - `message_processor.py`: Parses and routes QQ bot messages to game actions

3. **Data Layer** (`src/database/`)
   - `models.py`: SQLAlchemy ORM models (PlayerDB, GameSessionDB, PlayerProgressDB, etc.)
   - `database.py`: Database manager with CRUD operations

### Key Design Patterns

**State Machine Pattern**: The game uses two state enums:
- `GameState` (ACTIVE, COMPLETED, FAILED) - overall session state
- `TurnState` (DICE_ROLL, SELECTING_COLUMNS, END_OF_TURN, WAITING_FOR_CHECKIN) - within-turn state

These states are managed by `GameEngine` and persisted in `GameSessionDB.session_state` and `turn_state`.

**Adapter Pattern**: `message_processor.py` acts as an adapter translating QQ message strings into game service calls. It uses pattern matching and command handlers to route messages.

**Plugin System**: Traps use a plugin architecture - each trap type is a separate class inheriting from `TrapPlugin` (see `src/core/trap_plugin_system.py`). New traps can be added by creating a plugin class and registering it in `config/trap_plugins.json`.

### Critical Game Rules Implementation

**Temporary vs Permanent Markers**:
- Players have 3 temporary markers (`TemporaryMarker`) that move during a turn
- When ending turn voluntarily (`end_turn()`), temporary markers convert to permanent progress (`PlayerProgressDB`)
- If forced to stop (no valid moves + 3 markers placed), all temporary markers are lost

**First Turn Rule**:
- On the first turn of a session (`first_turn=True`), player MUST place exactly 2 markers on 2 different columns
- Enforced in `game_engine.py` `move_markers()` method

**Checkin System**:
- After voluntarily ending turn, player must "checkin" (打卡) before starting next turn
- This represents creating artwork to earn score points back
- State tracked via `needs_checkin` flag in GameSession

## Development Commands

### Running the Game

**CLI Interface** (recommended for development):
```bash
set PYTHONIOENCODING=utf-8  # Windows
python main.py --interface cli

# Demo mode (auto-runs sample commands):
python main.py --interface cli --demo
```

**GUI Interface**:
```bash
set PYTHONIOENCODING=utf-8
python main.py --interface gui
```

**QQ Bot** (using Lagrange OneBot):
```bash
cd src/bots/launchers
python unified_launcher.py --config ../../../config/qq_bot_config.json
```

### Testing

```bash
# Install test dependencies
pip install pytest pytest-asyncio pytest-cov

# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html

# Run specific test file
pytest tests/test_game_engine.py -v
```

Note: As of now, the `tests/` directory is empty. When writing tests, focus on:
- `test_game_engine.py` for core game logic
- `test_game_service.py` for service layer integration
- `test_message_processor.py` for QQ bot message parsing

### Database Operations

**View database**:
```bash
sqlite3 cant_stop.db
.tables
SELECT * FROM players;
SELECT * FROM game_sessions WHERE session_state = 'ACTIVE';
```

**Reset database** (delete and recreate):
```bash
del cant_stop.db  # Windows
# Database will be auto-recreated on next run
```

**Database migrations** (using Alembic):
```bash
alembic revision --autogenerate -m "description"
alembic upgrade head
```

## Configuration System

Configuration is loaded via `src/config/config_manager.py` from `config/default_config.yaml`. Key settings:

- `game.dice_cost`: Score points consumed per dice roll (default: 10)
- `game.max_temporary_markers`: Maximum temporary markers (default: 3)
- `game.win_condition_columns`: Columns needed to win (default: 3)
- `game.score_rewards`: Points earned for different artwork types
- `database.url`: Database connection string

**Loading config in code**:
```python
from src.config.config_manager import get_config
config = get_config()
dice_cost = config.get('game.dice_cost', 10)
```

## QQ Bot Integration

### Message Flow
1. QQ message received → `lagrange_game_bot.py` (WebSocket listener)
2. Message forwarded to → `qq_message_adapter.py` (formats user context)
3. Adapter calls → `MessageProcessor` (parses command)
4. Processor calls → `GameService` (executes game logic)
5. Service calls → `GameEngine` + `DatabaseManager`
6. Response bubbles back up to QQ

### Adding New Commands

Edit `src/services/message_processor.py`:

```python
def _init_handlers(self):
    self.command_handlers.update({
        "your_command": self._handle_your_command,
    })

def _handle_your_command(self, message: UserMessage) -> BotResponse:
    # Implement command logic
    result = self.game_service.your_method(message.user_id, ...)
    return BotResponse(
        content=result[1],  # result is typically (success, message)
        message_type=MessageType.COMMAND
    )
```

### Common Command Patterns
- Game actions: "掷骰", "替换永久棋子", "打卡完毕"
- Score rewards: "领取草图奖励1" (pattern: `领取(\S+?)奖励(\d+)`)
- Queries: "排行榜", "查看当前进度"
- Trap interactions: Use pattern handlers in `_init_handlers()`

## Common Development Tasks

### Adding a New Trap

1. Create trap plugin class in `src/core/trap_plugin_system.py`:
```python
class YourTrapPlugin(TrapPlugin):
    def execute(self, engine, player_id, session, column, position):
        # Implement trap logic
        return "Trap effect message"
```

2. Register in `config/trap_plugins.json`:
```json
{
  "your_trap_name": {
    "class": "YourTrapPlugin",
    "enabled": true
  }
}
```

3. Trap positions are randomly generated by `TrapConfigManager.generate_trap_positions()`

### Adding a New Achievement

1. Define achievement in `config/achievements.json` with trigger conditions
2. Achievement system automatically tracks based on player statistics
3. Achievements are checked after significant game events via `achievement_manager.py`

### Modifying Board Layout

Column lengths are defined in `MapConfig` in `src/models/game_models.py`:
```python
COLUMN_LENGTHS = {
    3: 3, 4: 4, 5: 5, 6: 6, 7: 7, 8: 8, 9: 9,
    10: 10, 11: 10,
    12: 9, 13: 8, 14: 7, 15: 6, 16: 5, 17: 4, 18: 3
}
```

## Important Implementation Details

### Score Management
- `Player.current_score`: Available points for dice rolls and purchases
- `Player.total_score`: Lifetime accumulated score (never decreases)
- Score transactions are logged in `ScoreTransactionDB` for audit trail

### Session Recovery
- Active sessions are persisted in database
- Use `GameService.resume_game(player_id)` to restore state
- All temporary markers and turn state are preserved

### Dice Roll Mechanics
- Always roll exactly 6 dice (simulated as 6 random integers 1-6)
- Results stored in `GameSession.dice_results`
- Players can choose which 3-dice combination to form (validated by `_validate_dice_combination()`)

### God Mode / Admin Panel
- `src/interfaces/god_mode_gui.py`: Admin interface for testing
- `src/interfaces/gm_panel.py`: GM controls within main GUI
- These allow forcing dice results, modifying scores, skipping checkin

## Platform-Specific Notes

**Windows Encoding**: The codebase sets UTF-8 encoding explicitly for Windows:
```python
sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())
```
Always use `set PYTHONIOENCODING=utf-8` when running on Windows.

**Lagrange OneBot Integration**:
- Lagrange.OneBot executable is in `Lagrange.OneBot/bin/Release/net9.0/win-x64/publish/`
- Config files: `appsettings.json`, `device.json`, `keystore.json`
- Bot connects via WebSocket (default: ws://127.0.0.1:8080)

## Faction System

Players choose one of two factions:
- **收养人 (Adopter)** - `Faction.ADOPTER`
- **Aeonreth** - `Faction.AONRETH`

Faction is set during player registration and affects future game mechanics (currently mostly cosmetic but extensible for faction-specific features).