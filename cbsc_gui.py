#!/usr/bin/env python3
"""
CBSC 量化交易系統 - 桌面 GUI 應用
一鍵打開，顯示 HKEX 報告 + 南北水資金流向 + 回測結果 + 每日自動更新。

打包成 EXE:
    pip install pyinstaller
    pyinstaller --onefile --windowed --name CBSC cbsc_gui.py

用法:
    python cbsc_gui.py        # 直接運行
    CBSC.exe                   # 打包後雙擊
"""

import sys
import os
import json
import subprocess
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
import numpy as np

# 確保能 import scripts 目錄
sys.path.insert(0, str(Path(__file__).parent))

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTabWidget, QLabel, QPushButton, QTableWidget, QTableWidgetItem,
    QProgressBar, QStatusBar, QSystemTrayIcon, QMenu, QCheckBox,
    QSpinBox, QGroupBox, QGridLayout, QHeaderView, QFileDialog,
)
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal
from PyQt6.QtGui import QIcon, QColor, QFont

import pyqtgraph as pg

# 數據目錄
DATA_DIR = Path(__file__).parent / "data"
SCRIPTS_DIR = Path(__file__).parent / "scripts"


# ==============================================================================
# 數據更新 Worker（後台線程）
# ==============================================================================

class UpdateWorker(QThread):
    """後台運行爬蟲 + 回測"""
    progress = pyqtSignal(str)
    finished_signal = pyqtSignal(bool, str)

    def __init__(self, run_backtest=False):
        super().__init__()
        self.run_backtest = run_backtest

    def run(self):
        try:
            today = datetime.now().strftime("%Y%m%d")
            month_ago = (datetime.now() - timedelta(days=30)).strftime("%Y%m%d")

            # 1. HKEX 每日報告
            self.progress.emit("📥 抓取 HKEX 每日報告...")
            subprocess.run(
                [sys.executable, str(SCRIPTS_DIR / "hkex_daily_crawler.py"),
                 "--start", month_ago, "--end", today, "--delay", "0.3"],
                capture_output=True, text=True, cwd=str(Path(__file__).parent)
            )
            self.progress.emit("✅ HKEX 完成")

            # 2. 南北水
            self.progress.emit("💰 抓取南北水資金流向...")
            subprocess.run(
                [sys.executable, str(SCRIPTS_DIR / "stock_connect_crawler.py")],
                capture_output=True, text=True, cwd=str(Path(__file__).parent)
            )
            self.progress.emit("✅ 南北水完成")

            # 3. 回測（可選）
            if self.run_backtest:
                self.progress.emit("🔬 運行多 CPU 回測...")
                subprocess.run(
                    [sys.executable, str(SCRIPTS_DIR / "multiprocess_backtest.py"), "--workers", "16"],
                    capture_output=True, text=True, cwd=str(Path(__file__).parent)
                )
                self.progress.emit("✅ 回測完成")

            self.finished_signal.emit(True, "全部更新完成！")
        except Exception as e:
            self.finished_signal.emit(False, f"更新失敗: {e}")


# ==============================================================================
# HKEX 報告 Tab
# ==============================================================================

