# Directory Organization Plan for fitqc

**Date**: 2026-01-23
**Purpose**: Reorganize root directory to separate production files from development/investigation artifacts
**Constraint**: No deletions, only moves; preserve git history; maintain import paths

---

## Executive Summary

The fitqc root directory contains **47 files** (20 Python scripts, 7 investigation reports, 1 data file, 19 config/production files). Analysis reveals:

- ✅ **Production structure is solid**: src/, tests/, docs/, examples/ follow Python best practices
- ⚠️ **Root is cluttered**: 20+ investigation scripts and 6 dated reports obscure essential files
- 🎯 **Goal**: Clear separation between "working on this now" vs "production/long-term valuable"
- 📊 **Impact**: 28 files should be reorganized (59% of root directory)

**Recommendation**: Implement **Option 2 (Investigations Archive)** - organize by purpose with clear active/historical separation.

---

## Table of Contents

1. [Current State Inventory](#current-state-inventory)
2. [File Categorization](#file-categorization)
3. [Dependency Analysis](#dependency-analysis)
4. [Proposed Organizational Structures](#proposed-organizational-structures)
5. [Migration Strategy](#migration-strategy)
6. [Parallel Execution Plan](#parallel-execution-plan)
7. [Risk Assessment](#risk-assessment)
8. [Success Criteria](#success-criteria)

---

## Current State Inventory

### Root Directory Composition

```
Total files in root: 47
├── Python scripts: 20 (43%)
├── Markdown docs: 7 (15%)
├── Config/production: 19 (40%)
└── Data files: 1 (2%)
```

### Production Directories (Well-Organized)

```
src/fitqc/          - 11 Python modules (production package)
tests/              - 24 test files + 34 test fixtures
docs/               - Sphinx documentation (RST files, conf.py)
examples/           - 4 usage example scripts
joss/               - 4 journal submission files
scripts/            - 1 maintenance utility
figures/            - 7 dataset subdirectories, 32 plots
```

### Development Directories (Existing)

```
plans/              - 7 design/planning documents
prompts/            - 4 AI assistant prompts
bkgrnd/             - 2 background context files
tmp/                - 10 temporary/validation files
notebooks/          - 1 exploration script
```

### Root Directory Files by Type

#### Production/Config (19 files - KEEP IN ROOT)
```
✅ pyproject.toml          - Package configuration
✅ README.md               - User documentation
✅ CHANGELOG.md            - Version history
✅ LICENSE                 - Legal
✅ .gitignore             - Git config
✅ .pre-commit-config.yaml - Pre-commit hooks
✅ .readthedocs.yaml      - RTD config
✅ uv.lock                - Dependency lock
✅ .git/, .github/, .pytest_cache/ (directories)
```

#### Investigation Scripts (20 files - REORGANIZE)
```
📦 analyze_ahe_data.py                - One-off A_He investigation
📦 analyze_all_ppa12_data.py          - Dataset validation utility
📦 analyze_new_datasets.py            - Dataset characterization
📦 analyze_np2_detailed.py            - One-off np2 investigation
📦 analyze_np2_highres.py             - One-off np2 investigation
📦 analyze_w_const_detailed.py        - One-off w_const investigation
📦 audit_all_datasets.py              - QA utility (active)
📦 audit_filtering.py                 - Debug/audit script
📦 check_filtered_np1.py              - Quick validation
📦 debug_curve_shape.py               - One-off debug
📦 debug_detection_failure.py         - One-off debug
📦 debug_elbow_detection.py           - One-off debug
📦 debug_upper_fp.py                  - One-off debug
📦 investigate_np1_ahe_issues.py      - One-off investigation
📦 plot_A_He_highres.py               - Superseded by plot_A_He_improved.py
📦 plot_A_He_improved.py              - Latest visualization tool
📦 plot_np2_highres.py                - One-off visualization
📦 plot_w_const_detailed.py           - One-off visualization
📦 plot_ppa12_filter_comparison.py    - Plot generator
📦 plot_ppa12_interior_combined.py    - Plot generator (active)
⭐ regenerate_bounds_filter_plots.py  - ACTIVE utility (Jan 21)
📦 test_bounds_validation.py          - Test script
📦 test_fix.py                        - Validation test
```

#### Investigation Reports (7 files - REORGANIZE)
```
📦 A_HE_PANEL_EXPLANATION.md                        - Jan 20 investigation
📦 BOUNDS_FILTER_VISUALIZATION_INVESTIGATION.md     - Jan 20-21 investigation
📦 FILTERING_AUDIT_REPORT.md                        - Jan 20 audit
📦 PARALLEL_SUBAGENT_PLAN.md                        - Jan 20 plan
📦 PPA12_TEST_DATA_ANALYSIS_REPORT.md               - Jan 20 analysis
📦 TEST_QUALITY_ANALYSIS.md                         - Jan 20 analysis
```

#### Data Files (1 file - REORGANIZE)
```
📦 np2_highres_histogram.txt          - Text output from investigation
```

---

## File Categorization

### Category 1: Production (KEEP IN ROOT) - 19 files

**Criteria**: Essential for users, contributors, or build systems

**Files**:
- pyproject.toml, README.md, CHANGELOG.md, LICENSE
- .gitignore, .pre-commit-config.yaml, .readthedocs.yaml
- uv.lock
- .git/, .github/, .pytest_cache/ (directories)

**Rationale**: Standard Python project structure; required in root by convention

---

### Category 2: Active Utilities (KEEP ACCESSIBLE) - 4 files

**Criteria**: Recently updated, reusable, actively used in development workflow

**Files**:
1. `regenerate_bounds_filter_plots.py` ⭐ (Jan 21, 01:43 - **most recent**)
   - Purpose: Regenerate all filter comparison plots with zoom panel
   - Status: Latest utility for visualization regeneration
   - Production deps: `fitqc.plot_bounds_filter_comparison`

2. `audit_all_datasets.py` (Jan 20, 22:50)
   - Purpose: QA tool for filtering consistency across 12 datasets
   - Status: Active validation utility
   - Production deps: `fitqc.boundary`, `fitqc.config`

3. `analyze_all_ppa12_data.py` (Jan 20, 20:40)
   - Purpose: Validation utility for algorithm testing
   - Status: Reusable across datasets
   - Production deps: `fitqc.boundary`, `fitqc.config`

4. `plot_ppa12_interior_combined.py` (Jan 20, 21:20)
   - Purpose: Generate comprehensive filter visualizations
   - Status: Active plot generator
   - Production deps: `fitqc.run_interior_qc`, `fitqc.plot_*`

**Rationale**: These scripts are tools, not one-off investigations; likely to be reused

---

### Category 3: Historical Investigations (ARCHIVE) - 16 files

**Criteria**: One-off scripts for specific issues; investigation complete; findings incorporated

**Analysis Scripts** (6 files):
```
analyze_ahe_data.py              - Jan 20, 20:08 | A_He boundary stickiness investigation
analyze_new_datasets.py          - Jan 20, 21:50 | Dataset characterization (one-time)
analyze_np2_detailed.py          - Jan 20, 22:05 | np2 metadata discrepancy
analyze_np2_highres.py           - Jan 20, 22:27 | np2 pattern detection
analyze_w_const_detailed.py      - Jan 20, 22:05 | w_const out-of-bounds investigation
investigate_np1_ahe_issues.py    - Jan 20, 20:40 | False positive root causes
```

**Debug Scripts** (5 files):
```
debug_curve_shape.py             - Jan 20, 20:32 | Elbow detection debug
debug_detection_failure.py       - Jan 20, 20:32 | Delta function detection debug
debug_elbow_detection.py         - Jan 20, 20:32 | A_He elbow debug
debug_upper_fp.py                - Jan 20, 20:32 | Upper boundary FP debug
audit_filtering.py               - Jan 20, 22:50 | Filtering visualization debug
```

**Plot Scripts** (5 files):
```
plot_A_He_highres.py             - Jan 20, 22:58 | Superseded by plot_A_He_improved.py
plot_A_He_improved.py            - Jan 21, 01:07 | Final A_He visualization
plot_np2_highres.py              - Jan 20, 22:36 | One-off np2 visualization
plot_w_const_detailed.py         - Jan 20, 22:36 | One-off w_const visualization
plot_ppa12_filter_comparison.py  - Jan 20, 21:14 | Superseded by regenerate_bounds_filter_plots.py
```

**Rationale**:
- All dated to Jan 20-21 development session
- Investigations complete (findings documented in reports)
- Issues resolved (code fixed, tests added, metadata corrected)
- No ongoing reference value
- Historical artifact value only

---

### Category 4: Quick Tests/Checks (ARCHIVE) - 3 files

**Criteria**: Ad-hoc validation scripts; one-time use

```
check_filtered_np1.py            - Jan 20, 21:05 | Quick np1 filtering check
test_bounds_validation.py        - Jan 20, 21:05 | Logging feature test
test_fix.py                      - Jan 20, 20:32 | Algorithm fix validation
```

**Rationale**: One-off validation; not part of test suite; historical only

---

### Category 5: Investigation Reports (ARCHIVE) - 6 files

**Criteria**: Point-in-time investigation documentation; findings incorporated

```
A_HE_PANEL_EXPLANATION.md                        - 9.0K | Jan 20 | Panel breakdown
BOUNDS_FILTER_VISUALIZATION_INVESTIGATION.md     - 18K  | Jan 21 | Design investigation (8 options)
FILTERING_AUDIT_REPORT.md                        - 11K  | Jan 20 | Verification audit
PARALLEL_SUBAGENT_PLAN.md                        - 15K  | Jan 20 | Execution plan
PPA12_TEST_DATA_ANALYSIS_REPORT.md               - 6.9K | Jan 20 | Initial dataset analysis
TEST_QUALITY_ANALYSIS.md                         - 14K  | Jan 20 | Test quality gaps
```

**Rationale**:
- All dated Jan 20-21, 2026
- Investigations complete
- Findings incorporated (code fixed, features added, tests improved)
- Not referenced by production code
- Pollute root directory (60K+ of investigation docs)

---

### Category 6: Data/Output Files (RELOCATE) - 1 file

```
np2_highres_histogram.txt        - 13K | Jan 20 | Text output from investigation
```

**Rationale**: Investigation output; belongs with investigation artifacts or in tmp/

---

## Dependency Analysis

### Import Dependency Map

**Key Finding**: ✅ **NO INTERDEPENDENCIES BETWEEN ROOT SCRIPTS**

All root scripts are standalone:
- Import from production code (`fitqc.*`)
- Do NOT import from each other
- Can be moved independently without breaking imports

#### Production Dependencies by Script

**Scripts depending on fitqc.boundary**:
```
analyze_ahe_data.py              → fitqc.boundary.run_boundary_qc, fitqc.config
analyze_all_ppa12_data.py        → fitqc.boundary.run_boundary_qc, fitqc.config
audit_all_datasets.py            → fitqc.boundary.*, fitqc.config
audit_filtering.py               → fitqc.boundary.*, fitqc.config
test_bounds_validation.py        → fitqc.boundary.run_boundary_qc, fitqc.config
test_fix.py                      → fitqc.boundary.run_boundary_qc, fitqc.config
debug_*.py (4 files)             → fitqc.boundary.*, fitqc.config
investigate_np1_ahe_issues.py    → None (numpy/pandas only)
```

**Scripts depending on fitqc.plot**:
```
regenerate_bounds_filter_plots.py    → fitqc.plot_bounds_filter_comparison
plot_ppa12_filter_comparison.py      → fitqc.plot_bounds_filter_comparison
plot_ppa12_interior_combined.py      → fitqc.plot_*, fitqc.run_*
```

**Scripts with no fitqc dependencies**:
```
analyze_new_datasets.py          → numpy, pandas, pyarrow (data processing only)
analyze_np2_*.py (2 files)       → numpy, pyarrow (data processing only)
analyze_w_const_detailed.py      → numpy, pyarrow (data processing only)
check_filtered_np1.py            → numpy, pyarrow (data processing only)
investigate_np1_ahe_issues.py    → numpy, pyarrow (data processing only)
plot_*.py (4 files)              → numpy, matplotlib (visualization only)
```

### Import Safety

✅ **Safe to move all root scripts**: None are imported by production code
✅ **Safe to move investigation reports**: Not code, no import concerns
✅ **Safe to move data files**: Not imported

**Verification**: Checked src/fitqc/*.py and tests/*.py - no imports from root-level scripts

---

## Proposed Organizational Structures

### Option 1: By File Type (Simple)

**Structure**:
```
fitqc/
├── scripts/
│   ├── analysis/        (analyze_*.py - 6 files)
│   ├── debug/           (debug_*.py - 5 files)
│   ├── plotting/        (plot_*.py - 6 files)
│   ├── validation/      (audit_*.py, check_*.py, test_*.py - 5 files)
│   └── utilities/       (regenerate_*.py - 1 file)
├── reports/
│   └── investigations/  (*.md - 6 files)
└── [production files remain in root]
```

**Pros**:
- ✅ Clear categorization by function
- ✅ Easy to find scripts by type ("I need a debug script")
- ✅ Simple structure with shallow hierarchy
- ✅ Familiar pattern (analysis/, debug/ are common conventions)

**Cons**:
- ❌ Doesn't distinguish active vs. historical
- ❌ Mixes one-off investigations with reusable utilities
- ❌ No temporal organization (can't see what's from recent work)
- ❌ May encourage accumulating more scripts over time
- ❌ Doesn't solve "what's important now" problem

**Use Case**: Best for projects with ongoing analysis needs where all scripts have long-term value

---

### Option 2: By Purpose (Active vs. Historical) ⭐ **RECOMMENDED**

**Structure**:
```
fitqc/
├── scripts/
│   ├── utilities/                    (Active, reusable)
│   │   ├── regenerate_bounds_filter_plots.py ⭐
│   │   ├── audit_all_datasets.py
│   │   ├── analyze_all_ppa12_data.py
│   │   └── plot_ppa12_interior_combined.py
│   └── investigations/               (Historical, archived)
│       ├── 2026-01-20-ppa12-validation/
│       │   ├── analyze_ahe_data.py
│       │   ├── analyze_new_datasets.py
│       │   ├── analyze_np2_detailed.py
│       │   ├── analyze_np2_highres.py
│       │   ├── analyze_w_const_detailed.py
│       │   ├── check_filtered_np1.py
│       │   ├── investigate_np1_ahe_issues.py
│       │   ├── plot_A_He_highres.py
│       │   ├── plot_A_He_improved.py
│       │   ├── plot_np2_highres.py
│       │   ├── plot_w_const_detailed.py
│       │   ├── plot_ppa12_filter_comparison.py
│       │   ├── test_bounds_validation.py
│       │   ├── test_fix.py
│       │   ├── np2_highres_histogram.txt
│       │   └── README.md (summary of investigation)
│       └── 2026-01-20-elbow-debug/
│           ├── debug_curve_shape.py
│           ├── debug_detection_failure.py
│           ├── debug_elbow_detection.py
│           ├── debug_upper_fp.py
│           ├── audit_filtering.py
│           └── README.md
├── docs/
│   └── investigations/               (Investigation reports)
│       ├── 2026-01-20-ppa12-validation/
│       │   ├── PPA12_TEST_DATA_ANALYSIS_REPORT.md
│       │   ├── FILTERING_AUDIT_REPORT.md
│       │   ├── TEST_QUALITY_ANALYSIS.md
│       │   └── A_HE_PANEL_EXPLANATION.md
│       ├── 2026-01-21-visualization-fix/
│       │   └── BOUNDS_FILTER_VISUALIZATION_INVESTIGATION.md
│       └── plans/
│           └── PARALLEL_SUBAGENT_PLAN.md
└── [production files remain in root]
```

**Pros**:
- ✅ **Clearly separates active vs. historical** - solves primary goal
- ✅ **Utilities immediately discoverable** - 4 active tools easy to find
- ✅ **Historical context preserved** - investigations grouped by date/topic
- ✅ **Scalable** - future investigations go in new dated folders
- ✅ **README in each investigation** - explains what/why/findings
- ✅ **Clear signal**: "utilities/ = current tools, investigations/ = history"
- ✅ **Matches git history** - dates align with commits

**Cons**:
- ❌ More complex structure (3 levels deep)
- ❌ Requires creating dated folders (extra work)
- ❌ Need to write README for each investigation
- ❌ Decisions needed: "Is this active or historical?"

**Use Case**: ✅ **Perfect for this project** - separates current tools from completed investigations

---

### Option 3: By Dataset (Data-Centric)

**Structure**:
```
fitqc/
├── scripts/
│   ├── A_He/
│   │   ├── analyze_ahe_data.py
│   │   ├── plot_A_He_highres.py
│   │   ├── plot_A_He_improved.py
│   │   └── debug_upper_fp.py
│   ├── np1/
│   │   ├── investigate_np1_ahe_issues.py
│   │   └── check_filtered_np1.py
│   ├── np2/
│   │   ├── analyze_np2_detailed.py
│   │   ├── analyze_np2_highres.py
│   │   └── plot_np2_highres.py
│   ├── w_const/
│   │   ├── analyze_w_const_detailed.py
│   │   └── plot_w_const_detailed.py
│   ├── multi_dataset/
│   │   ├── analyze_all_ppa12_data.py
│   │   ├── analyze_new_datasets.py
│   │   └── audit_all_datasets.py
│   └── algorithm/
│       ├── debug_*.py (5 files)
│       └── regenerate_*.py
```

**Pros**:
- ✅ Groups related analysis by subject
- ✅ Easy to find all work related to specific dataset
- ✅ Matches figures/ directory structure

**Cons**:
- ❌ **Doesn't separate active vs. historical** - fails primary goal
- ❌ Unclear where multi-dataset scripts go
- ❌ Algorithm debug scripts don't fit dataset model
- ❌ Duplicates organization (scripts/ AND figures/ both by dataset)
- ❌ Hard to find "what utilities do I have?"

**Use Case**: Best for dataset-focused analysis projects, not algorithmic development

---

### Option 4: Flat Archive (Minimal)

**Structure**:
```
fitqc/
├── scripts/
│   ├── regenerate_bounds_filter_plots.py ⭐
│   ├── audit_all_datasets.py
│   ├── analyze_all_ppa12_data.py
│   └── plot_ppa12_interior_combined.py
└── archive/
    └── 2026-01-20-ppa12-investigation/
        ├── scripts/       (16 Python files)
        ├── reports/       (6 MD files)
        └── outputs/       (np2_highres_histogram.txt)
```

**Pros**:
- ✅ Very simple: active vs. archive
- ✅ Clear boundary: "archive/ = don't look here"
- ✅ Minimal structure

**Cons**:
- ❌ No organization within archive (flat directory of 16 scripts)
- ❌ Less browsable for historical reference
- ❌ Doesn't group related investigations

**Use Case**: Best if historical artifacts have zero reference value

---

### Option 5: Keep Everything in Root (Status Quo)

**Structure**: No changes

**Pros**:
- ✅ No migration work
- ✅ No risk of breaking anything
- ✅ All files immediately visible

**Cons**:
- ❌ **Fails primary goal** - doesn't reduce clutter
- ❌ Harder for new contributors to understand structure
- ❌ Will accumulate more clutter over time
- ❌ Mixes production, active tools, and historical artifacts

**Use Case**: If team decides current structure is acceptable

---

## Recommended Solution: Option 2 (Active vs. Historical)

### Rationale

1. **Directly addresses the goal**: "separate development things we are working on vs production or long-term valuable"
   - `scripts/utilities/` = currently working on / long-term valuable
   - `scripts/investigations/` = historical context
   - Root = production only

2. **Evidence-based categorization**:
   - All 20 scripts analyzed with git timestamps
   - Clear investigation timeline: Jan 20-21, 2026
   - 4 scripts are reusable utilities, 16 are one-off investigations

3. **Aligns with project history**:
   - Investigations already have dated reports
   - Git commits show clear temporal clustering
   - Natural grouping: PPA12 validation (Jan 20), visualization fix (Jan 21)

4. **Scalable for future**:
   - New utilities → `scripts/utilities/`
   - New investigations → `scripts/investigations/YYYY-MM-DD-topic/`
   - Clear decision tree for where new files go

5. **Preserves value of both categories**:
   - Utilities remain discoverable and accessible
   - Historical investigations preserved with context (README explains what/why/outcome)

---

## Migration Strategy

### Phase 1: Create Directory Structure

```bash
# Create new directories
mkdir -p scripts/utilities
mkdir -p scripts/investigations/2026-01-20-ppa12-validation
mkdir -p scripts/investigations/2026-01-20-elbow-debug
mkdir -p docs/investigations/2026-01-20-ppa12-validation
mkdir -p docs/investigations/2026-01-21-visualization-fix
mkdir -p docs/investigations/plans
```

### Phase 2: Move Active Utilities (4 files)

```bash
# Move using git mv to preserve history
git mv regenerate_bounds_filter_plots.py scripts/utilities/
git mv audit_all_datasets.py scripts/utilities/
git mv analyze_all_ppa12_data.py scripts/utilities/
git mv plot_ppa12_interior_combined.py scripts/utilities/
```

**Rationale**: These are reusable tools, not one-off investigations

### Phase 3: Move PPA12 Investigation Scripts (14 files)

```bash
git mv analyze_ahe_data.py scripts/investigations/2026-01-20-ppa12-validation/
git mv analyze_new_datasets.py scripts/investigations/2026-01-20-ppa12-validation/
git mv analyze_np2_detailed.py scripts/investigations/2026-01-20-ppa12-validation/
git mv analyze_np2_highres.py scripts/investigations/2026-01-20-ppa12-validation/
git mv analyze_w_const_detailed.py scripts/investigations/2026-01-20-ppa12-validation/
git mv check_filtered_np1.py scripts/investigations/2026-01-20-ppa12-validation/
git mv investigate_np1_ahe_issues.py scripts/investigations/2026-01-20-ppa12-validation/
git mv plot_A_He_highres.py scripts/investigations/2026-01-20-ppa12-validation/
git mv plot_A_He_improved.py scripts/investigations/2026-01-20-ppa12-validation/
git mv plot_np2_highres.py scripts/investigations/2026-01-20-ppa12-validation/
git mv plot_w_const_detailed.py scripts/investigations/2026-01-20-ppa12-validation/
git mv plot_ppa12_filter_comparison.py scripts/investigations/2026-01-20-ppa12-validation/
git mv test_bounds_validation.py scripts/investigations/2026-01-20-ppa12-validation/
git mv test_fix.py scripts/investigations/2026-01-20-ppa12-validation/
git mv np2_highres_histogram.txt scripts/investigations/2026-01-20-ppa12-validation/
```

### Phase 4: Move Elbow Debug Scripts (5 files)

```bash
git mv debug_curve_shape.py scripts/investigations/2026-01-20-elbow-debug/
git mv debug_detection_failure.py scripts/investigations/2026-01-20-elbow-debug/
git mv debug_elbow_detection.py scripts/investigations/2026-01-20-elbow-debug/
git mv debug_upper_fp.py scripts/investigations/2026-01-20-elbow-debug/
git mv audit_filtering.py scripts/investigations/2026-01-20-elbow-debug/
```

### Phase 5: Move Investigation Reports (6 files)

```bash
# PPA12 validation reports
git mv PPA12_TEST_DATA_ANALYSIS_REPORT.md docs/investigations/2026-01-20-ppa12-validation/
git mv FILTERING_AUDIT_REPORT.md docs/investigations/2026-01-20-ppa12-validation/
git mv TEST_QUALITY_ANALYSIS.md docs/investigations/2026-01-20-ppa12-validation/
git mv A_HE_PANEL_EXPLANATION.md docs/investigations/2026-01-20-ppa12-validation/

# Visualization investigation
git mv BOUNDS_FILTER_VISUALIZATION_INVESTIGATION.md docs/investigations/2026-01-21-visualization-fix/

# Plans
git mv PARALLEL_SUBAGENT_PLAN.md docs/investigations/plans/
```

### Phase 6: Create Investigation README Files

Create `scripts/investigations/2026-01-20-ppa12-validation/README.md`:
```markdown
# PPA12 Test Dataset Validation Investigation

**Date**: January 20, 2026
**Purpose**: Comprehensive validation of boundary detection algorithm on 12 PPA12 real-world test datasets

## Objective
Validate that the boundary stickiness detection algorithm correctly identifies and quantifies boundary pileup across diverse datasets with different characteristics.

## Datasets Analyzed
- A_He: Bilateral boundary stickiness (1.642% at L=0, 0.358% at U=25)
- e_dv_pp, e_dv_ap: No stickiness
- np1: Out-of-bounds samples (failed fits at x=0)
- np2: Metadata discrepancy investigation
- w_const: Out-of-bounds validation
- Plus 6 additional datasets

## Key Findings
1. ✅ Algorithm validated on 3/3 datasets with true boundary stickiness
2. ✅ np1 out-of-bounds samples correctly identified as failed fits
3. ✅ Bounds validation warning system implemented
4. ✅ np2 metadata corrected
5. ✅ All 12 datasets pass filtering verification

## Scripts in This Investigation
- `analyze_*.py`: Dataset-specific deep analysis
- `plot_*.py`: High-resolution visualizations
- `check_*.py`, `test_*.py`: Validation scripts

## Reports
See `/docs/investigations/2026-01-20-ppa12-validation/` for detailed reports.

## Outcome
All validation tests passed. Algorithm ready for production use.
```

Create `scripts/investigations/2026-01-20-elbow-debug/README.md`:
```markdown
# Elbow Detection Debug Investigation

**Date**: January 20, 2026
**Purpose**: Debug and fix elbow detection algorithm for boundary stickiness quantification

## Problem
A_He dataset showed 1.642% lower boundary stickiness but elbow detection was not consistently identifying the correct tolerance threshold.

## Investigation
- Analyzed full (quantile, tolerance) curve
- Examined mass curves and excess ratios
- Tested different elbow detection strategies
- Debugged upper boundary false positive

## Scripts
- `debug_curve_shape.py`: Full curve analysis
- `debug_detection_failure.py`: Delta function detection
- `debug_elbow_detection.py`: Elbow detection logic
- `debug_upper_fp.py`: Upper boundary FP
- `audit_filtering.py`: Filtering visualization

## Outcome
Elbow detection algorithm fixed and validated.
```

### Phase 7: Update Any Documentation References

Check if any docs reference root-level scripts and update paths:
```bash
grep -r "analyze_" docs/
grep -r "debug_" docs/
grep -r "plot_" docs/
```

### Phase 8: Commit Changes

```bash
git add .
git commit -m "refactor: organize root directory by active vs. historical

Reorganize root directory to separate production files from development
artifacts, addressing clutter and improving discoverability.

Changes:
- Move 4 active utilities to scripts/utilities/
  - regenerate_bounds_filter_plots.py (latest tool)
  - audit_all_datasets.py
  - analyze_all_ppa12_data.py
  - plot_ppa12_interior_combined.py

- Archive 19 investigation files to scripts/investigations/
  - 2026-01-20-ppa12-validation/ (14 scripts)
  - 2026-01-20-elbow-debug/ (5 scripts)

- Move 6 investigation reports to docs/investigations/
  - PPA12 validation reports (4 files)
  - Visualization investigation (1 file)
  - Plans (1 file)

- Add README to each investigation folder explaining context

Root directory now contains only:
- Production config (pyproject.toml, README, etc.)
- Organized subdirectories (src/, tests/, docs/, scripts/)

All git history preserved using 'git mv'.
No imports broken (verified: no production code imports root scripts).

Closes #XX (if there's an issue tracking this)
"
```

---

## Parallel Execution Plan

### Analysis: Can Migration Be Parallelized?

**Dependencies**:
1. Phase 1 (create directories) → Must complete first
2. Phases 2-5 (git mv commands) → **Can run in parallel** (no file conflicts)
3. Phase 6 (create READMEs) → Can run in parallel after phases 2-5
4. Phase 7 (update docs) → Must complete after all moves
5. Phase 8 (commit) → Must be last

### Parallel Execution Strategy

**Subagent Group 1** (after Phase 1 completes):
- Subagent A: Execute Phase 2 (move utilities)
- Subagent B: Execute Phase 3 (move PPA12 scripts)
- Subagent C: Execute Phase 4 (move elbow debug scripts)
- Subagent D: Execute Phase 5 (move reports)

**Subagent Group 2** (after Group 1 completes):
- Subagent E: Create PPA12 README
- Subagent F: Create elbow debug README
- Subagent G: Create visualization fix README
- Subagent H: Check/update documentation references

**Time Savings**:
- Sequential: ~8 minutes (1 min per phase × 8 phases)
- Parallel: ~3 minutes (Phase 1: 30s, Group 1: 60s, Group 2: 60s, Phases 7-8: 30s)
- **Speedup**: ~2.7x

**Context Savings**:
- Sequential: All file reads/writes in main context
- Parallel: Subagents handle file operations, main context only receives summaries
- **Token savings**: ~50% (estimated)

### Parallel Execution Commands

```python
# After Phase 1 (directory creation) completes:

# Launch 4 parallel subagents for file moves
agents = [
    Task(subagent_type="Bash", prompt="Move active utilities: git mv regenerate_bounds_filter_plots.py ...", description="Move utilities"),
    Task(subagent_type="Bash", prompt="Move PPA12 investigation scripts: git mv analyze_ahe_data.py ...", description="Move PPA12 scripts"),
    Task(subagent_type="Bash", prompt="Move elbow debug scripts: git mv debug_curve_shape.py ...", description="Move debug scripts"),
    Task(subagent_type="Bash", prompt="Move investigation reports: git mv PPA12_TEST_DATA_ANALYSIS_REPORT.md ...", description="Move reports"),
]

# After file moves complete:
readme_agents = [
    Task(subagent_type="general-purpose", prompt="Create PPA12 investigation README...", description="Create PPA12 README"),
    Task(subagent_type="general-purpose", prompt="Create elbow debug README...", description="Create debug README"),
    Task(subagent_type="general-purpose", prompt="Create visualization fix README...", description="Create viz README"),
    Task(subagent_type="Explore", prompt="Check docs/ for references to moved scripts...", description="Check doc references"),
]
```

### Rollback Plan (if parallelization issues occur)

If parallel execution encounters conflicts:
1. **Stop all subagents**: Cancel pending operations
2. **Check git status**: Identify partially completed moves
3. **Reset to clean state**: `git reset --hard HEAD`
4. **Execute sequentially**: Fall back to sequential migration
5. **Verify**: Check that no files are lost or duplicated

---

## Risk Assessment

### Risk 1: Breaking Imports

**Likelihood**: Low
**Impact**: Medium
**Mitigation**:
- ✅ Verified: No production code imports root scripts
- ✅ Verified: No root scripts import each other
- ✅ Scripts only import from `fitqc.*` (production package)
- ✅ Moving scripts doesn't change import paths

**Residual Risk**: Documentation might reference old paths
- **Detection**: `grep -r "scripts/" docs/` after migration
- **Fix**: Update any hardcoded paths in docs

### Risk 2: Losing Git History

**Likelihood**: Low (if using `git mv`)
**Impact**: High
**Mitigation**:
- ✅ Use `git mv` instead of `mv` + `git add`
- ✅ Git automatically tracks file moves
- ✅ `git log --follow <file>` will show full history

**Verification**:
```bash
# After migration, verify history is preserved:
git log --follow scripts/utilities/regenerate_bounds_filter_plots.py
# Should show commits from when it was in root
```

### Risk 3: Accidental File Loss

**Likelihood**: Very Low
**Impact**: High
**Mitigation**:
- ✅ Using `git mv` prevents loss (atomic operation)
- ✅ Pre-migration verification: `ls -1 *.py | wc -l` (count files)
- ✅ Post-migration verification: Same count in new locations

**Recovery**:
- All files tracked in git: `git checkout HEAD -- <file>` recovers any lost file
- Commit after verification: Can revert entire migration if needed

### Risk 4: Confusion About File Locations

**Likelihood**: Medium (for developers not involved in migration)
**Impact**: Low
**Mitigation**:
- ✅ Add README in each investigation folder explaining purpose
- ✅ Update project README with new structure
- ✅ Commit message clearly documents reorganization
- ✅ Clear naming: `utilities/` vs. `investigations/` is self-explanatory

**Communication**:
- Document structure in project README
- Add comment to CHANGELOG.md noting reorganization
- Consider adding `.github/` note if needed

### Risk 5: Parallel Execution Conflicts

**Likelihood**: Low (files are independent)
**Impact**: Medium (may need to retry)
**Mitigation**:
- ✅ Each subagent moves distinct files (no overlaps)
- ✅ Each subagent creates distinct directories
- ✅ No shared state between parallel operations

**Detection**:
- Monitor subagent outputs for git errors
- Check `git status` after parallel operations

**Recovery**:
- If conflicts: `git reset --hard HEAD`
- Re-run sequentially

---

## Success Criteria

### Quantitative Metrics

1. **Root directory file count**:
   - Before: 47 files (20 Python, 7 MD, 19 config, 1 data)
   - After: ≤20 files (19 config/production + 1 data file if any)
   - **Target reduction**: 57% (27 files moved)

2. **Active utilities accessible**:
   - 4 files in `scripts/utilities/`
   - Clear, descriptive directory name

3. **Historical context preserved**:
   - 19 scripts in `scripts/investigations/`
   - 6 reports in `docs/investigations/`
   - READMEs explaining each investigation

4. **Git history intact**:
   - `git log --follow <moved-file>` shows full history
   - All files accounted for (none lost)

5. **No broken imports**:
   - All tests pass: `pytest`
   - No import errors in production code

### Qualitative Criteria

1. **Discoverability improved**:
   - ✅ New developer can easily find active utilities
   - ✅ Clear separation between "tools" and "archives"
   - ✅ Investigation context easy to understand

2. **Maintainability enhanced**:
   - ✅ Clear pattern for future work ("Where does this new script go?")
   - ✅ Investigations self-documented with READMEs
   - ✅ Scalable structure (dated folders for new investigations)

3. **Production clarity**:
   - ✅ Root directory shows only essential project files
   - ✅ No confusion about what's production vs. development
   - ✅ Clean first impression for repository visitors

### Validation Checklist

After migration:
- [ ] Run `git status` - all moves tracked correctly
- [ ] Run `pytest` - all tests pass
- [ ] Run `git log --follow scripts/utilities/regenerate_bounds_filter_plots.py` - history preserved
- [ ] Check root directory: `ls -1 | wc -l` ≤ 20 files
- [ ] Verify READMEs created in each investigation folder
- [ ] Check for broken links in docs: `grep -r "../" docs/`
- [ ] Review commit diff: `git diff --stat HEAD~1`
- [ ] Confirm with user: Structure makes sense and meets goals

---

## Appendix A: File Inventory by Timestamp

### Timeline of Root Script Creation

**January 20, 2026 - Morning (20:00-20:32)**:
```
20:06  analyze_ahe_data.py
20:14  debug_elbow_detection.py
20:15  debug_curve_shape.py
20:16  debug_upper_fp.py, test_fix.py
20:20  debug_detection_failure.py
```

**January 20, 2026 - Afternoon (20:38-21:50)**:
```
20:38  analyze_all_ppa12_data.py
20:39  investigate_np1_ahe_issues.py
21:07  check_filtered_np1.py
21:12  plot_ppa12_filter_comparison.py
21:19  plot_ppa12_interior_combined.py
21:49  analyze_new_datasets.py
```

**January 20, 2026 - Evening (22:03-22:58)**:
```
22:03  analyze_np2_detailed.py, analyze_w_const_detailed.py
22:26  analyze_np2_highres.py
22:35  plot_np2_highres.py, plot_w_const_detailed.py
22:47  audit_filtering.py
22:48  audit_all_datasets.py
22:56  plot_A_He_highres.py
```

**January 21, 2026 - Early Morning**:
```
01:07  plot_A_He_improved.py
01:41  regenerate_bounds_filter_plots.py ⭐ (LATEST)
```

### Patterns Observed

1. **Clear investigation phases**:
   - Morning: Elbow detection debugging
   - Afternoon: Initial PPA12 dataset analysis
   - Evening: Detailed dataset analysis and visualization
   - Next day: Improved visualization tools

2. **Tool evolution**:
   - `plot_A_He_highres.py` → `plot_A_He_improved.py` (superseded)
   - `plot_ppa12_filter_comparison.py` → `regenerate_bounds_filter_plots.py` (superseded)

3. **Investigation completion**:
   - Debug scripts all created in ~1 hour window (debugging session)
   - Dataset analysis scripts span 4 hours (thorough investigation)
   - Latest file is a utility (not investigation), suggesting work phase ended

---

## Appendix B: Directory Size Analysis

### Current Root Directory Size
```
Total files: 47
Total size: ~300K (excluding .git/)
Python scripts: 20 files, ~120K
Markdown docs: 7 files, ~75K
Config files: 19 files, ~250K (mostly uv.lock at 244K)
Data files: 1 file, 13K
```

### Projected Root Directory After Migration
```
Total files: ~20
Total size: ~260K
Config/production: 19 files, ~250K
Remaining: 1-2 files (if any data files)
```

**Size reduction**: 60% fewer files, 13% smaller (excluding .git/)

### Investigation Archives Size
```
scripts/investigations/: 19 files, ~120K Python + 13K data
docs/investigations/: 6 files, ~75K Markdown
Total archived: 25 files, ~208K
```

---

## Appendix C: Alternative Minimal Migration

If full Option 2 is too complex, here's a minimal migration:

**Minimal Structure**:
```
fitqc/
├── scripts/
│   ├── active/           (4 utility scripts)
│   └── archive/          (20 investigation scripts + reports)
└── [production files in root]
```

**Commands**:
```bash
mkdir -p scripts/active scripts/archive
git mv regenerate_bounds_filter_plots.py scripts/active/
git mv audit_all_datasets.py scripts/active/
git mv analyze_all_ppa12_data.py scripts/active/
git mv plot_ppa12_interior_combined.py scripts/active/
git mv analyze_*.py debug_*.py plot_*.py check_*.py investigate_*.py test_*.py scripts/archive/
git mv *.md scripts/archive/ (except README.md, CHANGELOG.md)
git mv np2_highres_histogram.txt scripts/archive/
```

**Pros**: Simpler, faster to execute
**Cons**: Less organized, no contextual grouping

---

## End of Plan

**Next Step**: User approval to proceed with Option 2 (recommended) or select alternative approach.
