# Galleonaire

Native iPhone and Apple Watch edition of Sidney Tambin's retro handheld quiz.
This is a separate project. It does not share application identifiers, game data,
source control, release pipelines or assets with Tennis Tracker.

The original handheld implementation is read-only reference material. New Apple
implementation, tests and release records live here.

## Layout

- `Apple/`: native application, shared Swift engine, tests and Xcode configuration.
- `Scripts/`: question migration, validation and release tooling.
- `Docs/`: original rules, accessibility evidence, asset provenance and release status.
- `Reference/`: preserved question-bank snapshot, without personal scores or saves.

Initial testing version: 0.1.0. Distribution is not complete until verified in
TestFlight; a successful build alone is not evidence of device accessibility.
