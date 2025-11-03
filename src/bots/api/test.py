"""
Lagrange Bot 测试脚本
用于测试所有功能
"""

from apis import LagrangeBot, MessageBuilder, GroupMessage, AtUser
import asyncio
from pathlib import Path


# ==================== 配置 ====================

# 测试配置（请修改为你的实际值）
TEST_CONFIG = {
    "ws_url": "ws://127.0.0.1:8080",
    "test_group": 541674420,  # 你的测试群号
    "test_user": 29177585,    # 你的 QQ 号（用于测试 at）
}


# ==================== 测试函数 ====================

async def test_connection():
    """测试 1：连接测试"""
    print("\n" + "="*50)
    print("测试 1：连接测试")
    print("="*50)

    bot = LagrangeBot()

    try:
        await bot.connect()
        print("✅ 连接成功")
        print(f"Bot QQ: {bot.bot_qq}")

        await bot.disconnect()
        print("✅ 断开连接成功")

        return True
    except Exception as e:
        print(f"❌ 连接失败: {e}")
        return False


async def test_send_messages():
    """测试 2：发送各种类型的消息"""
    print("\n" + "="*50)
    print("测试 2：发送消息")
    print("="*50)

    bot = LagrangeBot()
    await bot.connect()

    group_id = TEST_CONFIG["test_group"]
    user_id = TEST_CONFIG["test_user"]

    try:
        # 1. 发送文本
        print("发送纯文本...")
        await bot.send_group_text(group_id, "测试：纯文本消息")
        await asyncio.sleep(1)

        # 2. 发送 at
        print("发送 at 消息...")
        await bot.send_group_at(group_id, user_id, "测试 at")
        await asyncio.sleep(1)

        # 3. 发送 at + 文本
        print("发送 at + 文本...")
        await bot.send_group_at(group_id, user_id, "这是带文本的 at 消息")
        await asyncio.sleep(1)

        # 4. 使用 MessageBuilder
        print("使用 MessageBuilder 发送复杂消息...")
        msg = (MessageBuilder()
               .at(user_id)
               .text(" 测试复杂消息\n")
               .text("✅ 第一行\n")
               .text("✅ 第二行\n")
               .face(178)
               .build())
        await bot.send_group_msg(group_id, msg)
        await asyncio.sleep(1)

        # 5. 发送图片（URL）
        print("发送图片消息...")
        msg = (MessageBuilder()
               .text("测试图片：\n")
               .image("https://picsum.photos/400/300")
               .build())
        await bot.send_group_msg(group_id, msg)
        await asyncio.sleep(1)

        # 6. at 多人
        print("at 多人...")
        msg = (MessageBuilder()
               .at(user_id)
               .text(" ")
               .at(user_id)
               .text(" 测试 at 多人")
               .build())
        await bot.send_group_msg(group_id, msg)

        print("✅ 所有消息发送成功")

    except Exception as e:
        print(f"❌ 发送失败: {e}")
        import traceback
        traceback.print_exc()

    finally:
        await bot.disconnect()


async def test_get_group_info():
    """测试 3：获取群信息"""
    print("\n" + "="*50)
    print("测试 3：获取群信息")
    print("="*50)

    bot = LagrangeBot()
    await bot.connect()

    try:
        # 获取群列表
        print("获取群列表...")
        groups = await bot.get_group_list()
        print(f"✅ 已加入 {len(groups)} 个群:")
        for group in groups[:5]:  # 只显示前 5 个
            print(f"  - {group['group_name']} ({group['group_id']}) | {group['member_count']} 人")

        # 获取指定群信息
        group_id = TEST_CONFIG["test_group"]
        print(f"\n获取群 {group_id} 的信息...")
        group_info = await bot.get_group_info(group_id)
        print(f"✅ 群名：{group_info.get('group_name')}")
        print(f"✅ 成员数：{group_info.get('member_count')}")

        # 获取群成员列表
        print(f"\n获取群 {group_id} 的成员列表...")
        members = await bot.get_group_member_list(group_id)
        print(f"✅ 共 {len(members)} 个成员")
        print("前 5 个成员:")
        for member in members[:5]:
            print(f"  - {member.get('nickname')} ({member.get('user_id')})")

    except Exception as e:
        print(f"❌ 获取信息失败: {e}")
        import traceback
        traceback.print_exc()

    finally:
        await bot.disconnect()


