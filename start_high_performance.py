#!/usr/bin/env python3
"""
启动高计算量策略优化系统
"""

import os
import sys
import logging

logger = logging.getLogger(__name__)

def safe_import_and_run():
    """Safely import and run the complete project system"""
    try:
        # 切换到正确的目录
        target_dir = r"C:\Users\Penguin8n\.cursor\CODEX 寫量化團隊"
        if not os.path.exists(target_dir):
            logger.error(f"Target directory does not exist: {target_dir}")
            return False

        os.chdir(target_dir)

        # Safely import and run the system
        module_name = "complete_project_system"
        if not os.path.exists(f"{module_name}.py"):
            logger.error(f"Module file not found: {module_name}.py")
            return False

        # Import the module safely
        spec = importlib.util.spec_from_file_location(module_name, f"{module_name}.py")
        if spec is None or spec.loader is None:
            logger.error(f"Could not load module spec for {module_name}")
            return False

        module = importlib.util.module_from_spec(spec)

        # Execute the module safely
        spec.loader.exec_module(module)

        logger.info(f"Successfully executed {module_name}")
        return True

    except ImportError as e:
        logger.error(f"Import error: {e}")
        return False
    except Exception as e:
        logger.error(f"Error executing system: {e}")
        return False

if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Import required module
    import importlib.util

    # Run the system safely
    success = safe_import_and_run()
    if not success:
        logger.error("Failed to start the high performance system")
        sys.exit(1)
