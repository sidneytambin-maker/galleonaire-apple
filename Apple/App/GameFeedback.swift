import AVFoundation
import GalleonaireCore
#if os(iOS)
import UIKit
#else
import WatchKit
#endif

enum FeedbackEvent: String, CaseIterable {
    case correct, incorrect, fiftyFifty, audience, swapQuestion, nextQuestion, milestone, majorMilestone, finalQuestion, victory
    var title: String {
        switch self {
        case .correct: return "Correct Answer"
        case .incorrect: return "Incorrect Answer"
        case .fiftyFifty: return "Fifty-Fifty"
        case .audience: return "Ask the Audience"
        case .swapQuestion: return "Swap Question"
        case .nextQuestion: return "Next Question"
        case .milestone: return "First Guaranteed Prize"
        case .majorMilestone: return "Second Guaranteed Prize"
        case .finalQuestion: return "Final Question"
        case .victory: return "Million-Galleon Victory"
        }
    }
}

@MainActor final class GameFeedback {
    var settings = GameSettings()
    private var active = false
    private var music: AVAudioPlayer?
    private var effects: [AVAudioPlayer] = []
    private var lossHaptics: Task<Void, Never>?

    func setActive(_ active: Bool) {
        self.active = active
        if !active { lossHaptics?.cancel(); lossHaptics = nil; music?.pause(); effects.forEach { $0.stop() }; effects = [] }
        else { refreshMusic() }
    }
    func refreshVolumes() {
        if !settings.enabled(.hapticsEnabled) { lossHaptics?.cancel(); lossHaptics = nil }
        effects.removeAll { !$0.isPlaying }
        for effect in effects {
            effect.volume = settings.effectsGain
            if settings.effectsGain == 0 { effect.stop() }
        }
        refreshMusic()
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
        guard active, settings.musicGain > 0 else { music?.pause(); return }
        configure()
        if music == nil { music = player("magical-library"); music?.numberOfLoops = -1 }
        music?.volume = settings.musicGain
        if AVAudioSession.sharedInstance().secondaryAudioShouldBeSilencedHint { music?.pause() }
        else { music?.play() }
    }
    func play(_ event: FeedbackEvent) {
        guard active else { return }
        if settings.effectsGain > 0 {
            configure()
            effects.removeAll { !$0.isPlaying }
            if let effect = player(event.rawValue) {
                effect.volume = settings.effectsGain
                effects.append(effect)
                effect.play()
            }
        }
        guard settings.enabled(.hapticsEnabled) else { return }
        lossHaptics?.cancel()
        if event == .incorrect { playLossHaptics(); return }
        #if os(iOS)
        switch event {
        case .incorrect: UINotificationFeedbackGenerator().notificationOccurred(.error)
        case .correct, .victory, .milestone, .majorMilestone: UINotificationFeedbackGenerator().notificationOccurred(.success)
        default: UISelectionFeedbackGenerator().selectionChanged()
        }
        #else
        let type: WKHapticType
        switch event {
        case .incorrect: type = .failure
        case .correct, .victory, .milestone, .majorMilestone: type = .success
        default: type = .click
        }
        WKInterfaceDevice.current().play(type)
        #endif
    }
    /// Three separated failure beats, lasting about 1.5 seconds; cancelled on exit or mute.
    /// System feedback preserves the user's device accessibility and haptic preferences.
    private func playLossHaptics() {
        lossHaptics = Task { [weak self] in
            for beat in 0..<3 {
                guard let self, !Task.isCancelled, self.active,
                      self.settings.enabled(.hapticsEnabled) else { return }
                #if os(iOS)
                UINotificationFeedbackGenerator().notificationOccurred(.error)
                UIImpactFeedbackGenerator(style: .heavy).impactOccurred(intensity: 1)
                #else
                WKInterfaceDevice.current().play(.failure)
                #endif
                if beat < 2 { try? await Task.sleep(for: .milliseconds(650)) }
            }
        }
    }

}
