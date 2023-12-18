# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2023-12-17

### Added

- Custom fonts config and loader, with support for local TrueType files or Google Fonts-hosted font families.
- Support for multiple declarative rendering styles.
- The ability to generate an image using provided prose, with an optional tilt and randomly-offset thumbnail; thumbnail generation by default tries to maximize aesthetic quality by pre-scaling the rendering based on the a font density.
