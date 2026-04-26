# Parallel Subagent Execution Plan for PPA12 Testing Implementation

## Executive Summary

**Objective**: Implement comprehensive test suite for 12 PPA12 datasets while protecting context and accelerating wall-clock time through safe parallel subagent execution.

**Strategy**: Decompose work into 4 independent workstreams that can execute in parallel, with atomic commits providing rollback points and validation gates between stages.

**Expected Time Savings**: 60-70% reduction in wall-clock time (4 parallel agents vs sequential execution)

---

## 1. Work Breakdown & Independence Analysis

### Phase 1: Foundation & Corrections (Prerequisite)
**Sequential - Must Complete First**

| Task | Description | Why Sequential | Output |
|------|-------------|----------------|--------|
| 1A | Correct np2 metadata | Affects all downstream test expectations | `np2_test_metadata.json` |
| 1B | Document e_dv_pp wider spike | Needed for proposition analysis | Notes added to metadata |
| 1C | Document e_w_a dual spikes | Needed for multi-peak design | Notes added to metadata |

**Atomic Commit**: `fix(metadata): correct np2 expectations and document spike patterns`

---

### Phase 2: Parallel Design Analysis (4 Independent Subagents)

These can run **FULLY IN PARALLEL** because they operate on different problem domains with no shared state:

#### **Subagent A: Wider Interior Spike Propositions (e_dv_pp)**
**Independence**: Analyzes algorithm design options, no code modification
**Output**: `docs/WIDER_SPIKE_PROPOSITIONS.md`
**Context Safety**: Read-only analysis, cannot conflict with other work

**Deliverables**:
1. **Proposition 1**: Iterative spike removal approach
   - For: Detects adjacent/wider spikes incrementally
   - Against: Multiple detection passes, complexity
2. **Proposition 2**: Wider tolerance thresholds
   - For: Simple parameter adjustment
   - Against: May reduce sensitivity for other datasets
3. **Proposition 3**: Multi-peak detection algorithm
   - For: Comprehensive solution
   - Against: Requires significant algorithm changes
4. **Proposition 4**: Accept current behavior
   - For: No code changes, document limitation
   - Against: May miss wider spikes
5. **Recommendation**: Evidence-based choice with data support

**Atomic Commit**: `docs(analysis): add propositions for wider interior spike detection`

---

#### **Subagent B: Multi-Peak Interior Detection Design (e_w_a)**
**Independence**: Designs new algorithm feature, no shared code paths
**Output**: `docs/MULTI_PEAK_INTERIOR_DESIGN.md`
**Context Safety**: Design document only, no implementation

**Deliverables**:
1. **Requirements Analysis**:
   - User wants to specify expected number of spikes
   - Should detect BOTH spikes for e_w_a
   - GitHub issue created for auto-detection future work
2. **API Design**:
   - `InteriorConfig.expected_spikes: int | None` parameter
   - `InteriorResult.spikes_detected: list[float]` for all detected eps*
3. **Algorithm Approach**:
   - Find N distinct peaks in mass curve
   - Validate each peak meets excess_ratio threshold
   - Return list of tolerances, one per spike
4. **Test Strategy**:
   - e_w_a: test for 2 spikes detected
   - Existing tests: default to 1 spike (backward compatible)
5. **Implementation Plan**:
   - Step-by-step with atomic commits

**Atomic Commit**: `docs(design): multi-peak interior detection specification`

---

#### **Subagent C: Test Data Organization & Fixtures**
**Independence**: Works only on `tests/conftest.py`, no algorithm changes
**Output**: Updated `tests/conftest.py` with all 12 datasets
**Context Safety**: Isolated to test infrastructure

