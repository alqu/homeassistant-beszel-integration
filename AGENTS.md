# AGENTS.md

## Structure

- Keep user-visible strings in `translations/en.json`.
- Group Beszel field constants by their source struct and sort each group alphabetically.

## Behaviour

- Include Beszel Hub and system context in logs.
- Preserve cached system data during partial API failures.
- Return unavailable data as `None`; do not convert missing measurements to zero.
- Pass authentication failures up as `ConfigEntryAuthFailed` so Home Assistant
  starts reauthentication.

## Compatibility

- Keep configuration and entity names stable unless a migration is included.
- Keep the `hacs.json` and README minimum Home Assistant version equal to the
  `homeassistant` test pin, which must match `pytest-homeassistant-custom-component`;
  Renovate raises them together.
- Declare runtime requirements only in `manifest.json`; the test task installs them
  from there.
