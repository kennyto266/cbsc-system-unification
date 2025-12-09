#!/usr / bin / env python
"""
PDF报告系统基础测试

快速验证PDF报告生成系统的核心功能
"""

import sys
import tempfile
from datetime import datetime
from pathlib import Path

# 添加src目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


def test_basic_pdf_generation():
    """测试基本PDF生成功能"""
    print("\n=== 测试基本PDF生成功能 ===\n")

    # 创建临时文件
    temp_dir = Path(tempfile.mkdtemp())
    output_path = temp_dir / "test_report.pdf"

    try:
        from reports import PDFReportGenerator

        print("1. 创建报告生成器...")
        generator = PDFReportGenerator(
            output_path=output_path, title="量化交易分析报告", author="HK Quant System"
        )
        print("   ✓ 生成器创建成功")

        print("\n2. 添加封面页...")
        generator.add_cover_page(subtitle="2024年度投资组合分析", date=datetime.now())
        print("   ✓ 封面页添加成功")

        print("\n3. 添加章节...")
        generator.add_chapter_title("市场分析", level=1)
        generator.add_section_content(
            title="整体市场环境",
            content="2024年港股市场整体表现平稳，恒生指数全年上涨约10%。",
        )
        print("   ✓ 章节添加成功")

        print("\n4. 生成PDF...")
        result = generator.generate()
        print("   ✓ PDF生成成功")

        # 验证文件
        if result.exists():
            size_kb = result.stat().st_size / 1024
            print("\n5. 验证结果:")
            print(f"   - 文件路径: {result}")
            print(f"   - 文件大小: {size_kb:.2f} KB")
            print("   - 状态: ✓ 文件有效")
            return True
        else:
            print("   ✗ 文件未生成")
            return False

    except Exception as e:
        print(f"\n✗ 测试失败: {e}")
        import traceback

        traceback.print_exc()
        return False

    finally:
        # 清理临时文件
        if output_path.exists():
            output_path.unlink()
        temp_dir.rmdir()


def test_templates():
    """测试模板系统"""
    print("\n=== 测试模板系统 ===\n")

    try:
        from reports import ReportTemplates

        print("1. 创建模板管理器...")
        templates = ReportTemplates()
        print("   ✓ 模板管理器创建成功")

        print("\n2. 列出可用模板...")
        template_list = templates.list_templates()
        print(f"   可用模板 ({len(template_list)}个):")
        for i, template_name in enumerate(template_list, 1):
            print(f"     {i}. {template_name}")

        print("\n3. 测试模板渲染...")
        result = templates.render_template(
            "executive_summary",
            symbol="0700.HK",
            period="2024年",
            total_return=12.5,
            annual_return=11.8,
            max_drawdown=-8.2,
            sharpe_ratio=1.45,
            win_rate=58.3,
            recommendation="buy",
        )

        if "0700.HK" in result:
            print("   ✓ 模板渲染成功")
            print(f"   渲染结果长度: {len(result)} 字符")
            return True
        else:
            print("   ✗ 模板渲染失败")
            return False

    except Exception as e:
        print(f"\n✗ 测试失败: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_chart_manager():
    """测试图表管理器"""
    print("\n=== 测试图表管理器 ===\n")

    try:
        import numpy as np
        import pandas as pd

        from reports import ChartManager

        print("1. 创建图表管理器...")
        chart_manager = ChartManager()
        print("   ✓ 图表管理器创建成功")

        print("\n2. 创建示例数据...")
        dates = pd.date_range("2024 - 01 - 01", periods=10)
        data = pd.DataFrame({"x": dates, "y": np.random.randn(10).cumsum() + 100})
        print(f"   ✓ 数据创建成功: {len(data)} 行")

        print("\n3. 创建折线图...")
        chart_info = chart_manager.create_chart(
            chart_type="line",
            data=data,
            options={
                "x": "x",
                "y": "y",
                "title": "测试折线图",
                "config": {
                    "width": 600,
                    "height": 400,
                    "scale": 1,  # 降低分辨率以加快测试
                },
            },
        )

        print("   ✓ 图表创建成功")
        print(f"   - 图表类型: {chart_info['chart_type']}")
        print(f"   - 图表标题: {chart_info['title']}")

        # 清理图表文件
        chart_manager.cleanup()
        print("   ✓ 图表文件清理完成")

        return True

    except Exception as e:
        print(f"\n✗ 测试失败: {e}")
        import traceback

        traceback.print_exc()
        return False


def main():
    """运行所有测试"""
    print("=" * 60)
    print("PDF报告生成系统 - 基础功能测试")
    print("=" * 60)

    results = []

    # 运行测试
    results.append(("基本PDF生成", test_basic_pdf_generation()))
    results.append(("模板系统", test_templates()))
    results.append(("图表管理器", test_chart_manager()))

    # 输出结果
    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)

    for test_name, result in results:
        status = "✓ 通过" if result else "✗ 失败"
        print(f"{test_name:20s} {status}")

    # 统计
    passed = sum(1 for _, result in results if result)
    total = len(results)
    print(f"\n总计: {passed}/{total} 项测试通过")

    if passed == total:
        print("\n🎉 所有测试通过！")
        return 0
    else:
        print(f"\n⚠️  {total - passed} 项测试失败")
        return 1


if __name__ == "__main__":
    sys.exit(main())