**Deliverables**:
1. **Validate existing fixtures** (A_He, e_dv_pp, e_dv_ap, np1) - already done
2. **Add 8 new fixtures**:
   ```python
   @pytest.fixture
   def np2_test_case() -> dict: ...
   def e_w_p1_test_case() -> dict: ...
   def e_w_p2_test_case() -> dict: ...
   def e_w_a_test_case() -> dict: ...
   def vx_test_case() -> dict: ...
   def vy_test_case() -> dict: ...
   def vz_test_case() -> dict: ...
   def w_const_test_case() -> dict: ...
   ```
3. **Update `all_ppa12_test_cases` fixture** with complete dataset list
4. **Add documentation** for each fixture with:
   - Distribution characteristics
   - Expected stickiness patterns
   - Special notes (failed fits, multi-spike, etc.)

**Atomic Commit**: `test(fixtures): add 8 new PPA12 dataset fixtures`

---

#### **Subagent D: Test Categorization & Coverage Matrix**
**Independence**: Plans test structure, no code implementation
**Output**: `docs/TEST_COVERAGE_MATRIX.md`
**Context Safety**: Planning document, no code conflicts

**Deliverables**:
1. **Dataset Categorization**:
   - Bilateral boundary + interior (4 datasets)
   - Lower boundary + interior (1 dataset)
   - Upper boundary + interior (1 dataset)
   - Interior only (1 dataset)
   - No stickiness / negative controls (2 datasets)
   - Out-of-bounds / data quality (4 datasets)

2. **Test Coverage Matrix**:
   | Test Scenario | Datasets | Purpose |
   |---------------|----------|---------|
   | Bilateral strong | e_dv_pp, e_w_a | Validate bilateral detection |
   | Bilateral weak | e_dv_ap, A_He | Sub-percent sensitivity |
   | Single-sided lower | e_w_p1 | Asymmetric detection |
   | Single-sided upper | e_w_p2, w_const | Upper-only detection |
   | Extreme concentration | np2 (57%), e_w_p2 (37%) | Extreme stickiness |
   | Interior only | np2 | No boundary, yes interior |
   | Negative controls | vy, vz | False positive prevention |
   | Out-of-bounds | np1, np2, vx, w_const | Bounds validation |

3. **Test Organization Recommendations**:
   - Parameterized tests for similar patterns
   - Individual tests for unique cases
   - Grouping by algorithm feature (boundary/interior/combined)

**Atomic Commit**: `docs(test-plan): comprehensive coverage matrix for 12 datasets`

---

## 2. Execution Strategy

### Sequential Phase 1 (Foundation)
```bash
# Main agent executes directly
1. Correct np2 metadata
2. Document e_dv_pp wider spike pattern
3. Document e_w_a dual spike pattern
4. Atomic commit + push
```

**Estimated Time**: 15 minutes
**Output**: Corrected metadata, atomic commit checkpoint

---

### Parallel Phase 2 (Design Analysis)
```bash
# Launch 4 parallel subagents
Task("Design wider spike propositions", subagent_type="general-purpose")  # Subagent A
Task("Design multi-peak detection", subagent_type="general-purpose")     # Subagent B
Task("Implement test fixtures", subagent_type="general-purpose")         # Subagent C
Task("Create coverage matrix", subagent_type="general-purpose")          # Subagent D
```

**Estimated Time**:
- Sequential: 60 minutes (15 min × 4 tasks)
- Parallel: 20 minutes (max of 4 parallel tasks + 5 min merge overhead)
- **Time Savings**: 40 minutes (67% reduction)

**Why Safe**:
1. **No Shared Files**: Each agent writes to different output files
2. **Read-Only Inputs**: All agents read from already-committed test data
3. **Independent State**: No agent depends on another's output
4. **Atomic Commits**: Each agent creates its own commit for rollback

---

### Validation Gate (Sequential)
```bash
# Main agent reviews all 4 outputs
1. Review propositions document
2. Review multi-peak design
3. Review test fixtures
4. Review coverage matrix
5. User approval checkpoint
```

**Decision Point**: User approves design before implementation proceeds

---

### Parallel Phase 3 (Implementation)
**Only proceeds after user approval of Phase 2**

