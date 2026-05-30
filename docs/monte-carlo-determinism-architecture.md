# Monte Carlo Determinism & Seed Control Architecture

**Document ID**: MC-DET-ARCH-001  
**Version**: 1.0  
**Status**: Proposed Architecture  
**Date**: 2026-05-29  
**Audience**: Engineers, GRC Analysts, Risk Methodology Teams

## Executive Summary

This document specifies a tool-agnostic architecture for deterministic Monte Carlo simulations in quantitative risk analysis. The architecture ensures complete reproducibility of risk simulations for enterprise GRC reporting, audit verification, and methodological rigor while maintaining flexibility across implementation technologies.

## 1. Problem Statement

### 1.1 Current Gaps

**RiskShard's current Monte Carlo implementation lacks:**
1. **Scenario-level seed configuration** - Seeds only configurable via CLI
2. **Deterministic default behavior** - Defaults to non-deterministic system-time seeding
3. **Complete audit trails** - No seed recording in reports
4. **RNG isolation** - Shared random state across simulations
5. **Enterprise reproducibility** - Cannot guarantee identical results for verification

### 1.2 Enterprise Impact

**GRC & Compliance Risks:**
- **SOC 2/ISO 27001**: Incomplete audit trails violate control requirements
- **FAIR Methodology**: Reproducibility principle not met
- **Regulatory Reporting**: Cannot verify quarterly risk assessments
- **Audit Challenges**: External auditors cannot validate risk calculations

**Technical Risks:**
- **Correlated Randomness**: Single RNG instance shared across portfolio scenarios
- **State Leakage**: Simulation A affects unrelated simulation B
- **Order Dependence**: Portfolio results depend on scenario processing order
- **Verification Impossibility**: Cannot reproduce results from report metadata alone

## 2. Core Principles

### Principle 1: Explicit Determinism by Default
> All simulations must be deterministic when a seed is provided. Non-deterministic mode requires explicit opt-in.

**Rationale**: Enterprise risk reporting requires reproducibility. Default behavior should favor auditability over convenience.

### Principle 2: Complete Seed Audit Trail
> Every simulation must record sufficient metadata to enable exact reproduction.

**Rationale**: Audit trails must support third-party verification without access to original execution environment.

### Principle 3: RNG Instance Isolation
> Each simulation gets its own isolated random number generator instance.

**Rationale**: Prevents correlated randomness and state leakage between unrelated simulations.

### Principle 4: Configuration Hierarchy
> Clear precedence rules for seed resolution across configuration sources.

**Rationale**: Eliminates ambiguity in seed selection across different deployment scenarios.

## 3. Architecture Overview

### 3.1 High-Level Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Configuration  │    │   RNG Factory   │    │  Simulation     │
│  Sources        │───▶│   & Isolation   │───▶│  Engine         │
│  - CLI          │    │   Layer         │    │  - PERT         │
│  - Scenario     │    │   - MT19937     │    │  - Triangular   │
│  - Env Vars     │    │   - PCG         │    │  - Lognormal    │
│  - Config Files │    │   - CryptoRNG   │    │                 │
└─────────────────┘    └─────────────────┘    └─────────┬───────┘
                                                        │
                                                        ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Audit &        │    │   Reports &     │    │  Verification   │
│  Logging        │◀───│   Metadata      │◀───│  Tools          │
│  - Seed Usage   │    │  - Seed Proven. │    │  - Reproduction │
│  - RNG State    │    │  - RNG State    │    │  - Validation   │
│  - Timestamps   │    │  - Parameters   │    │  - Debugging    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### 3.2 Seed Resolution Hierarchy

```
Priority 1: Command-line argument (--seed 42)
Priority 2: Environment variable (RISKSHARD_SEED=42)
Priority 3: Scenario metadata (seed_mode: explicit)
Priority 4: Configuration file defaults
Priority 5: System-generated deterministic seed
Priority 6: Non-deterministic mode (explicit --no-seed)
```

## 4. Core Components Specification

### 4.1 Seed Specification Data Structure

