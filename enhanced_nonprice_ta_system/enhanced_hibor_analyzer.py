"""
Enhanced Non-Price TA System - Main Analyzer
增强非价格技术分析系统主程序

集成功能:
1. 数据收集与验证
2. 时间对齐系统
3. 智能指标适配
4. 技术指标计算
5. 参数优化
"""

import pandas as pd
import numpy as np
import json
from datetime import datetime
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

# 导入核心模块
from core.data_alignment_manager import DataAlignmentManager
from core.intelligent_indicator_selector import IntelligentIndicatorSelector
from core.enhanced_data_collector import EnhancedDataCollector

class EnhancedHIBORAnalyzer:
    """增强HIBOR分析器 - 统一的主分析接口"""

    def __init__(self, cache_dir: str = "enhanced_hibor_data"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)

        # 初始化核心组件
        self.data_collector = EnhancedDataCollector(cache_dir)
        self.alignment_manager = DataAlignmentManager()
        self.indicator_selector = IntelligentIndicatorSelector()

        # 数据存储
        self.raw_data = {}
        self.aligned_data = None
        self.indicator_recommendations = {}

        print("🚀 增强HIBOR分析器初始化完成")

    def run_complete_analysis(self, test_data_collection: bool = True,
                            collect_historical: bool = True) -> dict:
        """运行完整分析流程"""
        print("🎯 启动增强HIBOR分析系统")
        print("=" * 80)

        analysis_results = {
            'start_time': datetime.now(),
            'stages': {}
        }

        # 阶段1: 数据源能力测试
        if test_data_collection:
            print("\n📊 阶段1: 数据源能力测试")
            print("-" * 50)
            capabilities = self.data_collector.test_all_sources_capability()
            analysis_results['stages']['data_capabilities'] = capabilities

            # 保存能力报告
            self._save_capabilities_report(capabilities)

        # 阶段2: 历史数据收集
        if collect_historical:
            print("\n📊 阶段2: 历史数据收集")
            print("-" * 50)

            # 加载现有数据或收集新数据
            self.raw_data = self._load_or_collect_data()

            if self.raw_data:
                analysis_results['stages']['data_collection'] = {
                    'sources_count': len(self.raw_data),
                    'total_records': sum(len(df) for df in self.raw_data.values())
                }

                # 保存原始数据摘要
                self._save_data_summary()

        # 阶段3: 数据对齐
        if self.raw_data:
            print("\n📊 阶段3: 数据时间对齐")
            print("-" * 50)

            try:
                aligned_result = self.alignment_manager.align_datasets(self.raw_data)
                self.aligned_data = aligned_result.data

                analysis_results['stages']['data_alignment'] = {
                    'aligned_records': len(self.aligned_data),
                    'alignment_quality': aligned_result.alignment_report
                }

                # 保存对齐后的数据
                self._save_aligned_data()

            except Exception as e:
                print(f"❌ 数据对齐失败: {str(e)}")
                analysis_results['stages']['data_alignment'] = {'error': str(e)}

        # 阶段4: 智能指标选择
        if self.aligned_data is not None and not self.aligned_data.empty:
            print("\n📊 阶段4: 智能指标适配")
            print("-" * 50)

            try:
                # 为每个数据源推荐指标
                for source_name in self.raw_data.keys():
                    if source_name in self.raw_data:
                        print(f"\n🔍 分析数据源: {source_name}")

                        # 使用原始数据进行指标推荐
                        recommendations = self.indicator_selector.select_indicators(
                            self.raw_data[source_name], top_n=3
                        )
                        self.indicator_recommendations[source_name] = recommendations

                        # 保存推荐结果
                        self._save_indicator_recommendations(source_name, recommendations)

                analysis_results['stages']['indicator_selection'] = {
                    'analyzed_sources': len(self.indicator_recommendations),
                    'total_recommendations': sum(len(recs) for recs in self.indicator_recommendations.values())
                }

            except Exception as e:
                print(f"❌ 指标选择失败: {str(e)}")
                analysis_results['stages']['indicator_selection'] = {'error': str(e)}

        # 生成最终报告
        analysis_results['end_time'] = datetime.now()
        analysis_results['duration'] = (analysis_results['end_time'] - analysis_results['start_time']).total_seconds()

        self._generate_final_report(analysis_results)

        return analysis_results

    def _load_or_collect_data(self) -> dict:
        """加载现有数据或收集新数据"""
        data = {}

        # 检查是否有已收集的数据
        data_files = list(self.cache_dir.glob("historical_data_*.parquet"))

        if data_files:
            print(f"📁 发现 {len(data_files)} 个现有数据文件，尝试加载...")

            for file_path in data_files:
                try:
                    # 从文件名提取数据源key
                    filename = file_path.stem
                    source_key = filename.replace("historical_data_", "").split("_")[0]

                    df = pd.read_parquet(file_path)
                    data[source_key] = df
                    print(f"  ✅ 加载 {source_key}: {len(df)} 条记录")

                except Exception as e:
                    print(f"  ❌ 加载失败 {file_path}: {str(e)}")

            if data:
                print(f"📊 成功加载 {len(data)} 个数据源")
                return data

        # 如果没有现有数据，执行收集
        print("🔄 未发现现有数据，开始收集...")
        capabilities = getattr(self.data_collector, 'last_capabilities', None)

        if capabilities is None:
            # 先测试能力
            capabilities = self.data_collector.test_all_sources_capability()

        collection_results = self.data_collector.collect_all_historical_data(capabilities)

        # 转换收集结果为数据字典
        for source_key, result in collection_results.items():
            if result.success:
                data[source_key] = result.data

        return data

    def _save_capabilities_report(self, capabilities: dict):
        """保存数据源能力报告"""
        report_file = self.cache_dir / "data_capabilities_summary.json"

        summary = {}
        for key, cap in capabilities.items():
            summary[key] = {
                'name': cap.source_name,
                'max_records': cap.max_records,
                'success_rate': cap.success_rate,
                'data_quality_score': cap.data_quality_score,
                'date_range': cap.date_range
            }

        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)

        print(f"💾 数据源能力报告已保存: {report_file}")

    def _save_data_summary(self):
        """保存数据摘要"""
        summary = {}

        for source_key, df in self.raw_data.items():
            summary[source_key] = {
                'records_count': len(df),
                'columns': df.columns.tolist(),
                'date_range': None,
                'sample_data': df.head(3).to_dict('records') if not df.empty else []
            }

            # 获取日期范围
            date_cols = [col for col in df.columns if 'date' in col.lower()]
            if date_cols:
                summary[source_key]['date_range'] = {
                    'start': str(df[date_cols[0]].min()),
                    'end': str(df[date_cols[0]].max())
                }

        summary_file = self.cache_dir / "data_summary.json"
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False, default=str)

        print(f"💾 数据摘要已保存: {summary_file}")

    def _save_aligned_data(self):
        """保存对齐后的数据"""
        aligned_file = self.cache_dir / "aligned_historical_data.parquet"
        self.aligned_data.to_parquet(aligned_file)

        # 同时保存数据元信息
        metadata = {
            'shape': self.aligned_data.shape,
            'columns': self.aligned_data.columns.tolist(),
            'date_range': {
                'start': str(self.aligned_data.index.min()),
                'end': str(self.aligned_data.index.max())
            }
        }

        metadata_file = self.cache_dir / "aligned_data_metadata.json"
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False, default=str)

        print(f"💾 对齐数据已保存: {aligned_file}")

    def _save_indicator_recommendations(self, source_name: str, recommendations: list):
        """保存指标推荐结果"""
        recommendations_data = []

        for rec in recommendations:
            recommendations_data.append({
                'indicator_name': rec.indicator_name,
                'suitability_score': rec.suitability_score,
                'recommended_parameters': rec.recommended_parameters,
                'reasoning': rec.reasoning,
                'expected_performance': rec.expected_performance,
                'risk_level': rec.risk_level
            })

        rec_file = self.cache_dir / f"indicator_recommendations_{source_name}.json"
        with open(rec_file, 'w', encoding='utf-8') as f:
            json.dump(recommendations_data, f, indent=2, ensure_ascii=False)

    def _generate_final_report(self, analysis_results: dict):
        """生成最终分析报告"""
        print(f"\n📊 生成最终分析报告...")
        print("=" * 80)

        # 统计信息
        stages = analysis_results['stages']
        duration = analysis_results['duration']

        print(f"⏱️  总执行时间: {duration:.2f} 秒")

        # 数据源统计
        if 'data_capabilities' in stages:
            capabilities = stages['data_capabilities']
            total_sources = len(capabilities)
            successful_sources = sum(1 for cap in capabilities.values() if cap.success_rate > 0)
            total_records = sum(cap.max_records for cap in capabilities.values())

            print(f"📡 数据源统计:")
            print(f"  测试数据源: {total_sources} 个")
            print(f"  成功数据源: {successful_sources} 个")
            print(f"  总记录潜力: {total_records:,} 条")

        # 数据收集统计
        if 'data_collection' in stages:
            collection = stages['data_collection']
            print(f"💾 数据收集统计:")
            print(f"  收集数据源: {collection['sources_count']} 个")
            print(f"  实际记录数: {collection['total_records']:,} 条")

        # 数据对齐统计
        if 'data_alignment' in stages:
            alignment = stages['data_alignment']
            if 'aligned_records' in alignment:
                print(f"🔄 数据对齐统计:")
                print(f"  对齐后记录: {alignment['aligned_records']:,} 条")

        # 指标推荐统计
        if 'indicator_selection' in stages:
            selection = stages['indicator_selection']
            print(f"🎯 指标推荐统计:")
            print(f"  分析数据源: {selection['analyzed_sources']} 个")
            print(f"  推荐指标数: {selection['total_recommendations']} 个")

        # 保存完整报告
        report_file = self.cache_dir / f"enhanced_hibor_analysis_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        # 转换datetime对象为字符串以便JSON序列化
        def convert_datetime(obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            return obj

        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(analysis_results, f, indent=2, ensure_ascii=False, default=convert_datetime)

        print(f"\n📄 完整分析报告已保存: {report_file}")
        print(f"📁 所有数据文件保存在: {self.cache_dir}")

    def get_summary_statistics(self) -> dict:
        """获取分析结果的摘要统计"""
        summary = {
            'data_sources_count': len(self.raw_data) if self.raw_data else 0,
            'aligned_records': len(self.aligned_data) if self.aligned_data is not None else 0,
            'indicator_recommendations': sum(len(recs) for recs in self.indicator_recommendations.values())
        }

        if self.aligned_data is not None:
            summary['aligned_columns'] = len(self.aligned_data.columns)
            summary['date_range'] = {
                'start': str(self.aligned_data.index.min()),
                'end': str(self.aligned_data.index.max())
            }

        return summary

# 主函数
def main():
    """主执行函数"""
    print("🎯 Enhanced HIBOR Analyzer - 增强非价格技术分析系统")
    print("=" * 80)
    print("本系统将执行以下任务:")
    print("1. 📡 测试所有HKMA数据源的API能力")
    print("2. 💾 收集完整历史数据")
    print("3. 🔄 执行数据时间对齐")
    print("4. 🎯 智能指标适配和推荐")
    print("5. 📊 生成综合分析报告")
    print("=" * 80)

    try:
        # 创建分析器
        analyzer = EnhancedHIBORAnalyzer()

        # 执行完整分析
        results = analyzer.run_complete_analysis(
            test_data_collection=True,
            collect_historical=True
        )

        # 显示摘要统计
        summary = analyzer.get_summary_statistics()
        print(f"\n📈 分析完成摘要:")
        print(f"  数据源数量: {summary['data_sources_count']} 个")
        print(f"  对齐记录数: {summary['aligned_records']:,} 条")
        if 'aligned_columns' in summary:
            print(f"  数据字段数: {summary['aligned_columns']} 个")
        print(f"  指标推荐数: {summary['indicator_recommendations']} 个")

        print(f"\n🎉 增强HIBOR分析系统运行完成!")
        print(f"📁 所有结果文件保存在: enhanced_hibor_data/ 目录")

        return analyzer, results

    except Exception as e:
        print(f"\n❌ 系统运行出错: {str(e)}")
        import traceback
        traceback.print_exc()
        return None, None

if __name__ == "__main__":
    # 运行主程序
    analyzer, results = main()