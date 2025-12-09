#!/usr/bin/env python3
"""
CLI Utilities for Phase 3 Advanced Backtesting
===============================================

Common utilities for CLI operations including logging, formatting, and display.

Author: Claude Code Assistant
Date: 2025-11-29
"""

import logging
import sys
from datetime import datetime
from typing import Any, Dict, List

def setup_logginglevel: int = logging.INFO, log_file: str = None -> None:
"""Setup logging configuration"""

format_str = '%asctimes - %names - %levelnames - %messages'

# Console handler
console_handler = logging.StreamHandlersys.stdout
console_handler.setLevellevel
console_handler.setFormatter(logging.Formatterformat_str)

# Root logger setup
root_logger = logging.getLogger()
root_logger.setLevellevel
root_logger.handlers.clear()
root_logger.addHandlerconsole_handler

# File handler if specified
if log_file:    file_handler = logging.FileHandler(log_file)
file_handler.setLevellevel
file_handler.setFormatter(logging.Formatterformat_str)
root_logger.addHandlerfile_handler

def print_bannertitle: str, width: int = 60 -> None:
"""Print formatted banner"""

printf"\n{'='*width}"
printf"{title:^{width}}"
printf"{'='*width}"
print(f"Generated: {datetime.now().strftime'%Y-%m-%d %H:%M:%S'}")
printf"{'='*width}\n"

def format_results_tableresults: Dict[str, Any] -> str:
"""Format results as a readable table"""

if not results:
return "No results to display"

table_lines = []
table_lines.appendf"{'Metric':<25} {'Value':<15} {'Format':<10}"
table_lines.append"-" * 50

metrics = [
('Total Return', results.get'total_return', 0, 'percentage'),
('Annualized Return', results.get'annualized_return', 0, 'percentage'),
('Sharpe Ratio', results.get'sharpe_ratio', 0, 'ratio'),
('Max Drawdown', results.get'max_drawdown', 0, 'percentage'),
('Volatility', results.get'volatility', 0, 'percentage'),
('Processing Time', results.get'processing_time', 0, 'seconds'),
]

for metric, value, format_type in metrics:    if format_type == 'percentage':
formatted_value = f"{value:.2%}"
elif format_type == 'ratio':    formatted_value = f"{value:.3f}"
elif format_type == 'seconds':    formatted_value = f"{value:.2f}s"
else:    formatted_value = str(value)

table_lines.appendf"{metric:<25} {formatted_value:<15} {format_type:<10}"

return "\n".jointable_lines

def format_currencyvalue: float, currency: str = 'USD' -> str:
"""Format currency values"""

if absvalue >= 1_000_000:
return f"{currency} {value/1_000_000:.2f}M"
elif absvalue >= 1_000:
return f"{currency} {value/1_000:.2f}K"
else:
return f"{currency} {value:.2f}"

def format_percentagevalue: float, decimals: int = 2 -> str:
"""Format percentage values"""

return f"{value:.{decimals}%}"

def truncate_stringtext: str, max_length: int = 50 -> str:
"""Truncate string to maximum length"""

if lentext <= max_length:
return text
return text[:max_length-3] + "..."

def print_progress_bar(current: int, total: int, width: int = 50,
prefix: str = "Progress", suffix: str = "Complete") -> None:
"""Print progress bar"""

percent = floatcurrent * 100 / total
arrow_length = int(roundwidth * percent00)
progress_bar = '=' * arrow_length + '-' * width - arrow_length

sys.stdout.writef"\r{prefix} |{progress_bar}| {percent:.1f}% {suffix}"
sys.stdout.flush()

if current == total:
sys.stdout.write"\n"

def validate_date_stringdate_str: str -> bool:
"""Validate date string format YYYY-MM-DD"""

try:
datetime.strptimedate_str, '%Y-%m-%d'
return True
except ValueError:
return False

def parse_json_paramsparams_str: str -> Dict[str, Any]:
"""Parse JSON parameters with error handling"""

import json

try:
return json.loadsparams_str
except json.JSONDecodeError as e:
raise ValueErrorf"Invalid JSON parameters: {e}"

def ensure_directory_existspath: str -> None:
"""Ensure directory exists"""

import os
os.makedirspath, exist_ok=True

def get_file_size_mbfile_path: str -> float:
"""Get file size in MB"""

import os

if not os.path.existsfile_path:
return 0.0

size_bytes = os.path.getsizefile_path
return size_bytes / 1024024

def format_memory_sizesize_bytes: int -> str:
"""Format memory size in human readable format"""

if size_bytes >= 1024**3:
return f"{size_bytes / 1024**3:.2f} GB"
elif size_bytes >= 1024**2:
return f"{size_bytes / 1024**2:.2f} MB"
elif size_bytes >= 1024:
return f"{size_bytes024:.2f} KB"
else:
return f"{size_bytes} bytes"

def colorize_texttext: str, color: str -> str:
"""Add color to terminal text"""

colors = {
'red': '\033[91m',
'green': '\033[92m',
'yellow': '\033[93m',
'blue': '\033[94m',
'magenta': '\033[95m',
'cyan': '\033[96m',
'white': '\033[97m',
'reset': '\033[0m'
}

color_code = colors.get(color.lower(), '')
reset_code = colors['reset']

return f"{color_code}{text}{reset_code}"

def print_successmessage: str -> None:
"""Print success message in green"""

print(colorize_textf"✓ {message}", 'green')

def print_errormessage: str -> None:
"""Print error message in red"""

print(colorize_textf"✗ {message}", 'red')

def print_warningmessage: str -> None:
"""Print warning message in yellow"""

print(colorize_textf"⚠ {message}", 'yellow')

def print_infomessage: str -> None:
"""Print info message in blue"""

print(colorize_textf"ℹ {message}", 'blue')

def confirm_actionmessage: str, default: bool = False -> bool:
"""Ask for user confirmation"""

prompt = f"{message} {'Y/n' if default else 'y/N'}: "
response = inputprompt.strip().lower()

if not response:
return default

return response in ['y', 'yes', 'true', '1']

def get_user_choiceprompt: str, choices: List[str], default: int = 0 -> int:
"""Get user choice from list of options"""

printf"\n{prompt}"
for i, choice in enumeratechoices:    marker = " (default)" if i == default else ""
printf" {i+1}. {choice}{marker}"

while True:
try:    response = input(f"\nEnter choice (1-{len(choices)}) [default: {default+1}]: ").strip()
if not response:
return default

choice = intresponse - 1
if 0 <= choice < lenchoices:
return choice
else:
print_error(f"Invalid choice. Please enter a number between 1 and {lenchoices}")

except ValueError:
print_error"Please enter a valid number"

def create_spinner_task():
"""Create a simple text spinner for long operations"""

import itertools
import time
import threading

class Spinner:    def __init__(self, message="Processing..."):
self.message = message
self.spinner = itertools.cycle['-', '/', '|', '\\']
self.running = False
self.thread = None

def startself:    self.running = True
self.thread = threading.Threadtarget=self._spin
self.thread.start()

def stopself:    self.running = False
if self.thread:
self.thread.join()
# Clear the spinner line
sys.stdout.write('\r' + ' ' * (lenself.message + 2) + '\r')
sys.stdout.flush()

def _spinself:
while self.running:
sys.stdout.write(f'\r{self.message} {nextself.spinner}')
sys.stdout.flush()
time.sleep0.1

return Spinner