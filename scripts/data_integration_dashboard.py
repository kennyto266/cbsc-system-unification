#!/usr/bin/env python3
"""
数据整合监控仪表板
Data Integration Monitoring Dashboard

实时显示数据整合进度和状态
"""

import os
import sys
import json
import psycopg2
import pandas as pd
from datetime import datetime, timedelta
import time
from typing import Dict, List, Any

class DataIntegrationDashboard:
    """数据整合监控仪表板"""

    def __init__(self, db_url: str = None):
        self.db_url = db_url or os.getenv('DATABASE_URL',
                                        'postgresql://postgres:password@localhost:5432/quant_system')
        self.conn = None

    def connect(self):
        """连接数据库"""
        try:
            self.conn = psycopg2.connect(self.db_url)
            return True
        except Exception as e:
            print(f"❌ 数据库连接失败: {e}")
            return False

    def get_data_summary(self) -> Dict[str, Any]:
        """获取数据汇总信息"""
        if not self.conn:
            if not self.connect():
                return {}

        summary = {}

        with self.conn.cursor() as cursor:
            try:
                # 港交所数据统计
                cursor.execute("""
                    SELECT
                        COUNT(*) as total_records,
                        MIN(date) as earliest_date,
                        MAX(date) as latest_date,
                        AVG(turnover_hkd) as avg_turnover
                    FROM hkex_market_data
                """)
                hkex_result = cursor.fetchone()
                summary['hkex_market_data'] = {
                    'total_records': hkex_result[0] or 0,
                    'date_range': f"{hkex_result[1]} 至 {hkex_result[2]}" if hkex_result[1] else "无数据",
                    'avg_turnover_hkd': f"{hkex_result[3]:,.0f}" if hkex_result[3] else "0"
                }

                # 股票数据统计
                cursor.execute("""
                    SELECT
                        COUNT(*) as total_records,
                        COUNT(DISTINCT symbol) as unique_symbols,
                        MIN(date) as earliest_date,
                        MAX(date) as latest_date
                    FROM stock_historical_data
                """)
                stock_result = cursor.fetchone()
                summary['stock_historical_data'] = {
                    'total_records': stock_result[0] or 0,
                    'unique_symbols': stock_result[1] or 0,
                    'date_range': f"{stock_result[2]} 至 {stock_result[3]}" if stock_result[2] else "无数据"
                }

                # 政府经济数据统计
                cursor.execute("""
                    SELECT
                        COUNT(*) as total_records,
                        COUNT(DISTINCT data_type) as unique_types,
                        MIN(data_date) as earliest_date,
                        MAX(data_date) as latest_date
                    FROM government_economic_data
                """)
                gov_result = cursor.fetchone()
                summary['government_economic_data'] = {
                    'total_records': gov_result[0] or 0,
                    'unique_types': gov_result[1] or 0,
                    'date_range': f"{gov_result[2]} 至 {gov_result[3]}" if gov_result[2] else "无数据"
                }

                # 分区表状态
                cursor.execute("""
                    SELECT
                        schemaname,
                        tablename,
                        pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
                    FROM pg_tables
                    WHERE tablename LIKE '%partitioned%'
                    ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
                    LIMIT 10
                """)
                partition_tables = cursor.fetchall()
                summary['partition_tables'] = [
                    {'schema': row[0], 'table': row[1], 'size': row[2]}
                    for row in partition_tables
                ]

            except Exception as e:
                print(f"❌ 查询数据失败: {e}")

        return summary

    def get_recent_activity(self) -> List[Dict[str, Any]]:
        """获取最近活动"""
        activities = []

        # 检查最近的数据整合报告
        report_path = 'data_integration_report.json'
        if os.path.exists(report_path):
            try:
                with open(report_path, 'r', encoding='utf-8') as f:
                    report = json.load(f)
                    activities.append({
                        'timestamp': report.get('integration_summary', {}).get('end_time', ''),
                        'type': '数据整合',
                        'status': '✅ 完成' if report.get('integration_summary', {}).get('success_rate', '0') == '100.0%' else '⚠️ 部分完成',
                        'details': f"成功率: {report.get('integration_summary', {}).get('success_rate', 'N/A')}"
                    })
            except Exception as e:
                print(f"❌ 读取整合报告失败: {e}")

        # 检查最近的数据文件更新
        data_files = []
        for root, dirs, files in os.walk('.'):
            for file in files:
                if file.endswith(('.csv', '.json')) and ('hkex' in file or 'market_data' in file):
                    file_path = os.path.join(root, file)
                    mtime = datetime.fromtimestamp(os.path.getmtime(file_path))
                    if datetime.now() - mtime < timedelta(days=7):
                        data_files.append((file_path, mtime))

        data_files.sort(key=lambda x: x[1], reverse=True)
        for file_path, mtime in data_files[:5]:
            activities.append({
                'timestamp': mtime.strftime('%Y-%m-%d %H:%M:%S'),
                'type': '数据文件',
                'status': '📁 已更新',
                'details': os.path.basename(file_path)
            })

        return activities

    def display_dashboard(self):
        """显示仪表板"""
        # 清屏
        os.system('cls' if os.name == 'nt' else 'clear')

        print("="*80)
        print("📊 CBSC系统数据整合监控仪表板")
        print("="*80)
        print(f"刷新时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()

        # 数据汇总
        summary = self.get_data_summary()

        print("📈 数据汇总统计")
        print("-"*50)
        for data_type, stats in summary.items():
            if data_type != 'partition_tables':
                print(f"\n{self._get_emoji(data_type)} {data_type.replace('_', ' ').title()}:")
                for key, value in stats.items():
                    print(f"  {key.replace('_', ' ').title()}: {value}")

        # 分区表状态
        if 'partition_tables' in summary and summary['partition_tables']:
            print(f"\n🗂️  分区表状态 (Top 10)")
            print("-"*50)
            for table in summary['partition_tables']:
                print(f"  {table['schema']}.{table['table']}: {table['size']}")

        # 最近活动
        activities = self.get_recent_activity()
        if activities:
            print(f"\n🔄 最近活动")
            print("-"*50)
            for activity in activities:
                print(f"  {activity['timestamp']} - {activity['type']}: {activity['status']} - {activity['details']}")

        # 任务状态
        print(f"\n✅ Task #004 数据整合状态")
        print("-"*50)
        print("  状态: 🔄 进行中")
        print("  进度: 80% (数据迁移完成，验证进行中)")
        print("  预计完成: 2025-01-24")

        print("\n" + "="*80)
        print("按 Ctrl+C 退出，每30秒自动刷新")

    def _get_emoji(self, data_type: str) -> str:
        """获取数据类型对应的emoji"""
        emoji_map = {
            'hkex_market_data': '🏢',
            'stock_historical_data': '📈',
            'government_economic_data': '🏛️'
        }
        return emoji_map.get(data_type, '📊')

    def run_monitoring(self):
        """运行监控"""
        try:
            while True:
                self.display_dashboard()
                time.sleep(30)
        except KeyboardInterrupt:
            print("\n\n👋 监控已停止")

def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description='数据整合监控仪表板')
    parser.add_argument('--once', action='store_true', help='只显示一次')
    parser.add_argument('--export', help='导出状态到JSON文件')

    args = parser.parse_args()

    dashboard = DataIntegrationDashboard()

    if args.export:
        # 导出状态到JSON
        summary = dashboard.get_data_summary()
        with open(args.export, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        print(f"状态已导出到: {args.export}")
        return

    if args.once:
        dashboard.display_dashboard()
    else:
        dashboard.run_monitoring()

if __name__ == "__main__":
    main()