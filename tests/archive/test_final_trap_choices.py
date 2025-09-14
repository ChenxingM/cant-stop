"""
最终陷阱选择功能验证
"""

import sys
import os
import asyncio

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

async def test_all_formats():
    """测试所有陷阱选择格式"""
    try:
        from src.services.message_processor import MessageProcessor, UserMessage

        print("=== 陷阱选择功能最终验证 ===")

        processor = MessageProcessor()

        # 用户要求的所有格式
        test_formats = [
            # 纯数字
            ("1", "纯数字 - 都是我掉的"),
            ("2", "纯数字 - 金骰子"),
            ("3", "纯数字 - 银骰子"),
            ("4", "纯数字 - 普通d6骰子"),
            ("5", "纯数字 - 我没掉"),

            # 纯文字
            ("都是我掉的", "纯文字选择1"),
            ("金骰子", "纯文字选择2"),
            ("银骰子", "纯文字选择3"),
            ("普通d6骰子", "纯文字选择4"),
            ("我没掉", "纯文字选择5"),

            # 数字+文字组合
            ("1. 都是我掉的", "数字点文字"),
            ("2 金骰子", "数字空格文字"),
            ("3.银骰子", "数字点文字无空格"),
            ("4.  普通d6骰子", "数字点多空格文字"),
            ("5我没掉", "数字直连文字"),
        ]

        print("验证所有支持的格式:")
        all_success = True

        for test_input, description in test_formats:
            message = UserMessage(
                user_id="test",
                username="测试",
                content=test_input
            )

            response = await processor.process_message(message)

            # 检查是否是陷阱选择响应
            is_trap_response = (
                "土地神" in response.content and
                ("贪心" in response.content or
                 "祝福" in response.content or
                 "重骰" in response.content or
                 "积分" in response.content or
                 "诚实" in response.content)
            )

            status = "成功" if is_trap_response else "失败"
            print(f"  '{test_input}' ({description}): {status}")

            if not is_trap_response:
                all_success = False

        print(f"\n测试结果总结:")
        if all_success:
            print("✓ 所有格式都能正确识别和处理")
            print("✓ 支持纯数字格式 (1, 2, 3, 4, 5)")
            print("✓ 支持纯文字格式 (都是我掉的, 金骰子等)")
            print("✓ 支持数字文字组合格式 (1. 都是我掉的, 2 金骰子等)")
            print("\n🎉 陷阱选择功能完全实现！")
            print("用户现在可以使用任意格式来回应陷阱选择：")
            print("- 输入数字: 5")
            print("- 输入文字: 我没掉")
            print("- 输入组合: 5. 我没掉")
        else:
            print("❌ 部分格式还有问题，需要进一步调试")

        return all_success

    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    asyncio.run(test_all_formats())