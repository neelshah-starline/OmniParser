# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Fixed
- **Florence-2 Model Processing**: Fixed AttributeError "'NoneType' object has no attribute 'shape'" during icon caption generation
  - Added `attn_implementation="eager"` parameter for proper Florence-2 model loading
  - Implemented individual image processing (`batch_size=1`) for Florence models to avoid batched generation issues
  - Resolved `past_key_values` None errors during model inference

### Changed
- **Git Configuration**: Added `imgs/` and `screenshots/` folders to `.gitignore` to prevent committing generated test/demo content
- **Model Processing**: Optimized Florence-2 model to process images individually for better stability

### Added
- **CHANGELOG.md**: Added this changelog file to track project changes and fixes

## [2025-02-XX] - OmniParser V2 Release
- Released OmniParser V2 with improved performance (39.5% on Screen Spot Pro benchmark)
- Added OmniTool for Windows 11 VM control with multiple LLM support
- Enhanced icon detection and interactivity prediction

## [2024-11-XX] - OmniParser V1.5
- Improved fine-grained icon detection
- Added prediction of element interactivity
- Enhanced model performance and accuracy

## [2024-08-XX] - Initial Release
- First release of OmniParser for GUI screen parsing
- Support for vision-based GUI agent capabilities