**Tool-Agnostic YAML/JSON Schema**:
```yaml
# Scenario metadata extension
metadata:
  name: "Enterprise Risk Scenario"
  version: "1.0"
  
  # Simulation determinism configuration
  simulation:
    # Seed mode: explicit | generated | nondeterministic
    seed_mode: "explicit"
    
    # Required if mode=explicit
    seed_value: 123456789
    
    # RNG algorithm identifier
    seed_algorithm: "mt19937"
    
    # Isolation strategy
    rng_isolation: "strict"  # strict | shared | correlated
    
    # For generated seeds
    seed_generation:
      method: "scenario_hash"  # scenario_hash | timestamp | crypto
      salt: "2025-Q3-report"   # Optional versioning salt
      
    # Validation constraints
    validation:
      require_determinism: true
      allow_nondeterministic: false
```

**Alternative: Generated Seed Configuration**:
```yaml
metadata:
  simulation:
    seed_mode: "generated"
    seed_base: "deterministic_from_content"
    generation_parameters:
      hash_algorithm: "sha256"
      include_fields: ["frequency", "impact", "metadata.name"]
      exclude_fields: ["metadata.version"]  # Allow version changes
```

### 4.2 RNG Factory Interface

**Abstract Interface Definition**:
```typescript
// TypeScript-style interface for clarity
interface RandomNumberGeneratorFactory {
  // Create RNG with explicit seed
  create(seed: SeedSpecification): IsolatedRNG;
  
  // Create deterministic RNG with system-generated seed
  createDeterministic(): IsolatedRNG;
  
  // Create non-deterministic RNG (time-based)
  createNondeterministic(): IsolatedRNG;
  
  // Validate seed specification
  validateSeed(spec: SeedSpecification): ValidationResult;
  
  // Get supported algorithms
  getSupportedAlgorithms(): string[];
}

interface IsolatedRNG {
  // Core sampling methods
  nextFloat(): number;           // [0, 1)
  nextBeta(alpha: number, beta: number): number;
  nextTriangular(low: number, high: number, mode: number): number;
  
  // State management
  getState(): RNGState;
  setState(state: RNGState): void;
  clone(): IsolatedRNG;
  
  // Stream management (for parallel/correlated execution)
  getStreamId(): number;
  createDerivedStream(streamId: number): IsolatedRNG;
}

interface SeedSpecification {
  mode: "explicit" | "generated" | "nondeterministic";
  value?: number | string;  // Number for explicit, string hash for generated
  algorithm: string;
  isolation: "strict" | "shared" | "correlated";
  provenance?: SeedProvenance;
}

interface RNGState {
  algorithm: string;
  stateData: any;  // Algorithm-specific serialization
  sequenceNumber: number;  // Number of values generated
  checksum: string;  // For integrity verification
}
```

### 4.3 Simulation Execution Models

#### Model A: Independent Randomness (Default)
```
For each scenario in portfolio:
    seed = hash(base_seed + scenario_index + scenario_fingerprint)
    rng = factory.create({seed, algorithm: "mt19937", isolation: "strict"})
    results = run_simulation(scenario, rng)
    
Result: Each scenario has independent, reproducible randomness
```

#### Model B: Correlated Randomness (Explicit)
```
rng = factory.create({seed: base_seed, isolation: "shared"})
For each scenario in portfolio:
    results = run_simulation(scenario, rng)  // Same RNG instance
    
Result: Scenarios share RNG state, creating controlled correlation
```

#### Model C: Block Randomness (Advanced)
```
base_rng = factory.create({seed: base_seed, isolation: "strict"})
For each scenario:
    scenario_seed = base_rng.nextInt()  // Derive from base RNG
    scenario_rng = factory.create({seed: scenario_seed, isolation: "strict"})
    results = run_simulation(scenario, scenario_rng)
    
Result: Reproducible with statistical independence, seed derivation traceable
```

### 4.4 Report Metadata Specification

