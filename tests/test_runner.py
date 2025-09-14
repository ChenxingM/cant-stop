"""
测试运行器
统一运行所有测试套件
"""

import sys
import os

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from test_core_functionality import CoreFunctionalityTests
from test_integration import IntegrationTests


def run_all_tests():
    """运行所有测试套件"""
    print("启动 Can't Stop Bot 测试套件")
    print("=" * 50)

    test_suites = [
        ("核心功能测试", CoreFunctionalityTests),
        ("集成测试", IntegrationTests),
    ]

    total_passed = 0
    total_suites = len(test_suites)

    for suite_name, suite_class in test_suites:
        print(f"\n运行 {suite_name}...")
        print("-" * 30)

        try:
            suite_instance = suite_class()
            if suite_instance.run_all_tests():
                total_passed += 1
                print(f"✓ {suite_name} 全部通过")
            else:
                print(f"X {suite_name} 部分失败")
        except Exception as e:
            print(f"! {suite_name} 执行异常: {e}")

    print("\n" + "=" * 50)
    print(f"测试套件总结:")
    print(f"通过的测试套件: {total_passed}/{total_suites}")

    if total_passed == total_suites:
        print("所有测试套件通过！项目状态良好。")
        return True
    else:
        print("⚠️  部分测试套件失败，需要检查相关功能。")
        return False


def run_specific_test(test_name):
    """运行特定测试"""
    test_mapping = {
        "core": ("核心功能测试", CoreFunctionalityTests),
        "integration": ("集成测试", IntegrationTests),
    }

    if test_name not in test_mapping:
        print(f"❌ 未知的测试名称: {test_name}")
        print(f"可用的测试: {', '.join(test_mapping.keys())}")
        return False

    suite_name, suite_class = test_mapping[test_name]
    print(f"运行 {suite_name}...")

    try:
        suite_instance = suite_class()
        return suite_instance.run_all_tests()
    except Exception as e:
        print(f"! 测试执行异常: {e}")
        return False


if __name__ == "__main__":
    if len(sys.argv) > 1:
        test_name = sys.argv[1]
        run_specific_test(test_name)
    else:
        run_all_tests()