import AVFoundation
import GalleonaireCore
#if os(iOS)
import UIKit
#else
import WatchKit
#endif

enum FeedbackEvent: String { case selected, locked, correct, incorrect, lifelineSelected, lifelineActivated, lifelineResult, nextQuestion, milestone, majorMilestone, victory }

@MainActor final class GameFeedback {
    var settings = GameSettings()
    var voiceOver = false
    private var active = false
    private var music: AVAudioPlayer?
    private var effects: [AVAudioPlayer] = []

    func setActive(_ active: Bool, voiceOver: Bool) {
        self.active = active
        self.voiceOver = voiceOver
        if !active { music?.pause(); effects.forEach { $0.stop() }; effects = [] }
        else { refreshMusic() }
    }
    private func configure() {
        let session = AVAudioSession.sharedInstance()
        #if os(iOS)
        try? session.setCategory(.ambient, mode: .default)
        #else
        try? session.setCategory(.playback, mode: .default, options: [.mixWithOthers])
        #endif
        try? session.setActive(true)
    }
    private func player(_ name: String) -> AVAudioPlayer? {
        guard let url = Bundle.main.url(forResource: name, withExtension: "wav") else { return nil }
        return try? AVAudioPlayer(contentsOf: url)
    }
    func refreshMusic() {
        guard active, settings.enabled(.musicEnabled), settings.value(.musicVolume) > 0 else { music?.pause(); return }
        configure()
        if music == nil { music = player("magical-library"); music?.numberOfLoops = -1 }
        let requested = Float(settings.value(.musicVolume)) / 100
        music?.volume = voiceOver ? min(requested, 0.06) : requested
        if AVAudioSession.sharedInstance().secondaryAudioShouldBeSilencedHint { music?.pause() }
        else { music?.play() }
    }
    func play(_ event: FeedbackEvent) {
        guard active else { return }
        if settings.enabled(.effectsEnabled), settings.value(.effectsVolume) > 0 {
            configure()
            effects.removeAll { !$0.isPlaying }
            if let effect = player(event.rawValue) {
                effect.volume = min(Float(settings.value(.effectsVolume)) / 100, voiceOver ? 0.18 : 1)
                effects.append(effect)
                effect.play()
            }
        }
        guard settings.enabled(.hapticsEnabled) else { return }
        #if os(iOS)
        switch event {
        case .incorrect: UINotificationFeedbackGenerator().notificationOccurred(.error)
        case .correct, .victory, .milestone, .majorMilestone: UINotificationFeedbackGenerator().notificationOccurred(.success)
        case .locked: UIImpactFeedbackGenerator(style: .medium).impactOccurred()
        default: UISelectionFeedbackGenerator().selectionChanged()
        }
        #else
        let type: WKHapticType
        switch event {
        case .incorrect: type = .failure
        case .correct, .victory, .milestone, .majorMilestone: type = .success
        case .locked: type = .directionUp
        default: type = .click
        }
        WKInterfaceDevice.current().play(type)
        #endif
    }
}
