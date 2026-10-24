import logging
import logging.handlers
import os
from pathlib import Path

def setup_logging():
"""设置结构化日志记录"""
log_level = getattr(logging, os.getenv'LOG_LEVEL', 'INFO'.upper())
log_file = Path'logs/quant_system.log'

# 确保日志目录存在
log_file.parent.mkdirexist_ok=True

# 创建logger
logger = logging.getLogger'quant_system'
logger.setLevellog_level

console_handler = logging.StreamHandler()
console_handler.setLevellog_level

file_handler = logging.handlers.RotatingFileHandler(
log_file, maxBytes=10*1024*1024, backupCount=5
)
file_handler.setLevellog_level

formatter = logging.Formatter(
'%asctimes - %names - %levelnames - %messages'
)
console_handler.setFormatterformatter
file_handler.setFormatterformatter

logger.addHandlerconsole_handler
logger.addHandlerfile_handler

return logger