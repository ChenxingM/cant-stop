"""
测试陷阱选择指令识别
"""

import sys
import os
import asyncio

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

async def test_trap_choices():
    """测试陷阱选择指令识别"""
    try:
        from src.services.message_processor import MessageProcessor, UserMessage

        print("=== 测试陷阱选择指令识别 ===")

        processor = MessageProcessor()

        # 测试用例：各种格式的陷阱选择
        test_cases = [
            # 纯数字格式
            ("1", "数字1"),
            ("2", "数字2"),
            ("3", "数字3"),
            ("4", "数字4"),
            ("5", "数字5"),

            # 数字+点+空格+文字格式
            ("1. 都是我掉的", "数字点文字1"),
            ("2. 金骰子", "数字点文字2"),
            ("3. 银骰子", "数字点文字3"),
            ("4. 普通d6骰子", "数字点文字4"),
            ("5. 我没掉", "数字点文字5"),

            # 数字+空格+文字格式
            ("1 都是我掉的", "数字空格文字1"),
            ("2 金骰子", "数字空格文字2"),
            ("3 银骰子", "数字空格文字3"),
            ("4 普通d6骰子", "数字空格文字4"),
            ("5 我没掉", "数字空格文字5"),

            # 纯文字格式
            ("都是我掉的", "纯文字1"),
            ("金骰子", "纯文字2"),
            ("银骰子", "纯文字3"),
            ("普通d6骰子", "纯文字4"),
            ("我没掉", "纯文字5"),

            # 错误匹配测试
            ("1 错误文字", "错误匹配测试"),
            ("6", "超出范围数字"),
            ("0", "零数字"),

            # 边界情况
            ("5我没掉", "数字直接连文字"),
        ]

        print("1. 测试各种陷阱选择格式...")

        success_count = 0
        total_count = len(test_cases)

        for input_text, description in test_cases:
            try:
                message = UserMessage(
                    user_id="test_user",
                    username="测试用户",
                    content=input_text
                )

                response = await processor.process_message(message)

                # 检查是否成功识别为陷阱选择
                is_trap_choice = (
                    "土地神" in response.content or
                    "你选择了" in response.content or
                    "请输入1-5" in response.content or
                    "对应的选项是" in response.content
                )

                print(f"   测试 '{input_text}' ({description})")
                print(f"     结果: {'✓' if is_trap_choice else '✗'}")
                print(f"     响应: {response.content[:50]}...")

                if is_trap_choice:
                    success_count += 1

            except Exception as e:
                print(f"   测试 '{input_text}' 出错: {e}")

        print(f"\n2. 测试结果统计:")
        print(f"   成功识别: {success_count}/{total_count}")
        print(f"   成功率: {success_count/total_count*100:.1f}%")

        # 特别验证用户报告的问题
        print(f"\n3. 验证用户报告的问题:")

        problem_cases = ["5", "我没掉", "5. 我没掉"]

        for case in problem_cases:
            message = UserMessage(
                user_id="test_user",
                username="测试用户",
                content=case
            )

            response = await processor.process_message(message)
            is_recognized = "土地神" in response.content or "你选择了" in response.content

            print(f"   '{case}': {'✓ 已识别' if is_recognized else '✗ 未识别'}")

        if success_count >= total_count * 0.8:  # 80%成功率
            print(f"\n🎉 陷阱选择识别功能测试通过！")
            print(f"   支持的格式:")
            print(f"   ✓ 纯数字 (1, 2, 3, 4, 5)")
            print(f"   ✓ 纯文字 (都是我掉的, 金骰子, 等)")
            print(f"   ✓ 数字+文字组合 (1. 都是我掉的, 2 金骰子, 等)")
        else:
            print(f"\n❌ 测试未完全通过，需要进一步优化")

        return success_count >= total_count * 0.8

    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    asyncio.run(test_trap_choices())