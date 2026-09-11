# Galleonaire Privacy

Updated 11 September 2026. Galleonaire is a personal project by Sidney Tambin.

## Gameplay and Preferences

Galleonaire has no developer-operated server, advertising, tracking or analytics SDK.
It does not require an account. Questions, answers, original artwork and audio are
included in the application so that games work offline.

The current game, question history and highest prize are stored on the device.
Music, sound-effect and haptic preferences are stored locally and exchanged with
the user's paired iPhone or Apple Watch using Apple's WatchConnectivity framework.
A randomly generated preference identifier and revision numbers resolve changes
between those two devices. This does not send either active game to the other
device, or send gameplay to the developer.

Apple's device backup and restore services may include local app data according
to the user's system settings. Starting a new game replaces the active game;
Reset Highest Prize resets that record without ending the current game.

## TestFlight and Feedback

Apple's TestFlight service separately collects beta-testing information, including
crash logs and usage information, and makes beta feedback available to the developer.
Contact details may also be available, depending on the invitation and feedback route.
This is distinct from in-app analytics, which Galleonaire does not include.

Feedback submitted through TestFlight or by email is received for investigating
problems and improving the app. Do not include passwords or unrelated personal
information in feedback or screenshots.

Apple explains its beta data handling in [TestFlight Privacy and Data](https://testflight.apple.com/)
and the [TestFlight terms](https://www.apple.com/legal/internet-services/itunes/testflight/).

## Contact

For questions about Galleonaire or its handling of beta feedback, contact
sidney.tambin@googlemail.com.

## Release Declaration Check

This document describes the current implementation. Before publishing privacy
declarations, compare them with the actual shipped code and any beta information
received through Apple. No App Store privacy declaration has been submitted for
Galleonaire yet. This file is not currently a publicly hosted privacy-policy URL.
