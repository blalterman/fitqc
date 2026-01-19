# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Multi-curve quantile-based threshold detection for boundary and interior stickiness
- Progressive tolerance grid for boundary detection (denser near boundaries)
- `BoundaryConfig.grid_mode`: Choose between "uniform" and "progressive" grids
- `BoundaryConfig.use_quantile_analysis`: Enable multi-curve robust threshold estimation
- `InteriorConfig.use_quantile_analysis`: Enable multi-curve robust threshold estimation
- Median aggregation across quantiles for robust elbow detection
- Optional `quantile_elbows` field in `BoundaryResult` and `InteriorResult` for debugging
- Example script `examples/quantile_analysis_example.py` demonstrating multi-curve usage

### Changed
- Default behavior unchanged (backward compatible)
- Multi-curve analysis is opt-in via config flags
- Enhanced docstrings in `config.py`, `boundary.py`, and `interior.py` to explain multi-curve mode

### Improved
- Better detection of tight pileups (< 0.5% of range) with progressive grid
- More robust threshold estimation via multi-curve median aggregation
- More accurate epsilon estimation for very tight spikes (< 1e-8 width)

## Notes

This changelog will be updated with version numbers and release dates when the multi-curve
quantile detection feature is released after validation against real-world datasets.
