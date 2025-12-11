# GitHub Issue Mapping - CBSC System Unification Epic

## Epic Information
- **Repository**: https://github.com/kennyto266/cbsc-system-unification
- **Epic Issue**: #11 - Epic: System Unification
- **Epic File**: `.claude/epics/system-unification/epic.md`
- **Sync Date**: 2025-12-10T02:20:00Z

## Task Mappings

### Completed GitHub Sync Tasks
| Original File | GitHub Issue | Task Title | Status |
|---------------|-------------|------------|---------|
| `001.md` → `14.md` | #14 | Setup Development Environment and API Gateway | ✅ Synced |
| `002.md` → `15.md` | #15 | Design Unified Data Model and Migration Tools | ✅ Synced |
| `003.md` → `17.md` | #17 | Implement Authentication and User Management Service | ✅ Synced |
| `004.md` → `18.md` | #18 | Build Frontend Foundation and Component Library | ✅ Synced |

### Remaining Local Tasks (Not Yet Synced)
| File | Task Title | Priority | Parallel |
|------|------------|----------|-----------|
| `005.md` | Migrate Core CBSC Strategy Management APIs | High | false |
| `006.md` | Implement Unified Dashboard and Monitoring UI | High | false |
| `007.md` | Build Testing Framework and Quality Assurance | Medium | true |
| `008.md` | Deploy Production Environment and Documentation | Medium | false |

## File Updates Applied

### 1. File Renames
- ✅ `001.md` → `14.md` (GitHub Issue #14)
- ✅ `002.md` → `15.md` (GitHub Issue #15)
- ✅ `003.md` → `17.md` (GitHub Issue #17)
- ✅ `004.md` → `18.md` (GitHub Issue #18)

### 2. Frontmatter Updates
All synced task files now include:
```yaml
github: https://github.com/kennyto266/cbsc-system-unification/issues/{issue_number}
updated: 2025-12-10T02:20:00Z
```

### 3. Epic File Updates
- ✅ Updated epic frontmatter with GitHub URL
- ✅ Updated epic timestamp to 2025-12-10T02:20:00Z
- ✅ Updated Tasks Created section with real issue numbers (#14, #15, #17, #18)
- ✅ Updated task dependency references to match new file names

### 4. Dependency Updates
Task dependencies have been updated:
- Task 15 depends on: `[14]` (was `[001]`)
- Task 17 depends on: `[14, 15]` (was `[001, 002]`)
- Task 18 depends on: `[14]` (was `[001]`)

## Current Repository Structure
```
.claude/epics/system-unification/
├── epic.md                    # Epic: System Unification
├── 014.md                     # GitHub Issue #14 ✅
├── 015.md                     # GitHub Issue #15 ✅
├── 017.md                     # GitHub Issue #17 ✅
├── 018.md                     # GitHub Issue #18 ✅
├── 005.md                     # Local task (not synced)
├── 006.md                     # Local task (not synced)
├── 007.md                     # Local task (not synced)
├── 008.md                     # Local task (not synced)
└── github-mapping.md          # This file
```

## Next Steps

### For Remaining Tasks (005-008)
To complete the GitHub sync, these tasks need to be created as GitHub issues:
1. Create GitHub issues for tasks 005-008
2. Rename the files to match the new issue numbers
3. Update their frontmatter with GitHub URLs
4. Update epic.md Tasks Created section

### Worktree Creation
A git worktree should be created for focused epic development:
```bash
git worktree add ../epic-cbsc-system-integration main
```

## Epic Progress
- **Total Tasks**: 8
- **GitHub Synced**: 4/8 (50%)
- **Local Only**: 4/8 (50%)
- **Next Sync**: Tasks 005-008 pending GitHub issue creation

---

*Last Updated: 2025-12-10T02:20:00Z*
*Repository: kennyto266/cbsc-system-unification*