This phase can also be parallelized into 3 workstreams:
- **Stream 1**: Implement core tests for existing algorithm (8 datasets without multi-peak)
- **Stream 2**: Implement multi-peak enhancement + e_w_a tests
- **Stream 3**: Implement bounds validation tests for out-of-bounds datasets

---

## 3. Context Protection Mechanisms

### 3.1 Atomic Commit Strategy
**Principle**: Every completed unit of work = one atomic commit

**Benefits**:
- **Rollback Safety**: Can revert any commit without affecting others
- **Bisect-able History**: Can binary search for issues
- **Clear Documentation**: Each commit message explains one change
- **Parallel Merge**: Git handles concurrent branches automatically

**Example Commit Sequence**:
```
b4dda29 - chore(analysis): add 1000-bin high-resolution np2 histogram
<BRANCH POINT>
├─ fix(metadata): correct np2 and document spike patterns (Agent Main)
└─ PARALLEL BRANCHES
   ├─ docs(analysis): wider spike propositions (Agent A)
   ├─ docs(design): multi-peak interior detection (Agent B)
   ├─ test(fixtures): add 8 new PPA12 fixtures (Agent C)
   └─ docs(test-plan): test coverage matrix (Agent D)
<MERGE POINT>
└─ merge: integrate parallel design analysis
```

### 3.2 File-Level Independence

**Subagent A** writes to: `docs/WIDER_SPIKE_PROPOSITIONS.md`
**Subagent B** writes to: `docs/MULTI_PEAK_INTERIOR_DESIGN.md`
**Subagent C** writes to: `tests/conftest.py`
**Subagent D** writes to: `docs/TEST_COVERAGE_MATRIX.md`

**No Overlap**: Git can auto-merge without conflicts

### 3.3 Context Window Protection

**Problem**: Sequential execution consumes context with intermediate steps

**Solution**: Parallel agents work in isolation, only final results are merged back

**Context Usage**:
- **Sequential**: ~40K tokens (all 4 analyses + intermediate discussion)
- **Parallel**: ~15K tokens (4 final documents + merge discussion)
- **Savings**: 25K tokens (62% context preservation)

### 3.4 State Isolation

**Read-Only Shared State**:
- Test data files (parquet + JSON)
- Existing source code (`src/fitqc/`)
- Analysis scripts (committed)

**Write-Isolated State**:
- Each agent has its own output file(s)
- Each agent creates its own branch/commit
- No runtime state sharing

---

## 4. Risk Mitigation

### Risk 1: Subagent Produces Incorrect Analysis
**Probability**: Low-Medium
**Impact**: Medium (wasted time, but caught at validation gate)

**Mitigation**:
- Validation gate before implementation
- User reviews all documents
- Atomic commits allow easy rollback
- Can re-run specific agent if needed

---

### Risk 2: Git Merge Conflicts
**Probability**: Very Low (by design - no file overlap)
**Impact**: Low (easy to resolve if occurs)

**Mitigation**:
- Agents write to different files
- Only main agent touches shared files (metadata)
- Use `git pull --rebase` before merge

---

### Risk 3: Subagent Misunderstands Requirements
**Probability**: Low (clear, scoped prompts)
**Impact**: Medium (rework needed)

**Mitigation**:
- Detailed subagent prompts with examples
- Validation gate catches issues before implementation
- Can redirect subagent with follow-up

---

### Risk 4: Sequential Dependencies Violated
**Probability**: Very Low (work breakdown validated)
**Impact**: High (would require full rework)

**Mitigation**:
- Phase 1 completes before Phase 2 starts
- Validation gate between design and implementation
- Dependency analysis documented in this plan

---

## 5. Success Metrics

### Time Efficiency
- **Target**: 60-70% wall-clock time reduction
- **Measurement**: Compare parallel vs estimated sequential duration

### Context Preservation
- **Target**: ≤100K tokens for entire workflow
- **Measurement**: Token usage at each phase

