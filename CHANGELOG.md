# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.2.2] - 2020-06-01
### Fixed
- Live light client sleeping too long if process started before start time i.e. 8AM where start time is 9:30AM.

## [0.2.1] - 2020-04-16
### Changed
- Variable from `second_to_sleep` to `seconds_to_sleep`.

### Fixed
- Miscaculating seconds to sleep after being active.

## [0.2.0] - 2020-04-10
### Added
- A schedule, you specify what days and what time the live light should be active.
- Active and Inactive light color, as a config option.
- A way to turn off the live light add a new endpoint (DELETE) `/color`.

### Changed
- Config format to contain new sections.
- Debconf `config` and `templates` in `live-light-client` for new config values.

## [0.1.0] - 2020-04-04
### Added
- Initial Release.

[Unreleased]: https://gitlab.com/hmajid2301/markdown-mermaid-to-images/-/compare/release%2F0.2.2...master
[0.2.2]: https://gitlab.com/hmajid2301/markdown-mermaid-to-images/-/tags/release%2F0.2.2...release%2F0.2.1
[0.2.1]: https://gitlab.com/hmajid2301/markdown-mermaid-to-images/-/tags/release%2F0.2.1...release%2F0.2.0
[0.2.0]: https://gitlab.com/hmajid2301/markdown-mermaid-to-images/-/tags/release%2F0.2.0...release%2F0.1.0
[0.1.0]: https://gitlab.com/hmajid2301/markdown-mermaid-to-images/-/tags/release%2F0.1.0