# Configuration Directory

This directory contains all configuration files for the Can't Stop Bot project.

## Configuration Files

### game_config.json
Contains all game-related configuration settings:
- **database**: Database connection settings
- **game**: Game mechanics settings (dice cost, markers, rewards)
- **ui**: User interface settings (window title, size, DPI)

### trap_config.json
Contains trap system configuration:
- **trap_positions**: Generated trap positions on the game board
- **manual_traps**: Manually set trap positions

## Usage

The project uses a centralized configuration management system located in `src/config/config_manager.py`.

### Basic Usage

```python
from src.config.config_manager import get_config

# Get database URL
db_url = get_config("game_config", "database.url", "sqlite:///cant_stop.db")

# Get dice cost
dice_cost = get_config("game_config", "game.dice_cost", 10)

# Get window title
title = get_config("game_config", "ui.window_title", "Can't Stop")
```

### Key Benefits

1. **Centralized Configuration**: All settings in one place
2. **Type Safety**: Consistent configuration access
3. **Default Values**: Fallback values for missing settings
4. **Hot Reload**: Configuration can be reloaded without restart
5. **Nested Access**: Support for dot-notation paths (e.g., "database.url")

## Migration from Old System

The project has been migrated from the old YAML-based configuration system to this new JSON-based system for better integration and maintainability.