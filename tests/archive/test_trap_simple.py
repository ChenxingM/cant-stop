"""
简单陷阱选择测试
"""

import sys
import os
import asyncio

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

async def test_simple():
    """简单测试"""
    try:
        from src.services.message_processor import MessageProcessor, UserMessage

        print("=== 简单陷阱选择测试 ===")

        processor = MessageProcessor()

        # 测试关键用例
        test_cases = [
            "5",
            "我没掉",
            "5. 我没掉",
            "1",
            "都是我掉的"
        ]

        print("测试陷阱选择识别:")
        success = 0

        for case in test_cases:
            message = UserMessage(
                user_id="test",
                username="测试",
                content=case
            )

            response = await processor.process_message(message)

            # 检查是否包含陷阱选择响应
            is_trap = ("土地神" in response.content or
                      "你选择了" in response.content or
                      "请输入1-5" in response.content)

            print(f"  '{case}': {'成功' if is_trap else '失败'}")

            if is_trap:
                success += 1

        print(f"\n结果: {success}/{len(test_cases)} 成功")

        if success >= len(test_cases):
            print("陷阱选择功能正常工作！")
            return True
        else:
            print("部分功能需要调试")
            return False

    except Exception as e:
        print(f"ERROR: {e}")
        return False

if __name__ == "__main__":
    asyncio.run(test_simple())