class HkexTab(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # 統計卡片
        stats = QGroupBox("📊 最新市場統計")
        stats_layout = QGridLayout()
        self.lbl_hsi = QLabel("恆指: --")
        self.lbl_turnover = QLabel("成交額: --")
        self.lbl_deals = QLabel("成交宗數: --")
        self.lbl_ad = QLabel("升/跌: --")
        for lbl in [self.lbl_hsi, self.lbl_turnover, self.lbl_deals, self.lbl_ad]:
            f = lbl.font(); f.setPointSize(12); f.setBold(True); lbl.setFont(f)
        stats_layout.addWidget(self.lbl_hsi, 0, 0)
        stats_layout.addWidget(self.lbl_turnover, 0, 1)
        stats_layout.addWidget(self.lbl_deals, 1, 0)
        stats_layout.addWidget(self.lbl_ad, 1, 1)
        stats.setLayout(stats_layout)
        layout.addWidget(stats)

        # 恆指走勢圖
        self.plot = pg.PlotWidget(title="恆生指數走勢")
        self.plot.setLabel("left", "點數")
        self.plot.setLabel("bottom", "日期")
        self.plot.showGrid(x=True, y=True)
        layout.addWidget(self.plot)

        # 成交額柱狀圖
        self.plot_turnover = pg.PlotWidget(title="每日成交額（億港元）")
        self.plot_turnover.setLabel("left", "億 HKD")
        self.plot_turnover.showGrid(x=True, y=True)
        layout.addWidget(self.plot_turnover)

        # 數據表格
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["日期", "恆指收市", "變動", "成交額", "升", "跌"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table)

    def load_data(self):
        csv_path = DATA_DIR / "hkex_daily.csv"
        if not csv_path.exists():
            return
        df = pd.read_csv(csv_path).sort_values("date")

        if df.empty:
            return

        latest = df.iloc[-1]

        # 統計卡片
        hsi = latest.get("hsi_close")
        chg = latest.get("hsi_change", 0) or 0
        color = "#3f8600" if chg >= 0 else "#cf1322"
        self.lbl_hsi.setText(f"恆指: {hsi:,.2f}" if pd.notna(hsi) else "恆指: --")
        self.lbl_hsi.setStyleSheet(f"color: {color};")

        turnover = latest.get("turnover_hkd", 0) or 0
        self.lbl_turnover.setText(f"成交額: HK${turnover/1e9:.1f}B")
        self.lbl_deals.setText(f"成交宗數: {(latest.get('deals',0) or 0):,.0f}")
        adv = latest.get("advanced_stocks", 0) or 0
        dec = latest.get("declined_stocks", 0) or 0
        self.lbl_ad.setText(f"升/跌: {adv:,} / {dec:,}")

        # 恆指走勢圖
        valid = df.dropna(subset=["hsi_close"]).tail(30)
        if not valid.empty:
            x = range(len(valid))
            y = valid["hsi_close"].values
            self.plot.clear()
            self.plot.plot(list(x), list(y), pen=pg.mkPen(color="#1890ff", width=2))
            # 設定 x 軸標籤
            ticks = [[(i, d[:5]) for i, d in enumerate(valid["date"].values) if i % 5 == 0]]
            self.plot.getAxis("bottom").setTicks(ticks)

        # 成交額柱狀圖
        valid_t = df.dropna(subset=["turnover_hkd"]).tail(30)
        if not valid_t.empty:
            x2 = range(len(valid_t))
            y2 = (valid_t["turnover_hkd"].values / 1e8)  # 億港元
            self.plot_turnover.clear()
            for xi, yi in zip(x2, y2):
                self.plot_turnover.addItem(pg.BarGraphItem(x=[xi], height=[yi], width=0.6, brush="#1890ff"))

        # 表格（最近 14 天）
        recent = df.tail(14).iloc[::-1]
        self.table.setRowCount(len(recent))
        for i, (_, row) in enumerate(recent.iterrows()):
            self.table.setItem(i, 0, QTableWidgetItem(str(row.get("date", ""))))
            hsi_val = row.get("hsi_close")
            self.table.setItem(i, 1, QTableWidgetItem(f"{hsi_val:,.2f}" if pd.notna(hsi_val) else "-"))
            chg_val = row.get("hsi_change", 0) or 0
            item = QTableWidgetItem(f"{chg_val:+.2f}")
            item.setForeground(QColor("#3f8600" if chg_val >= 0 else "#cf1322"))
            self.table.setItem(i, 2, item)
            tov = row.get("turnover_hkd", 0) or 0
            self.table.setItem(i, 3, QTableWidgetItem(f"${tov/1e9:.1f}B"))
            self.table.setItem(i, 4, QTableWidgetItem(f"{row.get('advanced_stocks',0) or 0:,}"))
            self.table.setItem(i, 5, QTableWidgetItem(f"{row.get('declined_stocks',0) or 0:,}"))


# ==============================================================================
# 南北水 Tab
# ==============================================================================

class StockConnectTab(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # 統計卡片
        stats = QGroupBox("💰 港股通資金流向")
        sl = QGridLayout()
        self.lbl_total = QLabel("總成交: --")
        self.lbl_net = QLabel("淨買入: --")
        self.lbl_sh = QLabel("滬港通: --")
        self.lbl_sz = QLabel("深港通: --")
        for lbl in [self.lbl_total, self.lbl_net, self.lbl_sh, self.lbl_sz]:
            f = lbl.font(); f.setPointSize(12); f.setBold(True); lbl.setFont(f)
        sl.addWidget(self.lbl_total, 0, 0)
        sl.addWidget(self.lbl_net, 0, 1)
        sl.addWidget(self.lbl_sh, 1, 0)
        sl.addWidget(self.lbl_sz, 1, 1)
        stats.setLayout(sl)
        layout.addWidget(stats)

        # 淨買入走勢圖
        self.plot = pg.PlotWidget(title="南北水淨買入走勢（百萬 HKD）")
        self.plot.setLabel("left", "百萬 HKD")
        self.plot.showGrid(x=True, y=True)
        layout.addWidget(self.plot)

        # 表格
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["日期", "總成交", "買入", "賣出", "淨買入", "滬/深"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table)

    def load_data(self):
        csv_path = DATA_DIR / "stock_connect.csv"
        if not csv_path.exists():
            return
        df = pd.read_csv(csv_path).sort_values("date")
        if df.empty:
            return

        latest = df.iloc[-1]
        total = latest.get("southbound_total_mil", 0) or 0
        net = latest.get("southbound_net_mil", 0) or 0
        sh = latest.get("sh_southbound_mil", 0) or 0
        sz = latest.get("sz_southbound_mil", 0) or 0

        self.lbl_total.setText(f"總成交: HK${total:,.0f}M")
        net_color = "#3f8600" if net >= 0 else "#cf1322"
        self.lbl_net.setText(f"淨買入: {'+' if net>=0 else ''}HK${net:,.0f}M")
        self.lbl_net.setStyleSheet(f"color: {net_color};")
        self.lbl_sh.setText(f"滬港通: HK${sh:,.0f}M")
        self.lbl_sz.setText(f"深港通: HK${sz:,.0f}M")

        # 圖表
        valid = df.dropna(subset=["southbound_net_mil"])
        if not valid.empty:
            x = range(len(valid))
            y = valid["southbound_net_mil"].values
            self.plot.clear()
            self.plot.clear()
            for xi, yi in zip(x, y):
                c = "#52c41a" if yi >= 0 else "#f5222d"
                self.plot.addItem(pg.BarGraphItem(x=[xi], height=[yi], width=0.6, brush=c))

        # 表格
        recent = df.iloc[::-1]
        self.table.setRowCount(len(recent))
        for i, (_, row) in enumerate(recent.iterrows()):
            self.table.setItem(i, 0, QTableWidgetItem(str(row.get("date", ""))))
            self.table.setItem(i, 1, QTableWidgetItem(f"${row.get('southbound_total_mil',0) or 0:,.0f}M"))
            self.table.setItem(i, 2, QTableWidgetItem(f"${row.get('southbound_buy_mil',0) or 0:,.0f}M"))
            self.table.setItem(i, 3, QTableWidgetItem(f"${row.get('southbound_sell_mil',0) or 0:,.0f}M"))
            net_v = row.get("southbound_net_mil", 0) or 0
            item = QTableWidgetItem(f"{'+' if net_v>=0 else ''}{net_v:,.0f}M")
            item.setForeground(QColor("#3f8600" if net_v >= 0 else "#cf1322"))
            self.table.setItem(i, 4, item)
            self.table.setItem(i, 5, QTableWidgetItem(f"${row.get('sh_southbound_mil',0) or 0:,.0f} / ${row.get('sz_southbound_mil',0) or 0:,.0f}"))


# ==============================================================================
# 回測 Tab
# ==============================================================================

class BacktestTab(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # 統計
        stats = QGroupBox("🔬 回測概覽")
        sl = QGridLayout()
        self.lbl_count = QLabel("股票數: --")
        self.lbl_best = QLabel("最佳 Sharpe: --")
        self.lbl_avg = QLabel("平均回報: --")
        for lbl in [self.lbl_count, self.lbl_best, self.lbl_avg]:
            f = lbl.font(); f.setPointSize(12); f.setBold(True); lbl.setFont(f)
        sl.addWidget(self.lbl_count, 0, 0)
        sl.addWidget(self.lbl_best, 0, 1)
        sl.addWidget(self.lbl_avg, 0, 2)
        stats.setLayout(sl)
        layout.addWidget(stats)

        # Sharpe 對比圖
        self.plot = pg.PlotWidget(title="各股票 Sharpe Ratio 對比")
        self.plot.setLabel("left", "Sharpe")
        self.plot.setLabel("bottom", "股票")
        self.plot.showGrid(x=True, y=True)
        layout.addWidget(self.plot)

        # 回報率圖
        self.plot_ret = pg.PlotWidget(title="各股票回報率 (%)")
        self.plot_ret.setLabel("left", "%")
        self.plot_ret.showGrid(x=True, y=True)
        layout.addWidget(self.plot_ret)

        # 表格
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["股票", "Sharpe", "回報率", "最大回撤", "交易數", "勝率"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table)

    def load_data(self):
        csv_path = DATA_DIR / "backtest_results.csv"
        if not csv_path.exists():
            return
        df = pd.read_csv(csv_path)
        if "status" in df.columns:
            df = df[df["status"] == "ok"]
        if df.empty:
            return

        df = df.sort_values("sharpe", ascending=False)
        self.lbl_count.setText(f"股票數: {len(df)}")
        self.lbl_best.setText(f"最佳 Sharpe: {df['sharpe'].max():.3f}")
        self.lbl_avg.setText(f"平均回報: {df['return'].mean()*100:.1f}%")

        # Sharpe 圖
        x = range(len(df))
        y = df["sharpe"].values
        self.plot.clear()
        for xi, yi in zip(x, y):
            c = "#52c41a" if yi >= 0.5 else "#faad14" if yi >= 0 else "#f5222d"
            self.plot.addItem(pg.BarGraphItem(x=[xi], height=[yi], width=0.6, brush=c))
        ticks = [[(i, s) for i, s in enumerate(df["symbol"].values)]]
        self.plot.getAxis("bottom").setTicks(ticks)

        # 回報率圖
        y2 = (df["return"].values * 100)
        self.plot_ret.clear()
        for xi, yi in zip(x, y2):
            c = "#52c41a" if yi >= 0 else "#f5222d"
            self.plot_ret.addItem(pg.BarGraphItem(x=[xi], height=[yi], width=0.6, brush=c))
        self.plot_ret.getAxis("bottom").setTicks(ticks)

        # 表格
        self.table.setRowCount(len(df))
        for i, (_, row) in enumerate(df.iterrows()):
            self.table.setItem(i, 0, QTableWidgetItem(str(row.get("symbol", ""))))
            sh = row.get("sharpe", 0)
            item = QTableWidgetItem(f"{sh:.3f}")
            item.setForeground(QColor("#3f8600" if sh >= 0.5 else "#faad14" if sh >= 0 else "#cf1322"))
            self.table.setItem(i, 1, item)
            ret = row.get("return", 0)
            item2 = QTableWidgetItem(f"{ret*100:+.1f}%")
            item2.setForeground(QColor("#3f8600" if ret >= 0 else "#cf1322"))
            self.table.setItem(i, 2, item2)
            self.table.setItem(i, 3, QTableWidgetItem(f"{row.get('max_dd',0)*100:.1f}%"))
            self.table.setItem(i, 4, QTableWidgetItem(str(int(row.get("trades", 0)))))
            self.table.setItem(i, 5, QTableWidgetItem(f"{row.get('win_rate',0)*100:.0f}%"))


# ==============================================================================
# 主視窗
# ==============================================================================

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CBSC 量化交易系統")
        self.setMinimumSize(1200, 800)

        # 深色背景
        self.setStyleSheet("""
            QMainWindow { background: #1a1a2e; }
            QGroupBox { color: #e0e0e0; font-weight: bold; border: 1px solid #333; border-radius: 6px; margin-top: 8px; padding-top: 12px; }
            QGroupBox::title { subcontrol-origin: margin; left: 10px; }
            QLabel { color: #e0e0e0; }
            QTableWidget { background: #16213e; color: #e0e0e0; gridline-color: #333; }
            QHeaderView::section { background: #0f3460; color: #e0e0e0; }
            QPushButton { background: #1890ff; color: white; border: none; padding: 8px 16px; border-radius: 4px; font-size: 13px; }
            QPushButton:hover { background: #40a9ff; }
            QPushButton:pressed { background: #096dd9; }
            QCheckBox { color: #e0e0e0; }
        """)

        self.init_ui()
        self.init_timer()
        self.refresh_all()

    def init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        # 頂部工具欄
        toolbar = QHBoxLayout()
        title = QLabel("📊 CBSC 量化交易系統")
        f = title.font(); f.setPointSize(16); f.setBold(True); title.setFont(f)
        title.setStyleSheet("color: #1890ff;")
        toolbar.addWidget(title)
        toolbar.addStretch()

        self.chk_backtest = QCheckBox("更新時跑回測")
        self.chk_backtest.setChecked(False)
        toolbar.addWidget(self.chk_backtest)

        self.chk_auto = QCheckBox("每日自動更新 (16:15)")
        self.chk_auto.setChecked(True)
        self.chk_auto.stateChanged.connect(self.toggle_auto_update)
        toolbar.addWidget(self.chk_auto)

        self.btn_update = QPushButton("🔄 立即更新數據")
        self.btn_update.clicked.connect(self.update_data)
        toolbar.addWidget(self.btn_update)

        layout.addLayout(toolbar)

        # 進度條
        self.progress = QProgressBar()
        self.progress.setVisible(False)
        layout.addWidget(self.progress)

        # Tab 頁
        self.tabs = QTabWidget()
        self.hkex_tab = HkexTab()
        self.sc_tab = StockConnectTab()
        self.bt_tab = BacktestTab()
        self.tabs.addTab(self.hkex_tab, "📈 HKEX 每日報告")
        self.tabs.addTab(self.sc_tab, "💰 南北水資金流向")
        self.tabs.addTab(self.bt_tab, "🔬 回測結果")
        layout.addWidget(self.tabs)

        # 狀態欄
        self.statusBar().showMessage(f"就緒 | 數據目錄: {DATA_DIR}")

    def init_timer(self):
        """每日定時更新（16:15 HKT，收市後15分鐘）"""
        self.auto_timer = QTimer(self)
        self.auto_timer.timeout.connect(self.check_auto_update)
        self.auto_timer.start(60000)  # 每分鐘檢查一次
        self.last_auto_date = None

    def check_auto_update(self):
        if not self.chk_auto.isChecked():
            return
        now = datetime.now()
        # 交易日 16:15 自動更新（週一到週五）
        if now.weekday() < 5 and now.hour == 16 and now.minute >= 15:
            today_key = now.strftime("%Y%m%d")
            if today_key != self.last_auto_date:
                self.last_auto_date = today_key
                self.update_data()

    def toggle_auto_update(self):
        if self.chk_auto.isChecked():
            self.statusBar().showMessage("✅ 每日自動更新已開啟 (16:15)")
        else:
            self.statusBar().showMessage("⛔ 自動更新已關閉")

    def update_data(self):
        """觸發數據更新"""
        self.btn_update.setEnabled(False)
        self.progress.setVisible(True)
        self.progress.setRange(0, 0)  # 不確定進度

        self.worker = UpdateWorker(run_backtest=self.chk_backtest.isChecked())
        self.worker.progress.connect(lambda msg: self.statusBar().showMessage(msg))
        self.worker.finished_signal.connect(self.on_update_done)
        self.worker.start()

    def on_update_done(self, success, message):
        self.progress.setVisible(False)
        self.btn_update.setEnabled(True)
        self.statusBar().showMessage(message)
        if success:
            self.refresh_all()

    def refresh_all(self):
        """重新載入所有 tab 的數據"""
        self.hkex_tab.load_data()
        self.sc_tab.load_data()
        self.bt_tab.load_data()
        self.statusBar().showMessage(f"✅ 數據已更新 | {datetime.now().strftime('%H:%M:%S')}")


# ==============================================================================
# 入口
# ==============================================================================

def main():
    # 高 DPI 支援
    os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"

    app = QApplication(sys.argv)
    app.setApplicationName("CBSC 量化交易系統")

    # pyqtgraph 深色主題
    pg.setConfigOption("background", "#1a1a2e")
    pg.setConfigOption("foreground", "#e0e0e0")

    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
