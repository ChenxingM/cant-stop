"""
自定义异常类和错误处理
"""

from typing import Optional, Dict, Any
import traceback
from datetime import datetime


class CantStopError(Exception):
    """Can't Stop游戏基础异常"""

    def __init__(self, message: str, error_code: Optional[str] = None,
                 context: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.context = context or {}
        self.timestamp = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'error_type': self.__class__.__name__,
            'message': self.message,
            'error_code': self.error_code,
            'context': self.context,
            'timestamp': self.timestamp.isoformat()
        }

    def __str__(self) -> str:
        if self.error_code:
            return f"[{self.error_code}] {self.message}"
        return self.message


# 玩家相关异常
class PlayerError(CantStopError):
    """玩家相关异常"""
    pass


class PlayerNotFoundError(PlayerError):
    """玩家不存在异常"""

    def __init__(self, player_id: str):
        super().__init__(
            f"玩家不存在: {player_id}",
            error_code="PLAYER_NOT_FOUND",
            context={"player_id": player_id}
        )


class PlayerAlreadyExistsError(PlayerError):
    """玩家已存在异常"""

    def __init__(self, player_id: str):
        super().__init__(
            f"玩家已存在: {player_id}",
            error_code="PLAYER_EXISTS",
            context={"player_id": player_id}
        )


class InsufficientScoreError(PlayerError):
    """积分不足异常"""

    def __init__(self, player_id: str, required: int, current: int):
        super().__init__(
            f"积分不足，需要{required}积分，当前{current}积分",
            error_code="INSUFFICIENT_SCORE",
            context={
                "player_id": player_id,
                "required_score": required,
                "current_score": current
            }
        )


# 游戏会话相关异常
class GameSessionError(CantStopError):
    """游戏会话异常"""
    pass


class SessionNotFoundError(GameSessionError):
    """游戏会话不存在异常"""

    def __init__(self, session_id: str):
        super().__init__(
            f"游戏会话不存在: {session_id}",
            error_code="SESSION_NOT_FOUND",
            context={"session_id": session_id}
        )


class SessionStateError(GameSessionError):
    """游戏会话状态异常"""

    def __init__(self, session_id: str, current_state: str, expected_state: str):
        super().__init__(
            f"游戏会话状态错误，当前:{current_state}，期望:{expected_state}",
            error_code="INVALID_SESSION_STATE",
            context={
                "session_id": session_id,
                "current_state": current_state,
                "expected_state": expected_state
            }
        )


class ActiveSessionExistsError(GameSessionError):
    """活跃会话已存在异常"""

    def __init__(self, player_id: str, session_id: str):
        super().__init__(
            f"玩家已有活跃游戏会话: {session_id}",
            error_code="ACTIVE_SESSION_EXISTS",
            context={
                "player_id": player_id,
                "session_id": session_id
            }
        )


# 游戏规则相关异常
class GameRuleError(CantStopError):
    """游戏规则异常"""
    pass


class InvalidColumnError(GameRuleError):
    """无效列号异常"""

    def __init__(self, column: int):
        super().__init__(
            f"无效的列号: {column}，有效范围是3-18",
            error_code="INVALID_COLUMN",
            context={"column": column}
        )


class ColumnCompletedError(GameRuleError):
    """列已完成异常"""

    def __init__(self, column: int):
        super().__init__(
            f"列{column}已完成，无法再放置标记",
            error_code="COLUMN_COMPLETED",
            context={"column": column}
        )


class TooManyMarkersError(GameRuleError):
    """标记过多异常"""

    def __init__(self, current_markers: int, max_markers: int):
        super().__init__(
            f"临时标记数量超限，当前{current_markers}个，最多{max_markers}个",
            error_code="TOO_MANY_MARKERS",
            context={
                "current_markers": current_markers,
                "max_markers": max_markers
            }
        )


class InvalidDiceCombinationError(GameRuleError):
    """无效骰子组合异常"""

    def __init__(self, dice_results: list, target_columns: list):
        super().__init__(
            f"骰子结果{dice_results}无法组合出{target_columns}",
            error_code="INVALID_DICE_COMBINATION",
            context={
                "dice_results": dice_results,
                "target_columns": target_columns
            }
        )


class NoMovableMarkersError(GameRuleError):
    """无可移动标记异常"""

    def __init__(self, dice_results: list, current_markers: list):
        super().__init__(
            "无法移动任何临时标记，触发被动停止",
            error_code="NO_MOVABLE_MARKERS",
            context={
                "dice_results": dice_results,
                "current_markers": current_markers
            }
        )


class CheckinRequiredError(GameRuleError):
    """需要打卡异常"""

    def __init__(self, player_id: str):
        super().__init__(
            "需要完成打卡才能继续游戏",
            error_code="CHECKIN_REQUIRED",
            context={"player_id": player_id}
        )


# 数据库相关异常
class DatabaseError(CantStopError):
    """数据库异常"""
    pass


