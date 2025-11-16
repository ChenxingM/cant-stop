# 陷阱和遭遇反馈问题诊断指南

## 问题描述
用户报告：所有的陷阱和遭遇的用户反应都没有反馈

## 系统流程

### 正常流程
1. **玩家移动** → `game_engine.move_markers()`
2. **检查事件** → `_check_and_trigger_events()`
3. **触发遭遇** → `_handle_encounter_event()` → `encounter_mgr.trigger_encounter()`
4. **创建pending** → 保存到 `pending_encounters[player_id]`
5. **返回选项** → 玩家收到遭遇描述和选项列表
6. **玩家选择** → 发送选项文本（如"好呀好呀"）
7. **处理选择** → `_handle_encounter_choice()` → `process_encounter_choice()` → `encounter_mgr.process_choice()`
8. **检查pending** → 验证 `player_id in pending_encounters`
9. **匹配选项** → 查找 `choice.name == choice_name`
10. **返回结果** → 返回选择消息和效果

## 可能的问题点

### 1. 消息过滤问题 ✅ 已修复
**症状**: 玩家选择被标记为 `[SKIP]`
**原因**: 选项文本不在关键词列表中
**修复**: 已添加编号格式检测和常见选择关键词

### 2. 没有Pending遭遇
**症状**: 返回"你当前没有待处理的遭遇事件"
**可能原因**:
- 遭遇触发消息没有发送给玩家
- 玩家没有先触发遭遇就直接回复
- Pending状态被意外清除

**检查方法**:
```python
# 查看调试输出
[DEBUG] 玩家 XXX 尝试选择: 好呀好呀, 有pending遭遇: False
# False表示没有pending遭遇
```

### 3. 选项名称不匹配
**症状**: 返回"无效的选择：XXX"
**可能原因**:
- 玩家输入的文本与选项名称不完全匹配
- 多余的空格或标点符号
- 使用了编号（如"1"）而不是选项文本

**检查方法**:
```python
# 遭遇配置中的选项名称
{
  "name": "好呀好呀",  # ← 必须完全匹配
  "type": "positive"
}

# 玩家输入
"好呀好呀"  # ✅ 匹配
"1. 好呀好呀"  # ❌ 不匹配（多了编号）
"好呀"  # ❌ 不匹配（不完整）
```

### 4. 空消息返回
**症状**: `process_choice` 返回 success=True 但消息为空
**可能原因**: 遭遇配置中的 message 字段为空

## 调试步骤

### 步骤1: 检查遭遇触发
当玩家移动到有遭遇的位置时，应该看到：
```
已移动标记到列: [5, 7]

👥 触发遭遇：喵
📖 你在路上遇到了一只喵
💬 "喵喵喵～"

🎭 请选择你的行动：
1. 好呀好呀
2. 还是算了

💡 使用格式：好呀好呀
```

**如果没有看到遭遇消息** → 问题在触发阶段

### 步骤2: 检查日志输出
查找调试日志：
```
[DEBUG] 玩家 29177585 尝试选择: 好呀好呀, 有pending遭遇: True/False
[DEBUG] 处理结果: success=True/False, msg=XXX
```

**如果 has_pending=False** → pending遭遇未创建或被清除
**如果 success=False** → 选择处理失败，查看msg了解原因

### 步骤3: 检查遭遇配置
验证 `config/encounters.json` 中的选项配置：
```json
{
  "喵": {
    "name": "喵",
    "description": "你在路上遇到了一只喵",
    "quote": "喵喵喵～",
    "choices": [
      {
        "name": "好呀好呀",  // ← 确保名称正确
        "type": "positive",
        "message": "你摸了摸喵，获得了5积分",  // ← 确保有消息
        "effect": {
          "type": "score",
          "value": 5
        }
      }
    ]
  }
}
```

## 临时修复建议

### 方案1: 使用编号选择
修改遭遇触发消息，添加编号提示：
```python
# 在 encounter_system.py 的 trigger_encounter 中
for i, choice in enumerate(encounter.choices, 1):
    message += f"{i}. {choice.name}\n"

message += f"\n💡 方式1：输入选项文本（如：{encounter.choices[0].name}）"
message += f"\n💡 方式2：输入编号（如：1）"
```

### 方案2: 添加编号选择处理
```python
# 在 process_choice 中支持编号选择
def process_choice(self, player_id: str, choice_input: str):
    # 尝试作为编号处理
    try:
        choice_index = int(choice_input) - 1
        if 0 <= choice_index < len(encounter.choices):
            selected_choice = encounter.choices[choice_index]
    except ValueError:
        # 作为文本匹配
        for choice in encounter.choices:
            if choice.name == choice_input:
                selected_choice = choice
                break
```

### 方案3: 自动清理过期pending
```python
# 定期清理超过10分钟的pending遭遇
def clean_expired_pending(self):
    now = datetime.now()
    expired = []
    for player_id, pending in self.pending_encounters.items():
        if (now - pending.triggered_at).seconds > 600:
            expired.append(player_id)
    for player_id in expired:
        del self.pending_encounters[player_id]
```

## 常见错误案例

### 案例1: 玩家直接回复选项
```
玩家: 好呀好呀
机器人: 你当前没有待处理的遭遇事件
```
**原因**: 玩家没有先触发遭遇
**解决**: 让玩家先移动到遭遇位置

### 案例2: 选项名称包含特殊字符
```json
{
  "name": "不了，谢谢",  // ← 包含逗号
  "message": "..."
}
```
**问题**: 玩家可能只输入"不了"
**解决**: 使用更简单的选项名称或支持模糊匹配

### 案例3: 消息过长被截断
```python
# 如果遭遇消息很长，可能被QQ截断
message = "..." * 1000  # 超过2000字符
```
**解决**: 限制消息长度或分多条发送

## 推荐的即时测试

### 测试命令序列
```
1. 选择阵营：收养人
2. 轮次开始
3. .r6d6
4. 5,7  （假设移动到有遭遇的位置）
5. （观察是否收到遭遇消息）
6. 好呀好呀  （选择选项）
7. （观察是否收到选择反馈）
```

### 预期输出
```
步骤4:
已移动标记到列: [5, 7]
👥 触发遭遇：喵
📖 你在路上遇到了一只喵
🎭 请选择你的行动：
1. 好呀好呀
2. 还是算了

步骤6:
✨ 你摸了摸喵，获得了5积分
💰 你的积分：120 → 125
```

## 下一步行动

1. **立即**: 检查日志中的DEBUG输出
2. **短期**: 添加编号选择支持（方案2）
3. **中期**: 实现pending状态持久化到数据库
4. **长期**: 添加遭遇状态UI显示（"当前遭遇：XXX"）

---

**最后更新**: 2025-11-16
**状态**: 已添加调试输出，等待用户反馈
