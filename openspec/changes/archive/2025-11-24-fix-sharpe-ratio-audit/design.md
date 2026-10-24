# Design: Sharpe Ratio Calculation Fix and System Audit

## Context
The quantitative trading system has been operating with fundamentally incorrect Sharpe Ratio calculations, affecting strategy evaluation and risk assessment. Multiple mathematical errors were identified in the core calculation function.

## Goals / Non-Goals
- **Goals**:
  - Implement mathematically correct Sharpe Ratio calculations
  - Ensure all performance metrics are reliable and industry-standard
  - Maintain system integrity and scientific credibility
  - Provide transparent calculation methodology
- **Non-Goals**:
  - Preserve existing incorrect performance claims
  - Rush the fix without proper validation
  - Maintain backward compatibility with wrong calculations

## Decisions
- **Decision**: Use industry-standard financial libraries (empyrical, quantlib) as primary calculation methods
  - **Rationale**: These libraries are battle-tested, widely adopted, and mathematically sound
  - **Alternatives considered**: Custom implementation (higher risk), VectorBT only (limited validation)

- **Decision**: Implement multi-method validation approach
  - **Rationale**: Cross-validation ensures accuracy and builds confidence
  - **Alternatives considered**: Single method only (less robust), External audit only (costly)

- **Decision**: Full recalculation of all strategies
  - **Rationale**: Partial fixes would create inconsistent and unreliable results
  - **Alternatives considered**: Incremental fixes (risk of inconsistency), Cherry-pick validation (insufficient)

## Risks / Trade-offs
- **Risk**: Corrected calculations may invalidate "world-class" performance claims → **Mitigation**: Focus on scientific accuracy over marketing claims
- **Risk**: Extended downtime during recalculation → **Mitigation**: Parallel calculation systems, phased rollout
- **Risk**: User confusion about changed metrics → **Mitigation**: Transparent documentation, clear explanation of changes
- **Trade-off**: Accuracy vs. Speed → **Choice**: Prioritize accuracy with extended timeline

## Migration Plan
1. **Phase 1** (Week 1): Implement correct calculation functions and validation framework
2. **Phase 2** (Week 2): Parallel calculation system for strategy comparison
3. **Phase 3** (Week 3): Full recalculation of all 24,044 strategies
4. **Phase 4** (Week 4): Validation, documentation update, and deployment

## Open Questions
- Should we maintain historical (incorrect) results for comparison purposes?
- What is the minimum acceptable Sharpe Ratio threshold after correction?
- How will this affect existing trading decisions based on incorrect metrics?