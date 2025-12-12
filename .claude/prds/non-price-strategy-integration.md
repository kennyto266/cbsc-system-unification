---
name: non-price-strategy-integration
description: Complete integration of non-price data strategies into the main CBSC trading system
status: backlog
created: 2025-12-12T00:26:08Z
---

# PRD: Non-Price Strategy Integration

## Executive Summary

This PRD defines the complete integration of existing non-price data strategies (HKMA macro data, sentiment analysis, alternative data) into the main CBSC quantitative trading system. The integration will expose these powerful strategies through the main API, add frontend dashboard components, unify data flows, and implement proper access controls.

## Problem Statement

Currently, CBSC has sophisticated non-price trading strategies implemented but they exist in isolation:

- **Functional Silo**: Non-price strategies exist in `src/non_price/` but are not accessible through the main API
- **Incomplete User Experience**: Users cannot access macro-driven or sentiment-based strategies through the primary dashboard
- **Data Fragmentation**: Price and non-price data flows operate separately, limiting combined analysis capabilities
- **Missed Opportunities**: Powerful strategies using HKMA data, sentiment analysis, and alternative signals are underutilized

**Why Now**: The system has mature price-based strategies and user management, but lacks comprehensive multi-dimensional analysis capabilities that modern quantitative trading requires.

## User Stories

### Primary Personas

**1. Portfolio Manager (David)**
- Role: Manages multi-strategy quantitative portfolio
- Needs: Access to all strategy types through unified interface
- Pain Points: Must switch between systems to access macro/sentiment strategies

**2. Quantitative Analyst (Sarah)**
- Role: Develops and backtests trading strategies
- Needs: Unified data access for combined price+non-price analysis
- Pain Points: Manual data consolidation between different strategy systems

**3. System Administrator (Mike)**
- Role: Maintains trading infrastructure
- Needs: Centralized access control and monitoring
- Pain Points: Managing multiple isolated systems increases operational overhead

### Detailed User Stories

**Story 1: Unified Strategy Access**
> As a Portfolio Manager, I want to access all trading strategies (price, macro, sentiment) through the main dashboard so that I can make comprehensive investment decisions without switching interfaces.

**Acceptance Criteria:**
- Main dashboard displays all available strategy types
- Single login provides access to all strategies
- Strategy performance metrics are unified
- Real-time switching between strategy types

**Story 2: Combined Data Analysis**
> As a Quantitative Analyst, I want to combine price data with HKMA macro indicators and sentiment data so that I can create more sophisticated multi-factor strategies.

**Acceptance Criteria:**
- API provides combined price+non-price data endpoints
- Data timestamps are synchronized across sources
- Backtesting framework supports combined strategies
- Data quality metrics for all sources

**Story 3: Centralized Access Control**
> As a System Administrator, I want to manage access permissions for all strategies through a single system so that I can ensure security and compliance.

**Acceptance Criteria:**
- Single authentication system covers all strategies
- Role-based permissions for different strategy types
- Audit logs for all strategy access
- Security policies applied consistently

## Requirements

### Functional Requirements

**FR1: API Integration**
- Expose non-price strategy endpoints through main API (port 3004)
- RESTful endpoints for HKMA data, sentiment analysis, alternative data
- WebSocket support for real-time non-price signal updates
- Unified response formats across all strategy types

**FR2: Frontend Dashboard Integration**
- Add non-price strategy components to main dashboard
- Real-time display of macro indicators (HIBOR, monetary base, etc.)
- Sentiment analysis visualization and alerts
- Strategy comparison tools (price vs non-price performance)

**FR3: Data Flow Unification**
- Synchronized data ingestion across all sources
- Unified caching strategy for price and non-price data
- Common data quality validation framework
- Integrated backtesting capabilities

**FR4: Access Control & Security**
- Role-based permissions for different strategy types
- API rate limiting for external data sources
- Data encryption for sensitive macroeconomic data
- Audit trail for all strategy access and modifications

**FR5: Performance & Monitoring**
- Unified performance metrics across all strategies
- System health monitoring for integrated components
- Alert system for data quality issues
- Performance benchmarking tools

### Non-Functional Requirements

**NFR1: Performance**
- API response time < 200ms for cached data
- Real-time signal latency < 1 second
- Dashboard load time < 3 seconds
- Backtesting completion within 5 minutes for standard datasets

