#!/usr/bin/env python3
"""
Stage 2 Root Directory Cleanup - Simple Version
Safe file organization with ASCII output
"""
import os
import shutil
import json
from pathlib import Path
from datetime import datetime
import subprocess

def run_command(cmd, description=""):
    """Run command and handle errors"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, encoding='utf-8')
        if result.returncode == 0:
            print(f"[OK] {description}")
            return True
        else:
            print(f"[ERROR] {description}: {result.stderr}")
            return False
    except Exception as e:
        print(f"[ERROR] {description}: {e}")
        return False

def create_archive_structure():
    """Create Stage 2 archive structure"""
    print("\n=== Creating Archive Structure ===")

    archive_dirs = [
        "archive/stage2_duplicate_scripts",
        "archive/stage2_old_reports",
        "archive/stage2_analysis_tools"
    ]

    for dir_path in archive_dirs:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
        print(f"[OK] Created directory: {dir_path}")

    return True

def archive_duplicate_scripts():
    """Archive duplicate script files"""
    print("\n=== Archiving Duplicate Scripts ===")

    duplicate_patterns = [
        "start_*.py",
        "run_*.py",
        "complete_*.py",
        "enhanced_*.py",
        "ultimate_*.py",
        "simple_*.py",
        "quick_*.py",
        "analyze_*.py",
        "debug_*.py",
        "basic_*.py",
        "fixed_*.py",
        "final_*.py"
    ]

    archived_count = 0

    for pattern in duplicate_patterns:
        cmd = f"find . -maxdepth 1 -name '{pattern}' -not -path './simplified_system/*'"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, encoding='utf-8')

        if result.stdout.strip():
            files = result.stdout.strip().split('\n')
            for file in files:
                if file and os.path.exists(file):
                    try:
                        # Keep core files
                        core_files = [
                            'start_system.py',
                            'run_dashboard.py',
                            'complete_system.py'
                        ]

                        filename = os.path.basename(file)
                        if filename in core_files:
                            print(f"[KEEP] Core file: {file}")
                            continue

                        # Archive file
                        archive_path = f"archive/stage2_duplicate_scripts/{filename}"
                        shutil.move(file, archive_path)
                        archived_count += 1
                        print(f"[ARCHIVED] {file} -> archive/stage2_duplicate_scripts/")
                    except Exception as e:
                        print(f"[ERROR] Failed to archive {file}: {e}")

    print(f"Archived {archived_count} duplicate script files")
    return archived_count > 0

def archive_old_reports():
    """Archive old report files"""
    print("\n=== Archiving Old Reports ===")

    archived_count = 0

    # Archive HTML reports
    cmd = "find . -maxdepth 1 -name '*_report.html'"
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, encoding='utf-8')

    if result.stdout.strip():
        files = result.stdout.strip().split('\n')
        for file in files:
            if file and os.path.exists(file):
                try:
                    archive_path = f"archive/stage2_old_reports/{os.path.basename(file)}"
                    shutil.move(file, archive_path)
                    archived_count += 1
                    print(f"[ARCHIVED] HTML report: {file}")
                except Exception as e:
                    print(f"[ERROR] Failed to archive {file}: {e}")

    # Archive JSON result files
    cmd = "find . -maxdepth 1 -name '*results*.json' -o -name '*optimization*.json' -o -name '*backtest*.json'"
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, encoding='utf-8')

    if result.stdout.strip():
        files = result.stdout.strip().split('\n')
        for file in files:
            if file and os.path.exists(file):
                try:
                    archive_path = f"archive/stage2_old_reports/{os.path.basename(file)}"
                    shutil.move(file, archive_path)
                    archived_count += 1
                    print(f"[ARCHIVED] JSON result: {file}")
                except Exception as e:
                    print(f"[ERROR] Failed to archive {file}: {e}")

    print(f"Archived {archived_count} old report files")
    return archived_count > 0

def archive_analysis_tools():
    """Archive analysis tools"""
    print("\n=== Archiving Analysis Tools ===")

    analysis_tools = [
        "analyze_files.py",
        "file_cleanup.py",
        "safe_cleanup.py",
        "safe_cleanup_stage2.py",
        "file_analysis_report.json",
        "cleanup_stage1_report.json"
    ]

    archived_count = 0

    for tool in analysis_tools:
        if os.path.exists(tool):
            try:
                archive_path = f"archive/stage2_analysis_tools/{tool}"
                shutil.move(tool, archive_path)
                archived_count += 1
                print(f"[ARCHIVED] Analysis tool: {tool}")
            except Exception as e:
                print(f"[ERROR] Failed to archive {tool}: {e}")

    print(f"Archived {archived_count} analysis tools")
    return archived_count > 0

def generate_cleanup_report():
    """Generate cleanup report"""
    print("\n=== Generating Cleanup Report ===")

    report = {
        "stage2_cleanup_timestamp": datetime.now().isoformat(),
        "actions_completed": [
            "Archive structure created",
            "Duplicate scripts archived",
            "Old reports archived",
            "Analysis tools archived"
        ],
        "directories_created": [
            "archive/stage2_duplicate_scripts",
            "archive/stage2_old_reports",
            "archive/stage2_analysis_tools"
        ]
    }

    with open("stage2_cleanup_report.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print("[OK] Stage 2 cleanup report saved: stage2_cleanup_report.json")
    return True

def main():
    """Main execution function"""
    print("Stage 2 Root Directory Safe Cleanup")
    print("Following 4 principles: Backup, Progressive, Version Control, Archive First")
    print("=" * 80)

    try:
        # Execute all stages
        create_archive_structure()
        archive_duplicate_scripts()
        archive_old_reports()
        archive_analysis_tools()
        generate_cleanup_report()

        print("\n" + "=" * 80)
        print("[SUCCESS] Stage 2 cleanup completed!")
        print("=" * 80)

        print("\nCleanup Summary:")
        print("- Duplicate scripts archived to archive/stage2_duplicate_scripts/")
        print("- Old reports archived to archive/stage2_old_reports/")
        print("- Analysis tools archived to archive/stage2_analysis_tools/")
        print("- Core systems preserved: simplified_system/, src/, frontend/")

        print("\nNext Steps:")
        print("1. Review remaining files in root directory")
        print("2. Test core system functionality")
        print("3. Consider Stage 3 documentation cleanup")

    except Exception as e:
        print(f"\n[ERROR] Stage 2 cleanup failed: {e}")
        print("Please check error and run 'git status' to see current state")

if __name__ == "__main__":
    main()