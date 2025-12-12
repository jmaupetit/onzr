# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.6.0] - 2025-12-12

### Added

- Add playlist support
- Add fallback track support
- Add the `CONNECTION_POOL_MAXSIZE` configuration setting
- Add the `ALWAYS_FETCH_RELEASE_DATE` configuration setting
- CLI: add the `playlist` command
- CLI: add the `search` command `--playlist/-p` option
- CLI: add track/album release date to outputs for the `search` 
  and `artist` commands using the `-r/--release` option

### Changed 

- Fetch track details in separated threads (when requested)

#### Dependencies

- Upgrade `fastapi` to `0.123.10`
- Upgrade `pydantic` to `2.12.5`
- Upgrade `pydantic-settings` to `2.12.0`
- Upgrade `typer` to `0.20.0`
- Upgrade `uvicorn` to `0.38.0`

## [0.5.2] - 2025-11-04

### Fixed

- CLI: restore track progression bar (and length) for MP3 files

## [0.5.1] - 2025-10-30

### Fixed

- Update server OpenAPI specification

## [0.5.0] - 2025-10-30

### Added

- CLI: add all command options short name
- CLI: add `--first/-f` option to the `search` command

### Changed

- CLI: require Onzr server to be up before running commands that depend on it

### Fixed

- Store song version in track title

## [0.4.0] - 2025-10-22

### Added

- CLI: Add the `config` command
- CLI: Add the `openapi` command
- CLI: Add configurable `THEME`

### Changed

- CLI: Improve commands output (`now` command is no longer experimental)

#### Dependencies

- Upgrade `pydantic` to `2.12.3`

### Fixed

- Allow to play queue from the first track (rank 0)
- Use the best available quality if the default quality is not available

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

[unreleased]: https://github.com/jmaupetit/onzr/compare/v0.6.0...main
[0.6.0] https://github.com/jmaupetit/onzr/compare/v0.5.2...v0.6.0
[0.5.2] https://github.com/jmaupetit/onzr/compare/v0.5.1...v0.5.2
[0.5.1] https://github.com/jmaupetit/onzr/compare/v0.5.0...v0.5.1
[0.5.0] https://github.com/jmaupetit/onzr/compare/v0.4.0...v0.5.0
[0.4.0] https://github.com/jmaupetit/onzr/compare/v0.3.0...v0.4.0
[0.3.0] https://github.com/jmaupetit/onzr/compare/v0.2.0...v0.3.0
[0.2.0] https://github.com/jmaupetit/onzr/compare/v0.1.0...v0.2.0
[0.1.0] https://github.com/jmaupetit/onzr/compare/13ca0d7...v0.1.0