**NFR2: Scalability**
- Support 100+ concurrent users
- Handle 10,000+ API requests per minute
- Process real-time data from 50+ sources
- Horizontal scaling capability for increased load

**NFR3: Reliability**
- 99.9% uptime for trading hours
- Automatic failover for data source failures
- Data backup and recovery procedures
- Graceful degradation during high load

**NFR4: Security**
- OAuth 2.0 authentication for all API endpoints
- End-to-end encryption for sensitive data
- SQL injection and XSS protection
- Regular security audits and penetration testing

## Success Criteria

### Primary Metrics

**Technical Metrics:**
- API availability: 99.9% uptime during trading hours
- Response time: 95th percentile < 500ms
- Error rate: < 0.1% for all integrated endpoints
- Data quality score: > 95/100 for all sources

**Business Metrics:**
- Strategy adoption: 80% of active users access non-price strategies within 3 months
- User engagement: 50% increase in daily active users
- Portfolio performance: 15% improvement in risk-adjusted returns for combined strategies
- System efficiency: 40% reduction in manual data consolidation time

### Secondary Metrics

- User satisfaction score: > 4.5/5.0
- Support ticket reduction: 30% fewer issues related to system complexity
- Development velocity: 25% faster deployment of new multi-factor strategies
- Operational cost: 20% reduction through system consolidation

## Constraints & Assumptions

### Technical Constraints
- Must maintain backward compatibility with existing price-based strategies
- Cannot modify external HKMA API data formats
- Must comply with Hong Kong financial data regulations
- Limited to 4GB GPU memory for accelerated processing

### Business Constraints
- Must complete integration within Q1 2026
- Cannot increase operational costs by more than 15%
- Must maintain existing service level agreements
- Limited to existing development team resources

### Assumptions
- HKMA API will continue to be available and stable
- User base has sufficient technical expertise for multi-factor strategies
- Existing infrastructure can support increased load
- Market demand for sophisticated quantitative strategies will continue to grow

## Out of Scope

### Features Not Included
- Mobile application development
- Third-party strategy marketplace
- Machine learning model training infrastructure
- International market data integration (beyond Hong Kong)

### Limitations
- Will not replace existing price-based strategies
- Will not modify core authentication system architecture
- Will not implement custom hardware acceleration
- Will not create separate user interfaces for different user types

## Dependencies

### External Dependencies
- HKMA API availability and stability
- Yahoo Finance API for price data
- Redis for caching infrastructure
- PostgreSQL database system

### Internal Dependencies
- Existing user authentication system
- Current price-based strategy framework
- Database migration scripts
- Frontend build and deployment pipeline

### Team Dependencies
- Backend development team for API integration
- Frontend team for dashboard components
- DevOps team for deployment and monitoring
- QA team for comprehensive testing

## Implementation Timeline

### Phase 1: API Integration (4 weeks)
- Week 1-2: Create non-price strategy API endpoints
- Week 3: Implement WebSocket real-time data streaming
- Week 4: Integration testing and documentation

### Phase 2: Frontend Integration (6 weeks)
- Week 1-2: Dashboard component development
- Week 3-4: Real-time data visualization
- Week 5-6: User testing and refinement

### Phase 3: Data Flow Unification (3 weeks)
- Week 1: Synchronized data ingestion pipeline
- Week 2: Unified caching strategy
- Week 3: Backtesting framework integration

### Phase 4: Security & Monitoring (2 weeks)
- Week 1: Access control implementation
- Week 2: Monitoring and alerting setup

### Phase 5: Testing & Deployment (3 weeks)
- Week 1-2: Comprehensive testing (unit, integration, performance)
- Week 3: Production deployment and monitoring

## Risk Assessment

### High Risks
- **Data Source Reliability**: HKMA API availability issues
  - Mitigation: Implement multiple fallback data sources
- **Performance Impact**: Integration may slow existing systems
  - Mitigation: Phased rollout with performance monitoring

### Medium Risks
- **User Adoption**: Complex strategies may overwhelm users
  - Mitigation: Comprehensive training and documentation
- **Integration Complexity**: Technical challenges in system unification
  - Mitigation: Proof-of-concept validation before full implementation

### Low Risks
- **Security Vulnerabilities**: New attack vectors through integrated APIs
  - Mitigation: Regular security audits and penetration testing
- **Regulatory Compliance**: Data usage compliance issues
  - Mitigation: Legal review and compliance monitoring