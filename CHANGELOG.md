# Change Log

All notable changes to this project will be documented in this file.
This project adheres to [Semantic Versioning](http://semver.org/).

## [Unreleased](https://github.com/otto-de/jellyfish/compare/1.0.0...HEAD)

## [1.0.0](https://github.com/otto-de/jellyfish/compare/1.0.0...HEAD) - 2017-05-19
### Removed
- resource view feature was removed.

## [0.15.1](https://github.com/otto-de/jellyfish/compare/0.15.0...0.15.1) - 2017-03-27
### Fixed
- Properly convert root_app flag into boolean. 


## [0.15.0](https://github.com/otto-de/jellyfish/compare/0.14.0...0.15.0) - 2017-03-2
### Add
- Severity rating and sorting of services.

## [0.14.0](https://github.com/otto-de/jellyfish/compare/d0ff089a5409d9e7e00150b381e9c01a34bb9e5d...0.14.0) - 2016-11-9
### Add
- Tidy up resource overview.
- Mini pie charts for resource overview.

## 0.13.1 - 2016-11-7
### Fixed
- Some jobs do not have messages.

## 0.13.0 - 2016-11-7
### Changed
- Use lable names for status path and root app from config.
- Use domain name from config.

## 0.12.0 - 2016-10-31
### Changed
- Use full name for all tab to distinguish between services with the same name from multiple verticals.

## 0.11.1 - 2016-10-4
### Fixed
- Add excluding filter support for environment filter 

## 0.11.0 - 2016-09-28
### Added
- Parameter to include auto refresh metatag.
- App name filter now supports excluding services with leading *!* (example: filter=!service).
- Filter for verticals / groups (example: group=p13n,reco)
- Filter for marathon type label.

## 0.10.0 - 2016-09-26
### Added
- Cookie support for status page query.
- Configurable header for status page query.
- Configurable blacklist for services.

## 0.9.0 - 2016-09-22
Some general refactoring.

### Added
- Support for single services outside of marathon.
- Running jobs will be represented by blinking/glowing status icons.
- Styleguide html test.
- Resource Allocation tab. 

## 0.8.0 - 2016-08-15
### Added [experimental]
- Displays peak resource usage of the last 14 days.

## 0.7.1 - 2016-08-12
### Fixed
- Use all found apps to calculate resource allocation, instead of only the filtered ones.

## 0.7.0 - 2016-08-12
### Changed
- Jellyfish does not save previous job status to display the status age anymore, instead it will use the 'stopped timestamp' from the status page (as of Edison-Microservice version 0.69.1).

## 0.6.0
### Added
- Display resource allocation for each vertical, task and application.
- A service will be marked as "ERROR" if the status code of the status page request is >= 500. This is to indicate infrastructure problems, where the application is healthy, but not accessible.

### Changed
- Use Root_App flag to build status path to build the correct status path for services with names that differ from the vertical name.
- Environment Columns should always be the same size.
- Increase size of status indicator (10px -> 15px).

## 0.5.1
### Fixed
- Status age button sets correct parameter.

## 0.5.0
### Added
- Display job messages as tooltip.
- TEST FEATURE: Display job status age (from jellyfish's point of view) for jobs != OK.

### Changed
- Logging will include error types for better analysis.

## 0.4.3 - 2016-07-13
### Fixed
- Fix Query Strings forwarding.

## 0.4.1 - 2016-07-12
### Fixed
- Parameter handling.

## 0.4.0 - 2016-07-12
### Added
- 'all' tab to include all services.
- 'vertical' tag for every service on 'all' tab to identify their source.
- Service counter on tabs.

## 0.3.0 - 2016-07-12
### Added
- Support Marathon subgroups.
- Support status path information in lables.
- Styleguide link.
- Use python argument parser for startup.

### Changed
- Use marathon hostname to identify thread.
- Change button semantics (current state instead of action, eg. Hide jobs -> Jobs hidden).
- Change some ui wording.

### Fixed
- Show empty tab is filter result is empty.
- Handle Marathon not responding.
- Styleguide.

## 0.2.0 - 2016-07-08
### Added
- Show Active only colors.

### Changed
- Buttons now show the actual state instead of action ("Hide Jobs" -> "Jobs hidden"). The "closed eye" icon symbolised that information is hidden from you.

### Issues:
- Status page of all colors of an app identical.

## 0.1.0 - 2016-07-08
First release of Jellyfish.

### Added
- Display status of all apps in Marathon.
- Status level filter.
- Job filter (true/false).
- Name filter.
- Size (heading) parameter.
- Link to Marathon.
- Link to status page.

### Issues:
- Status page of all colors of an app identical.

This changelog is inspired by [keepachangelog.com](http://http://keepachangelog.com/de/)
