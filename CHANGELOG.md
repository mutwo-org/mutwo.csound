# Change Log

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/)
and this project adheres to [Semantic Versioning](http://semver.org/).

## [Unreleased]

## [0.7.0] - 2023-04-27

### Changed
- modernized dependencies, testing structure

### Fixed
- docstring


## [0.6.0] - 2022-08-10

### Changed
- to new `mutwo.core` version with parameter based duration model
- `mutwo.ext-csound` to `mutwo.csound`


## [0.5.0] - 2022-05-09

### Changed
- `EventToSoundFile` argument `csound_score_converter` to `event_to_csound_score`
- improved warnings


## [0.4.0] - 2022-03-15

### Changed
- `constants` to `configurations` and `constants`


## [0.3.0] - 2022-02-17

### Changed
- refactored `CsoundScoreConverter` to `EventToCsoundScore`
- refactored `CsoundConverter` to `EventToSoundFile`
- package structure to namespace package to apply refactor of mutwo main package


## [0.2.0] - 2022-01-11

### Changed
- applied movement from music related parameter and converter modules (which have been moved from [mutwo core](https://github.com/mutwo-org/mutwo) in version 0.49.0 to [mutwo.ext-music](https://github.com/mutwo-org/mutwo.ext-music))

### Removed
- unused boilerplate code