**Complete Reproduction Metadata**:
```json
{
  "report_type": "monte_carlo_simulation",
  "timestamp": "2026-05-29T10:30:00Z",
  
  "reproducibility": {
    "deterministic": true,
    "seed_used": 123456789,
    
    "seed_provenance": {
      "source": "scenario_metadata",
      "scenario_hash": "a1b2c3d4e5f6...",
      "generated_at": "2026-05-29T10:30:00Z",
      "algorithm": "mt19937",
      "isolation_mode": "strict"
    },
    
    "rng_state": {
      "initial_state": "0x1234567890abcdef...",
      "final_state": "0xfedcba0987654321...",
      "values_generated": 10000,
      "algorithm_version": "mt19937-64/2013"
    },
    
    "simulation_parameters": {
      "trials": 10000,
      "distribution": "pert",
      "confidence": 4,
      "scenario_order": ["scenario_a.yaml", "scenario_b.yaml"],
      "trial_sequence": "sequential",
      "portfolio_model": "independent_randomness"
    },
    
    "reproduction_command": "risk_shard reproduce --seed 123456789 --trials 10000 --scenarios scenario_a.yaml scenario_b.yaml"
  },
  
  "verification": {
    "result_hash": "sha256:abc123...",
    "signature": "optional_crypto_signature",
    "audit_log_reference": "audit-2026-05-29-103000"
  }
}
```

## 5. Implementation Guidelines

### 5.1 Technology-Agnostic Requirements

**Any implementation must provide**:
1. **Seed persistence** - Store seed with results
2. **RNG isolation** - Prevent state leakage
3. **Deterministic execution** - Same inputs → same outputs
4. **Audit trail** - Log seed usage and RNG state
5. **Verification support** - Enable result reproduction

**Implementation options**:
- **Python**: `random.Random` with custom seeding, `numpy.random.Generator`
- **JavaScript**: `seedrandom` library, Web Crypto API for seeds
- **Java**: `java.util.Random`, `java.security.SecureRandom`
- **R**: `set.seed()`, `rng` package for multiple streams
- **C++**: `<random>` library with custom distributions

### 5.2 Configuration Management

**Configuration File Example** (`~/.config/riskshard/defaults.yaml`):
```yaml
simulation:
  # Default behavior
  default_seed_mode: "generated"
  require_determinism: true
  
  # RNG configuration
  rng_algorithm: "mt19937"
  rng_isolation: "strict"
  
  # Seed generation
  seed_generation:
    method: "scenario_hash"
    hash_algorithm: "sha256"
    salt: "${ORG_ID}-${REPORT_PERIOD}"
    
  # Validation rules
  validation:
    min_seed_value: 1
    max_seed_value: 4294967295  # 2^32 - 1
    disallow_common_seeds: [0, 1, 42, 123, 123456789]
    require_audit_logging: true
    
  # Performance tuning
  performance:
    rng_cache_size: 100
    state_serialization: false  # Trade-off: performance vs. debug
    parallel_streams: 4

reports:
  include_reproduction_metadata: true
  store_rng_state: false  # Privacy/security consideration
  verification_hash: "sha256"
  
audit:
  log_seed_usage: true
  log_rng_state_changes: false  # Verbose debugging only
  retention_days: 365
  encryption_required: true
```

### 5.3 Enterprise Integration Patterns

#### Pattern 1: Multi-Tenant Isolation
```yaml
# Tenant-specific configuration
tenants:
  tenant_a:
    seed_namespace: "tenant_a"
    seed_salt: "salt_tenant_a_${YEAR_QTR}"
    rng_algorithm: "mt19937"
    
  tenant_b:
    seed_namespace: "tenant_b"
    seed_salt: "salt_tenant_b_${YEAR_QTR}"
    rng_algorithm: "pcg64"  # Different algorithm per tenant
```

#### Pattern 2: Regulatory Compliance
```yaml
compliance:
  soc2:
    audit_trail_required: true
    seed_logging_required: true
    retention_period_days: 90
    
  iso27001:
    integrity_checks_required: true
    access_controls_required: true
    
  gdpr:
    anonymize_seeds: false  # Seeds are not PII
    right_to_explanation: true  # Must explain simulation results
```

#### Pattern 3: High-Performance Batch Processing
```yaml
batch_processing:
  strategy: "stream_parallel"
  stream_count: 8
  chunk_size: 1000
  
  # Seed derivation for parallel streams
  seed_derivation:
    base_seed: "${BATCH_ID}"
    stream_salt: "stream_${STREAM_ID}"
    
  # Result aggregation
  aggregation:
    method: "statistical_merge"
    preserve_determinism: true
```

## 6. Verification & Validation

### 6.1 Reproduction Testing