async def test_message_parsing():
    """测试 4：消息解析（at 昵称提取）"""
    print("\n" + "="*50)
    print("测试 4：消息解析和 at 昵称提取")
    print("="*50)
    print("请在群里发送一条 at 消息（at 任何人）...")
    print("等待监听消息...\n")

    bot = LagrangeBot(allowed_groups=[TEST_CONFIG["test_group"]])
    await bot.connect()

    message_received = False

    @bot.on_group_message
    async def test_handler(msg: GroupMessage):
        nonlocal message_received

        print(f"\n{'='*50}")
        print(f"📩 收到消息")
        print(f"{'='*50}")
        print(f"群号: {msg.group_id}")
        print(f"发送者: {msg.sender_nickname} ({msg.user_id})")
        print(f"原始消息: {msg.raw_message}")
        print(f"纯文本: {msg.plain_text}")
        print(f"\n消息段数组:")
        import json
        print(json.dumps(msg.message_array, ensure_ascii=False, indent=2))

        # ✅ 测试 at 列表
        print(f"\nat 列表 (QQ号): {msg.at_list}")

        # ✅ 测试 at 用户列表（带昵称）
        print(f"\nat 用户列表 (带昵称):")
        if msg.at_users:
            for at_user in msg.at_users:
                print(f"  - QQ: {at_user.qq}")
                print(f"    昵称: {at_user.nickname if at_user.nickname else '(未获取到)'}")
                print(f"    字符串表示: {at_user}")
        else:
            print("  (无 at)")

        print(f"\nat 了机器人: {msg.is_at_bot}")
        print(f"{'='*50}\n")

        # 回复测试
        if msg.at_users:
            at_names = ", ".join([str(user) for user in msg.at_users])
            await bot.send_group_msg(
                msg.group_id,
                f"✅ 测试成功！检测到 at 了: {at_names}"
            )

        message_received = True

    # 监听 30 秒
    try:
        await asyncio.wait_for(
            bot.listen(),
            timeout=30.0
        )
    except asyncio.TimeoutError:
        if message_received:
            print("✅ 测试完成")
        else:
            print("⚠️ 超时，未收到测试消息")
    except KeyboardInterrupt:
        print("\n测试中断")
    finally:
        await bot.disconnect()


async def test_keywords_and_commands():
    """测试 5：关键词和命令"""
    print("\n" + "="*50)
    print("测试 5：关键词和命令处理")
    print("="*50)
    print("请在群里发送以下消息进行测试:")
    print("  - 发送 '你好' 测试关键词")
    print("  - 发送 '/ping' 测试命令")
    print("  - 发送 '/hello 张三' 测试带参数的命令")
    print("  - 发送 '/info' 查看消息详情")
    print("\n等待监听...\n")

    bot = LagrangeBot(allowed_groups=[TEST_CONFIG["test_group"]])
    await bot.connect()

    # 关键词测试
    @bot.on_keyword("你好")
    async def on_hello(msg: GroupMessage):
        print(f"✅ 触发关键词 '你好'")
        await bot.send_group_at(msg.group_id, msg.user_id, "你好呀！")

    @bot.on_keyword("测试")
    async def on_test(msg: GroupMessage):
        print(f"✅ 触发关键词 '测试'")
        await bot.send_group_msg(msg.group_id, "收到测试消息！")

    # 命令测试
    @bot.on_command("ping")
    async def cmd_ping(msg: GroupMessage, args):
        print(f"✅ 触发命令 /ping")
        await bot.send_group_msg(msg.group_id, "🏓 Pong!")

    @bot.on_command("hello")
    async def cmd_hello(msg: GroupMessage, args):
        print(f"✅ 触发命令 /hello, 参数: {args}")
        name = args[0] if args else msg.sender_nickname
        await bot.send_group_at(
            msg.group_id,
            msg.user_id,
            f"Hello, {name}!"
        )

    @bot.on_command("info")
    async def cmd_info(msg: GroupMessage, args):
        print(f"✅ 触发命令 /info")
        info_text = f"""
📊 消息详情
发送者: {msg.sender_nickname} ({msg.user_id})
群号: {msg.group_id}
纯文本: {msg.plain_text}
at列表: {msg.at_list}
at机器人: {msg.is_at_bot}
        """.strip()

        await bot.send_group_msg(msg.group_id, info_text)

    # at 机器人测试
    @bot.on_group_message
    async def handle_at_bot(msg: GroupMessage):
        if msg.is_at_bot:
            print(f"✅ 有人 at 了机器人")
            await bot.send_group_at(
                msg.group_id,
                msg.user_id,
                "你 at 我干嘛？有什么可以帮你的吗？"
            )

    # 监听 60 秒
    try:
        await asyncio.wait_for(
            bot.listen(),
            timeout=60.0
        )
    except asyncio.TimeoutError:
        print("\n⏰ 测试时间结束")
    except KeyboardInterrupt:
        print("\n测试中断")
    finally:
        await bot.disconnect()


