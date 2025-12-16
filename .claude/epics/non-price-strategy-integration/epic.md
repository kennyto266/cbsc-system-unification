---
name: non-price-strategy-integration
description: Complete integration of non-price data strategies into the main CBSC trading system
status: active
created: 2025-12-12T00:28:27Z
updated: 2025-12-16T03:00:00Z
github: https://github.com/kennyto266/cbsc-system-unification/issues/71
progress: 60%
---

# Epic: Non-Price Strategy Integration

## Overview

This epic will integrate the existing sophisticated non-price data strategies (HKMA macro data, sentiment analysis, alternative data) into the main CBSC quantitative trading system, providing users with unified access to all trading strategies through a single interface.

## Problem Statement

CBSC currently has powerful non-price trading strategies implemented in isolation (`src/non_price/`), but users cannot access them through the main dashboard (port 3004). This creates functional silos, incomplete user experience, data fragmentation, and missed opportunities for sophisticated multi-factor analysis.

## Solution Approach

We will implement a 5-phase integration plan that:
1. Exposes non-price strategies through the main API
2. Adds frontend dashboard components for visualization
3. Unifies data flows between price and non-price sources
4. Implements proper access controls and security
5. Provides comprehensive testing and monitoring

## Success Criteria

- 80% of active users access non-price strategies within 3 months
- 99.9% API uptime during trading hours
- <500ms response time for 95th percentile of requests
- 15% improvement in risk-adjusted returns for combined strategies

## Implementation Timeline

**Total Duration**: 18 weeks
- **Phase 1**: API Integration (4 weeks)
- **Phase 2**: Frontend Integration (6 weeks)
- **Phase 3**: Data Flow Unification (3 weeks)
- **Phase 4**: Security & Monitoring (2 weeks)
- **Phase 5**: Testing & Deployment (3 weeks)

## Dependencies

- Existing `src/non_price/` strategy system
- Main CBSC API (port 3004)
- Frontend dashboard framework
- Authentication and authorization system
- HKMA API for macroeconomic data

## Risk Mitigation

- Implement multiple fallback data sources for HKMA API reliability
- Phased rollout with performance monitoring
- Comprehensive user training and documentation
- Proof-of-concept validation before full implementation

## Team Allocation

- Backend Development: API integration and data flow unification
- Frontend Development: Dashboard components and visualization
- DevOps: Deployment pipeline and monitoring setup
- QA: Comprehensive testing across all phases
- Product: Project coordination and user acceptance testing

## Out of Scope

- Mobile application development
- Third-party strategy marketplace
- Machine learning model training infrastructure
- International market data integration beyond Hong Kong

## Key Deliverables

1. **Integrated API Endpoints**: RESTful and WebSocket interfaces for all non-price strategies
2. **Unified Dashboard**: Single interface for accessing all strategy types
3. **Combined Backtesting**: Framework for multi-factor strategy testing
4. **Security Framework**: Role-based access control and audit logging
5. **Monitoring System**: Real-time performance and data quality monitoring
6. **Documentation**: Complete user guides and technical documentation