**Test Suite Requirements**:
```yaml
tests:
  determinism:
    - name: "same_seed_same_results"
      description: "Identical seed produces bit-identical results"
      tolerance: "exact"  # No floating-point tolerance
      
    - name: "different_seed_different_results"
      description: "Different seeds produce statistically different results"
      tolerance: "ks_test p < 0.01"
      
    - name: "seed_independence"
      description: "Simulations with isolated RNGs produce independent results"
      test: "correlation_test r < 0.01"
      
    - name: "reproduction_from_metadata"
      description: "Can reproduce results from report metadata alone"
      requirement: "critical"
```

**Verification Command Interface**:
```bash
# Basic reproduction
risk_shard reproduce --report report.json

# With validation
risk_shard verify --report report.json --tolerance 0.0001

# Audit trail inspection
risk_shard audit --since 2026-01-01 --tenant tenant_a

# Seed management
risk_shard seeds generate --scenario scenario.yaml --method hash
risk_shard seeds validate --seed 123456789
```

### 6.2 Statistical Validation

**Required Statistical Tests**:
1. **Kolmogorov-Smirnov Test**: Verify distribution shape consistency
2. **Chi-Square Test**: Verify frequency distribution
3. **Autocorrelation Test**: Verify independence of samples
4. **Seed Collision Test**: Verify unique seeds produce unique sequences

**Validation Report Example**:
```json
{
  "validation": {
    "determinism": {
      "passed": true,
      "bit_identical": true,
      "floating_point_variance": 0.0
    },
    
    "statistical": {
      "ks_test_p_value": 0.85,
      "chi_square_p_value": 0.72,
      "autocorrelation_lag1": 0.003,
      "distribution_mean_error": 0.0001
    },
    
    "reproduction": {
      "successful": true,
      "execution_time_diff": "0.5s",
      "memory_usage_diff": "2MB"
    }
  }
}
```

## 7. Migration & Adoption

### 7.1 Phased Implementation

**Phase 1: Foundation** (Weeks 1-2)
- Add seed parameter to simulation APIs (backward compatible)
- Implement basic RNG isolation
- Add seed recording to reports (optional)

**Phase 2: Determinism by Default** (Weeks 3-4)
- Change default to deterministic generated seeds
- Add scenario metadata seed support
- Implement seed validation and logging

**Phase 3: Enterprise Features** (Weeks 5-8)
- Audit trail integration
- Multi-tenant seed isolation
- Cryptographic seed generation
- Compliance reporting

**Phase 4: Advanced Features** (Weeks 9-12)
- Parallel execution support
- RNG state checkpoint/restore
- Third-party verification tools
- Performance optimization

### 7.2 Backward Compatibility

**Compatibility Matrix**:
| Feature | Old Behavior | New Behavior | Migration Path |
|---------|-------------|--------------|----------------|
| No seed specified | Non-deterministic | Generated deterministic seed | Config flag to restore old behavior |
| CLI --seed | Single RNG shared | Isolated RNG per scenario | Automatic, transparent |
| Scenario metadata | No seed support | Optional seed specification | Add metadata field |
| Reports | No seed info | Complete reproduction metadata | New report format optional |

**Migration Tools**:
```bash
# Convert old scenarios to include seed metadata
risk_shard migrate --scenarios-dir ./scenarios --add-seeds

# Validate migration
risk_shard validate-migration --before old_report.json --after new_report.json

# Generate compliance report
risk_shard compliance-report --since-migration 2026-05-01
```

## 8. Security Considerations

### 8.1 Threat Model

**Assets to protect**:
1. **Seed values** - Could reveal simulation patterns if predictable
2. **RNG state** - Could allow prediction of future random values
3. **Audit logs** - Contain sensitive operational information
4. **Report metadata** - Could be used to reverse-engineer risk models

**Threats**:
- **T1**: Attacker predicts future simulation results
- **T2**: Attacker deduces sensitive information from seed patterns
- **T3**: Attacker manipulates seeds to produce desired results
- **T4**: Attacker exhausts seed space causing collisions

### 8.2 Security Controls

**Required Controls**:
```yaml
security:
  seed_generation:
    use_crypto_rng_for_seeds: true
    min_entropy_bits: 128
    reseed_interval: 1000000
    
  access_control:
    seed_read_permission: "analyst"
    seed_write_permission: "admin"
    audit_log_access: "auditor"
    
  logging:
    encrypt_audit_logs: true
    mask_seeds_in_logs: false  # Seeds not considered sensitive
    log_integrity_checks: true
    
  validation:
    validate_seed_source: true
    rate_limit_seed_requests: "100/hour"
    detect_seed_manipulation: true
```