async def test_all():
    """运行所有测试"""
    print("\n" + "="*60)
    print("🧪 Lagrange Bot 完整测试")
    print("="*60)

    tests = [
        ("连接测试", test_connection),
        ("发送消息测试", test_send_messages),
        ("获取群信息测试", test_get_group_info),
        ("消息解析测试 (at 昵称)", test_message_parsing),
        ("关键词和命令测试", test_keywords_and_commands),
    ]

    for i, (name, test_func) in enumerate(tests, 1):
        print(f"\n▶️  运行测试 {i}/{len(tests)}: {name}")

        try:
            await test_func()
            print(f"✅ {name} 完成\n")
        except Exception as e:
            print(f"❌ {name} 失败: {e}\n")
            import traceback
            traceback.print_exc()

        # 测试间隔
        if i < len(tests):
            print("等待 3 秒后继续下一个测试...")
            await asyncio.sleep(3)

    print("\n" + "="*60)
    print("🎉 所有测试完成！")
    print("="*60)


# ==================== 快速测试菜单 ====================

async def interactive_menu():
    """交互式测试菜单"""
    while True:
        print("\n" + "="*60)
        print("🤖 Lagrange Bot 测试菜单")
        print("="*60)
        print("1. 测试连接")
        print("2. 测试发送消息")
        print("3. 测试获取群信息")
        print("4. 测试消息解析 (at 昵称提取)")
        print("5. 测试关键词和命令")
        print("6. 运行所有测试")
        print("0. 退出")
        print("="*60)

        choice = input("\n请选择测试项 (0-6): ").strip()

        if choice == "0":
            print("👋 再见！")
            break
        elif choice == "1":
            await test_connection()
        elif choice == "2":
            await test_send_messages()
        elif choice == "3":
            await test_get_group_info()
        elif choice == "4":
            await test_message_parsing()
        elif choice == "5":
            await test_keywords_and_commands()
        elif choice == "6":
            await test_all()
        else:
            print("❌ 无效选择，请重新输入")

        input("\n按 Enter 继续...")


# ==================== 主函数 ====================

async def main():
    """主函数"""
    import sys

    # 检查配置
    print("📋 当前测试配置:")
    print(f"  WebSocket URL: {TEST_CONFIG['ws_url']}")
    print(f"  测试群号: {TEST_CONFIG['test_group']}")
    print(f"  测试用户: {TEST_CONFIG['test_user']}")
    print("\n⚠️  请确保配置正确！")

    confirm = input("\n配置正确吗？(y/n): ").strip().lower()
    if confirm != 'y':
        print("\n请修改脚本顶部的 TEST_CONFIG 配置")
        return

    # 运行交互式菜单
    await interactive_menu()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 测试中断，再见！")