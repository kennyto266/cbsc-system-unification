#!/usr/bin/env python3
"""
CSV格式導出器
支持多種編碼、分隔符和數據格式化選項
"""

import os
import csv
import logging
from typing import Dict, List, Optional, Any, Union
from pathlib import Path
from datetime import datetime
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)

class CSVExporter:
    """CSV導出器類"""

    def __init__(self, config: Dict):
        self.config = config
        self.encoding = config.get('encoding', 'utf-8-sig')
        self.date_format = config.get('date_format', '%Y-%m-%d')
        self.decimal_separator = config.get('decimal_separator', '.')
        self.include_headers = config.get('include_headers', True)
        self.delimiter = config.get('delimiter', ',')

    def export(self, data: Any, output_path: Path, options: Dict = None) -> bool:
        """
        導出數據到CSV文件

        Args:
            data: 要導出的數據
            output_path: 輸出文件路徑
            options: 導出選項

        Returns:
            bool: 是否成功
        """
        try:
            # 將數據轉換為DataFrame
            df = self._convert_to_dataframe(data)

            if df.empty:
                logger.warning("⚠️ 數據為空，無法導出")
                return False

            # 格式化數據
            df = self._format_dataframe(df)

            # 導出到CSV
            df.to_csv(
                output_path,
                index=False,
                encoding=self.encoding,
                sep=self.delimiter,
                header=self.include_headers,
                date_format=self.date_format,
                float_format=lambda x: f"{x:.{self._get_decimal_places(x)}f}".replace('.', self.decimal_separator)
            )

            file_size = os.path.getsize(output_path) if os.path.exists(output_path) else 0
            logger.info(f"✅ CSV文件導出成功: {output_path} ({file_size} bytes, {len(df)} 行)")
            return True

        except Exception as e:
            logger.error(f"❌ CSV導出失敗: {e}")
            return False

    def _convert_to_dataframe(self, data: Any) -> pd.DataFrame:
        """將數據轉換為DataFrame"""
        try:
            if isinstance(data, pd.DataFrame):
                return data.copy()
            elif isinstance(data, pd.Series):
                return data.to_frame()
            elif isinstance(data, dict):
                # 處理字典數據
                if all(isinstance(v, (list, tuple)) for v in data.values()):
                    # 字典的值都是列表，創建DataFrame
                    return pd.DataFrame(data)
                else:
                    # 字典的值是單個值，創建單行DataFrame
                    return pd.DataFrame([data])
            elif isinstance(data, (list, tuple)):
                # 列表數據
                if data and isinstance(data[0], dict):
                    # 列表包含字典
                    return pd.DataFrame(data)
                else:
                    # 簡單列表
                    return pd.DataFrame({'Value': data})
            else:
                # 其他類型，轉換為單行DataFrame
                return pd.DataFrame({'Data': [data]})
        except Exception as e:
            logger.warning(f"數據轉換失敗: {e}")
            return pd.DataFrame()

    def _format_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """格式化DataFrame數據"""
        try:
            formatted_df = df.copy()

            # 處理日期時間列
            for col in formatted_df.columns:
                if formatted_df[col].dtype == 'datetime64[ns]':
                    if self.date_format:
                        formatted_df[col] = formatted_df[col].dt.strftime(self.date_format)

                # 處理數值列
                elif formatted_df[col].dtype in ['float64', 'float32']:
                    # 替換NaN為空字符串
                    formatted_df[col] = formatted_df[col].fillna('')

                    # 格式化數字
                    if self.decimal_separator != '.':
                        formatted_df[col] = formatted_df[col].apply(
                            lambda x: f"{x:.{self._get_decimal_places(x)}f}".replace('.', self.decimal_separator) if pd.notna(x) else ''
                        )

                # 處理整數列
                elif formatted_df[col].dtype in ['int64', 'int32']:
                    # 替換NaN為空字符串
                    formatted_df[col] = formatted_df[col].fillna('')

            return formatted_df

        except Exception as e:
            logger.warning(f"數據格式化失敗: {e}")
            return df

    def _get_decimal_places(self, value: float) -> int:
        """獲取數值的小數位數"""
        if pd.isna(value):
            return 2
        if value == 0:
            return 2
        if abs(value) >= 1:
            return 2
        return max(2, -int(np.floor(np.log10(abs(value)))))

    def export_multiple_sheets(self, data_dict: Dict[str, Any], base_path: Path) -> bool:
        """
        導出多個數據表到多個CSV文件

        Args:
            data_dict: 數據字典 {表名: 數據}
            base_path: 基礎文件路徑

        Returns:
            bool: 是否成功
        """
        try:
            success_count = 0
            total_count = len(data_dict)

            for sheet_name, data in data_dict.items():
                # 生成文件名
                sheet_path = base_path.parent / f"{base_path.stem}_{sheet_name}{base_path.suffix}"

                # 導出單個表
                if self.export(data, sheet_path):
                    success_count += 1
                else:
                    logger.warning(f"⚠️ 工作表 {sheet_name} 導出失敗")

            success = success_count == total_count
            if success:
                logger.info(f"✅ 多表CSV導出完成: {success_count}/{total_count} 個文件")
            else:
                logger.warning(f"⚠️ 部分CSV導出失敗: {success_count}/{total_count} 個文件")

            return success

        except Exception as e:
            logger.error(f"❌ 多表CSV導出失敗: {e}")
            return False

    def export_with_summary(self, data: Any, output_path: Path, summary_data: Dict = None) -> bool:
        """
        導出數據並包含摘要信息

        Args:
            data: 要導出的數據
            output_path: 輸出文件路徑
            summary_data: 摘要數據

        Returns:
            bool: 是否成功
        """
        try:
            # 將數據轉換為DataFrame
            df = self._convert_to_dataframe(data)

            if df.empty:
                return False

            # 添加摘要行
            if summary_data:
                summary_rows = []
                for key, value in summary_data.items():
                    summary_rows.append([key, str(value)])

                summary_df = pd.DataFrame(summary_rows, columns=['摘要項', '數值'])

                # 合併數據和摘要
                combined_df = pd.concat([summary_df, pd.DataFrame([['', '']])], ignore_index=True)
                combined_df = pd.concat([combined_df, df], ignore_index=True)
            else:
                combined_df = df

            # 格式化數據
            combined_df = self._format_dataframe(combined_df)

            # 導出到CSV
            combined_df.to_csv(
                output_path,
                index=False,
                encoding=self.encoding,
                sep=self.delimiter,
                header=self.include_headers,
                date_format=self.date_format
            )

            logger.info(f"✅ 帶摘要的CSV文件導出成功: {output_path}")
            return True

        except Exception as e:
            logger.error(f"❌ 帶摘要的CSV導出失敗: {e}")
            return False

    def export_validation_report(self, validation_results: Dict, output_path: Path) -> bool:
        """
        導出數據驗證報告

        Args:
            validation_results: 驗證結果
            output_path: 輸出路徑

        Returns:
            bool: 是否成功
        """
        try:
            # 組織驗證報告數據
            report_data = []

            # 整體摘要
            report_data.append(['驗證類型', '整體驗證'])
            report_data.append(['總檢查項', validation_results.get('total_checks', 0)])
            report_data.append(['通過檢查', validation_results.get('passed_checks', 0)])
            report_data.append(['失敗檢查', validation_results.get('failed_checks', 0)])
            report_data.append(['驗證時間', validation_results.get('validation_time', '')])
            report_data.append(['', ''])

            # 詳細結果
            if 'details' in validation_results:
                report_data.append(['詳細結果', ''])
                for item in validation_results['details']:
                    report_data.append([f"檢查: {item.get('check', '')}", f"結果: {item.get('result', '')}"])
                    if 'message' in item:
                        report_data.append(['信息', item['message']])
                    report_data.append(['', ''])

            # 創建DataFrame並導出
            report_df = pd.DataFrame(report_data, columns=['類別', '內容'])
            return self.export(report_df, output_path)

        except Exception as e:
            logger.error(f"❌ 驗證報告CSV導出失敗: {e}")
            return False

    def create_csv_template(self, columns: List[str], output_path: Path, sample_data: List = None) -> bool:
        """
        創建CSV模板文件

        Args:
            columns: 列名列表
            output_path: 輸出路徑
            sample_data: 示例數據

        Returns:
            bool: 是否成功
        """
        try:
            # 創建模板DataFrame
            if sample_data:
                template_df = pd.DataFrame(sample_data, columns=columns)
            else:
                template_df = pd.DataFrame(columns=columns)

            # 添加說明行
            header_rows = [['CSV導入模板', ''], ['', ''], ['列名', '說明']]
            for col in columns:
                header_rows.append([col, f'請在此列輸入{col}數據'])

            header_df = pd.DataFrame(header_rows[3:], columns=columns)

            # 導出模板
            template_df.to_csv(
                output_path,
                index=False,
                encoding=self.encoding,
                sep=self.delimiter
            )

            # 創建說明文件
            readme_path = output_path.parent / f"{output_path.stem}_README.txt"
            with open(readme_path, 'w', encoding='utf-8') as f:
                f.write(f"CSV導入模板說明\n")
                f.write(f"生成時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"編碼: {self.encoding}\n")
                f.write(f"分隔符: '{self.delimiter}'\n")
                f.write(f"日期格式: {self.date_format}\n")
                f.write(f"小數分隔符: '{self.decimal_separator}'\n\n")
                f.write(f"列說明:\n")
                for i, col in enumerate(columns, 1):
                    f.write(f"{i}. {col}\n")

            logger.info(f"✅ CSV模板創建成功: {output_path}")
            return True

        except Exception as e:
            logger.error(f"❌ CSV模板創建失敗: {e}")
            return False

    def merge_csv_files(self, file_paths: List[Path], output_path: Path, add_source_column: bool = True) -> bool:
        """
        合併多個CSV文件

        Args:
            file_paths: 要合併的CSV文件路徑列表
            output_path: 輸出路徑
            add_source_column: 是否添加源文件列

        Returns:
            bool: 是否成功
        """
        try:
            merged_dfs = []

            for file_path in file_paths:
                try:
                    df = pd.read_csv(
                        file_path,
                        encoding=self.encoding,
                        sep=self.delimiter
                    )

                    if add_source_column:
                        df['source_file'] = file_path.name

                    merged_dfs.append(df)

                except Exception as e:
                    logger.warning(f"⚠️ 文件讀取失敗: {file_path} - {e}")

            if not merged_dfs:
                logger.error("❌ 沒有可合併的文件")
                return False

            # 合併所有DataFrame
            merged_df = pd.concat(merged_dfs, ignore_index=True)

            # 導出合併結果
            merged_df.to_csv(
                output_path,
                index=False,
                encoding=self.encoding,
                sep=self.delimiter
            )

            logger.info(f"✅ CSV文件合併成功: {output_path} ({len(merged_df)} 行)")
            return True

        except Exception as e:
            logger.error(f"❌ CSV文件合併失敗: {e}")
            return False

    def get_csv_info(self, csv_path: Path) -> Dict:
        """
        獲取CSV文件信息

        Args:
            csv_path: CSV文件路徑

        Returns:
            Dict: 文件信息
        """
        try:
            # 獲取基本信息
            file_info = {
                'file_path': str(csv_path),
                'file_size': os.path.getsize(csv_path),
                'encoding': self.encoding
            }

            # 讀取CSV獲取數據信息
            df = pd.read_csv(
                csv_path,
                encoding=self.encoding,
                sep=self.delimiter,
                nrows=5  # 只讀取前5行獲取結構信息
            )

            file_info.update({
                'columns': list(df.columns),
                'column_count': len(df.columns),
                'estimated_rows': os.path.getsize(csv_path) // (len(df.to_csv(index=False, header=False).encode()) / len(df)) if len(df) > 0 else 0,
                'sample_data': df.head(3).to_dict('records')
            })

            return file_info

        except Exception as e:
            logger.error(f"❌ CSV文件信息獲取失敗: {e}")
            return {'error': str(e)}