## 9. Performance Considerations

### 9.1 Performance Targets

**Baseline Requirements**:
- **RNG initialization**: < 1ms per instance
- **State serialization**: < 0.5ms per instance
- **Memory overhead**: < 1KB per RNG instance
- **Throughput**: Support 1000+ concurrent simulations

**Optimization Strategies**:
1. **RNG instance pooling** for frequent small simulations
2. **Lazy state serialization** only when needed for audit
3. **Stream-based RNGs** for parallel execution
4. **Cached seed derivation** for repeated scenarios

### 9.2 Scalability Patterns

**Small-scale** (< 100 scenarios):
- Simple isolated RNG per scenario
- In-memory state management
- Synchronous execution

**Medium-scale** (100-10,000 scenarios):
- RNG instance pooling with LRU cache
- Batch seed generation
- Parallel execution with stream isolation

**Large-scale** (> 10,000 scenarios):
- Distributed RNG services
- Seed derivation trees
- Statistical sampling instead of full reproduction

## 10. Compliance & Standards

### 10.1 Standards Alignment

**FAIR Methodology**:
- **Principle**: "Results should be reproducible given the same inputs"
- **Implementation**: Complete seed audit trail, deterministic execution

**NIST SP 800-90A**:
- **Requirement**: "Random number generators must be deterministic from seed"
- **Implementation**: Use NIST-approved RNG algorithms, seed validation

**ISO/IEC 27001**:
- **Control A.12**: "Operations security must ensure integrity"
- **Implementation**: Audit logging, access controls, integrity checks

**SOC 2 Type II**:
- **Criteria CC6.1**: "Logical access security"
- **Implementation**: Role-based seed access, audit trails

### 10.2 Compliance Evidence

**Required Artifacts**:
1. **Seed usage logs** with timestamps and provenance
2. **RNG algorithm documentation** and validation certificates
3. **Reproduction test results** demonstrating determinism
4. **Access control configuration** for seed management
5. **Audit trail samples** for external review

**Compliance Reporting**:
```yaml
compliance_reports:
  frequency: "quarterly"
  contents:
    - seed_usage_statistics
    - reproduction_success_rate
    - audit_log_completeness
    - security_incident_report
  recipients:
    - internal_audit
    - risk_committee
    - external_auditors
```

## 11. Glossary

**Deterministic Simulation**: A simulation that produces identical results when run with identical inputs and seed.

**Seed**: A value used to initialize a random number generator, determining the entire sequence of "random" values.

**RNG (Random Number Generator)**: An algorithm that produces a sequence of numbers that appear random.

**RNG Isolation**: The practice of using separate RNG instances for different simulations to prevent state leakage.

**Seed Provenance**: Metadata describing the origin and generation method of a seed value.

**Reproduction Metadata**: Information stored with simulation results that enables exact reproduction.

**Audit Trail**: A secure log of all seed usage and simulation executions for compliance purposes.

**Stream Isolation**: Technique for creating statistically independent random number sequences from a single seed.

## 12. References

1. **FAIR Institute** - Factor Analysis of Information Risk Methodology
2. **NIST SP 800-90A** - Recommendation for Random Number Generation
3. **ISO/IEC 27001:2022** - Information security management
4. **SOC 2 Type II** - Service Organization Control reporting
5. **Matsumoto & Nishimura (1998)** - Mersenne Twister RNG algorithm
6. **O'Neill (2014)** - PCG: A Family of Simple Fast Space-Efficient Random Number Generators

## 13. Revision History

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 1.0 | 2026-05-29 | Initial architecture specification | Systems Audit Team |
| 0.9 | 2026-05-28 | Draft for review | Engineering Team |
| 0.8 | 2026-05-27 | Initial audit findings | Risk Methodology Team |

## 14. Approval

| Role | Name | Signature | Date |
|------|------|-----------|------|
| Chief Risk Officer | | | |
| Head of Engineering | | | |
| GRC Compliance Lead | | | |
| Systems Architect | | | |

---

**Document Control**: This document is controlled. Unauthorized distribution prohibited.  
**Classification**: Internal Architecture Specification  
**Retention**: Permanent  
**Review Cycle**: Annual review required, or after significant architecture changes.
