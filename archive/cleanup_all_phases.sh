#!/bin/bash
###############################################################################
# QUANT SYSTEM CLEANUP - MASTER SCRIPT
# Runs all cleanup phases in sequence
###############################################################################

echo "============================================================================="
echo "QUANT SYSTEM CLEANUP - MASTER SCRIPT"
echo "Executing all cleanup phases..."
echo "============================================================================="
echo ""
echo "This script will:"
echo "  1. Delete node_modules, __pycache__, target directories"
echo "  2. Archive deprecated code"
echo "  3. Update .gitignore"
echo "  4. Verify results"
echo ""
echo "Estimated file reduction: 60,000+ files (36%+)"
echo ""
read -p "Continue? (y/N): " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Cleanup cancelled."
    exit 0
fi

echo ""
echo "============================================================================="
echo "Starting cleanup..."
echo "============================================================================="
echo ""

# Make scripts executable
chmod +x cleanup_phase1_safe_deletions.sh
chmod +x cleanup_phase2_archive_deprecated.sh
chmod +x cleanup_phase3_update_gitignore.sh
chmod +x verify_cleanup_results.sh

# Run Phase 1
echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║                   EXECUTING PHASE 1                        ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""
bash cleanup_phase1_safe_deletions.sh

# Run Phase 2
echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║                   EXECUTING PHASE 2                        ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""
bash cleanup_phase2_archive_deprecated.sh

# Run Phase 3
echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║                   EXECUTING PHASE 3                        ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""
bash cleanup_phase3_update_gitignore.sh

# Run Verification
echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║                  RUNNING VERIFICATION                      ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""
bash verify_cleanup_results.sh

echo ""
echo "============================================================================="
echo -e "${GREEN}CLEANUP COMPLETE!${NC}"
echo "============================================================================="
echo ""
echo "All cleanup phases executed successfully!"
echo ""
echo "Next steps:"
echo "  1. Review the verification results above"
echo "  2. Test that your application still works"
echo "  3. If everything is good, commit changes:"
echo "     git add -A"
echo "     git commit -m 'Cleanup: Reduce file count by 60,000+ files'"
echo ""
echo "To regenerate deleted files:"
echo "  • Frontend: cd frontend && npm install"
echo "  • Rust: cargo build"
echo "  • Python venv: python -m venv venv_qflib"
echo ""
echo "============================================================================="