### Code Quality
- **Target**: All tests pass, no regressions
- **Measurement**: `pytest` results

### Rollback Safety
- **Target**: Any phase revertible independently
- **Measurement**: Clean `git revert` of each commit

---

## 6. Execution Checklist

### Phase 1: Foundation (Sequential)
- [ ] Correct np2 metadata (`expected_lower_stickiness: false → true`)
- [ ] Add note to e_dv_pp metadata about wider spike
- [ ] Add note to e_w_a metadata about dual spikes
- [ ] Atomic commit + push
- [ ] **Checkpoint**: Metadata corrections complete

### Phase 2: Design (Parallel)
- [ ] Launch Subagent A: Wider spike propositions
- [ ] Launch Subagent B: Multi-peak detection design
- [ ] Launch Subagent C: Test fixtures implementation
- [ ] Launch Subagent D: Test coverage matrix
- [ ] Wait for all 4 agents to complete
- [ ] Review all 4 outputs
- [ ] Merge commits (should auto-merge)
- [ ] Push merged branch
- [ ] **Checkpoint**: User approves design

### Phase 3: Implementation (Parallel) - Only after approval
- [ ] Launch implementation subagents (TBD based on approved design)
- [ ] Validation and merge
- [ ] **Checkpoint**: Tests implemented

### Phase 4: Validation (Sequential)
- [ ] Run full test suite
- [ ] Generate coverage report
- [ ] **Checkpoint**: All tests pass

---

## 7. Justification & Evidence

### Why Parallel Execution is Safe Here

**Evidence from current state**:
1. ✅ All 12 datasets already loaded (no data collection needed)
2. ✅ Analysis scripts completed (understand all patterns)
3. ✅ Metadata mostly correct (only 1 correction needed)
4. ✅ Conftest structure established (know where fixtures go)

**Independence verified**:
- Design analysis has NO code dependencies
- Fixture implementation touches isolated file
- Coverage planning is pure documentation
- No shared mutable state

### Why Atomic Commits Protect Us

**Evidence from this session**:
- Already used 9 atomic commits successfully
- Each commit is self-contained and revertible
- Clear commit messages enable understanding
- No issues with rollback so far

**Example** (from this session):
```
cb61da9 - chore(analysis): add detailed np2 and w_const visualizations
bf13d50 - chore(analysis): add comprehensive PPA12 dataset analysis script
ad02559 - feat(plot): add interior and combined filter comparison visualizations
```

### Context Protection Evidence

**Token usage this session**: ~115K tokens
**Major consumers**:
- Analysis iterations: ~30K
- Plotting implementations: ~25K
- Discussion and clarification: ~60K

**With parallel execution**:
- 4 agents each produce ~10-15K token output
- Main agent reviews ~10K tokens (summaries)
- **Net**: ~25K tokens vs ~40K sequential
- **Savings**: 15K tokens (37% reduction)

---

## 8. Alternative Considered: Sequential Execution

**Pros**:
- Simpler to coordinate
- No merge overhead
- Can adjust based on findings

**Cons**:
- 60+ minutes longer wall-clock time
- 25K+ more tokens consumed
- More context pollution from intermediate work
- Higher risk of hitting context limits

**Decision**: Parallel execution preferred for this specific case due to:
1. Clear work boundaries
2. Independent deliverables
3. No runtime dependencies
4. Atomic commit safety net
5. Significant time/context savings

---

## 9. Approval Request

**Ready to proceed?**

**Phase 1** (Sequential - 15 min):
1. Correct np2 metadata
2. Document spike patterns
3. Commit + push

**Phase 2** (Parallel - 20 min):
Launch 4 subagents for:
- Wider spike propositions
- Multi-peak design
- Test fixtures
- Coverage matrix

**After Phase 2**: User reviews and approves before Phase 3 implementation

---

**Approval needed to proceed with Phase 1**. Phase 2 will await your approval after Phase 1 completion.