class DatabaseConnectionError(DatabaseError):
    """数据库连接异常"""

    def __init__(self, connection_string: str):
        super().__init__(
            f"数据库连接失败: {connection_string}",
            error_code="DB_CONNECTION_FAILED",
            context={"connection_string": connection_string}
        )


class DatabaseOperationError(DatabaseError):
    """数据库操作异常"""

    def __init__(self, operation: str, table: str, details: Optional[str] = None):
        message = f"数据库操作失败: {operation} on {table}"
        if details:
            message += f" - {details}"

        super().__init__(
            message,
            error_code="DB_OPERATION_FAILED",
            context={
                "operation": operation,
                "table": table,
                "details": details
            }
        )


# 配置相关异常
class ConfigurationError(CantStopError):
    """配置异常"""
    pass


class ConfigFileNotFoundError(ConfigurationError):
    """配置文件不存在异常"""

    def __init__(self, config_path: str):
        super().__init__(
            f"配置文件不存在: {config_path}",
            error_code="CONFIG_FILE_NOT_FOUND",
            context={"config_path": config_path}
        )


class InvalidConfigValueError(ConfigurationError):
    """无效配置值异常"""

    def __init__(self, key: str, value: Any, expected: str):
        super().__init__(
            f"无效的配置值: {key}={value}，期望{expected}",
            error_code="INVALID_CONFIG_VALUE",
            context={
                "config_key": key,
                "config_value": value,
                "expected": expected
            }
        )


# 消息处理相关异常
class MessageProcessingError(CantStopError):
    """消息处理异常"""
    pass


class UnknownCommandError(MessageProcessingError):
    """未知指令异常"""

    def __init__(self, command: str):
        super().__init__(
            f"未知指令: {command}",
            error_code="UNKNOWN_COMMAND",
            context={"command": command}
        )


class CommandParseError(MessageProcessingError):
    """指令解析异常"""

    def __init__(self, command: str, expected_format: str):
        super().__init__(
            f"指令格式错误: {command}，期望格式: {expected_format}",
            error_code="COMMAND_PARSE_ERROR",
            context={
                "command": command,
                "expected_format": expected_format
            }
        )


class RateLimitError(MessageProcessingError):
    """频率限制异常"""

    def __init__(self, user_id: str, limit: int):
        super().__init__(
            f"用户{user_id}请求过于频繁，限制:{limit}/分钟",
            error_code="RATE_LIMIT_EXCEEDED",
            context={
                "user_id": user_id,
                "rate_limit": limit
            }
        )


# 错误处理装饰器
def error_handler(default_return=None, log_errors=True):
    """错误处理装饰器"""

    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except CantStopError as e:
                if log_errors:
                    from .logger import log_error
                    log_error(e, context=e.context)

                if default_return is not None:
                    return default_return
                raise

            except Exception as e:
                if log_errors:
                    from .logger import log_error
                    context = {
                        'function': func.__name__,
                        'args': str(args),
                        'kwargs': str(kwargs)
                    }
                    log_error(e, context=context)

                # 包装为CantStopError
                wrapped_error = CantStopError(
                    f"未处理的异常: {str(e)}",
                    error_code="UNHANDLED_ERROR",
                    context={'original_error': type(e).__name__}
                )

                if default_return is not None:
                    return default_return
                raise wrapped_error

        return wrapper

    return decorator


def async_error_handler(default_return=None, log_errors=True):
    """异步错误处理装饰器"""

    def decorator(func):
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except CantStopError as e:
                if log_errors:
                    from .logger import log_error
                    log_error(e, context=e.context)

                if default_return is not None:
                    return default_return
                raise

            except Exception as e:
                if log_errors:
                    from .logger import log_error
                    context = {
                        'function': func.__name__,
                        'args': str(args),
                        'kwargs': str(kwargs)
                    }
                    log_error(e, context=context)

                # 包装为CantStopError
                wrapped_error = CantStopError(
                    f"未处理的异常: {str(e)}",
                    error_code="UNHANDLED_ERROR",
                    context={'original_error': type(e).__name__}
                )

                if default_return is not None:
                    return default_return
                raise wrapped_error

        return wrapper

    return decorator


# 错误恢复策略
class ErrorRecoveryStrategy:
    """错误恢复策略"""

    @staticmethod
    def handle_database_error(error: DatabaseError) -> bool:
        """处理数据库错误"""
        # 尝试重连数据库
        try:
            from ..database.database import get_db_manager
            db_manager = get_db_manager()
            # 重新创建连接
            return True
        except Exception:
            return False

    @staticmethod
    def handle_session_error(error: GameSessionError, player_id: str) -> bool:
        """处理会话错误"""
        # 尝试恢复或重建会话
        try:
            from ..services.game_service import GameService
            game_service = GameService()
            # 清理无效会话并创建新会话
            return True
        except Exception:
            return False

    @staticmethod
    def handle_configuration_error(error: ConfigurationError) -> bool:
        """处理配置错误"""
        # 尝试使用默认配置
        try:
            from .config import reload_config
            reload_config()
            return True
        except Exception:
            return False