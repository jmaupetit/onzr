# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- CLI: Add the `openapi` command

## [0.3.0] - 2025-10-05

### Added

- Switch to a HTTP client-server architecture using FastAPI
- Switch to Pydantic models
- Switch to pydantic-settings for configuration management
- Implement an API Client
- Stream tracks over HTTP to VLC
- CLI: Add the `add` command
- CLI: Add the `queue` command
- CLI: Add the `clear` command
- CLI: Add the `now` command
- CLI: Add the `pause` command
- CLI: Add the `next` command
- CLI: Add the `previous` command
- CLI: Add the `serve` command
- CLI: Add the `state` command
- CLI: Add the `version` command
- CLI: Add the `--rank` option for the `play` command

### Deleted

- Remove dynaconf settings management

## [0.2.0] - 2025-04-18

### Added

- Explore album tracks using the `album` command
- Explore artist albums using the `artist` command `--albums` option
- Bootstrap installation using the `init` command
- Document base CLI commands

## [0.1.0] - 2025-04-02

### Added

- Implement a draft CLI using VLC

[unreleased]: https://github.com/jmaupetit/onzr/compare/v0.3.0...main

[0.3.0] https://github.com/jmaupetit/onzr/compare/v0.2.0...v0.3.0
[0.2.0] https://github.com/jmaupetit/onzr/compare/v0.1.0...v0.2.0
[0.1.0] https://github.com/jmaupetit/onzr/compare/13ca0d7...v0.1.0
