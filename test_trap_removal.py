"""
测试陷阱清除后不重新生成
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    from src.services.game_service import GameService

    print("=== 测试陷阱清除不重新生成 ===")

    game_service = GameService()

    # 记录初始陷阱数量
    initial_traps = game_service.engine.trap_config.generated_traps.copy()
    initial_count = len(initial_traps)
    print(f"初始陷阱数量: {initial_count}")
    print("初始陷阱位置:")
    for pos, name in initial_traps.items():
        print(f"  {pos}: {name}")

    # 手动设置一个陷阱
    print("\n手动设置陷阱在第10列-第5位...")
    success, message = game_service.set_manual_trap("小小火球术", 10, 5)
    print(f"设置结果: {success}, {message}")

    after_add_traps = game_service.engine.trap_config.generated_traps.copy()
    after_add_count = len(after_add_traps)
    print(f"添加后陷阱数量: {after_add_count}")

    # 清除刚设置的陷阱
    print("\n清除第10列-第5位的陷阱...")
    success, message = game_service.remove_trap_at_position(10, 5)
    print(f"清除结果: {success}, {message}")

    after_remove_traps = game_service.engine.trap_config.generated_traps.copy()
    after_remove_count = len(after_remove_traps)
    print(f"清除后陷阱数量: {after_remove_count}")

    print("清除后陷阱位置:")
    for pos, name in after_remove_traps.items():
        print(f"  {pos}: {name}")

    # 验证结果
    print(f"\n=== 验证结果 ===")
    print(f"初始陷阱数量: {initial_count}")
    print(f"清除后陷阱数量: {after_remove_count}")

    if after_remove_count == initial_count:
        print("✅ 成功！清除陷阱后没有生成新的随机陷阱")
    else:
        print("❌ 失败！清除陷阱后陷阱数量发生了变化")

    # 检查特定位置是否被清除
    if "10_5" not in after_remove_traps:
        print("✅ 成功！指定位置的陷阱已被正确清除")
    else:
        print("❌ 失败！指定位置的陷阱仍然存在")

except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()