import SwiftUI
import GalleonaireCore

struct SheetContent<Content: View>: View {
    @Environment(\.dismiss) private var dismiss
    let title: String
    @ViewBuilder var content: () -> Content
    var body: some View {
        NavigationStack {
            List { content() }
                .navigationTitle(title)
                .toolbar { ToolbarItem(placement: .confirmationAction) { Button("Done") { dismiss() } } }
                .tint(Palette.gold)
        }.preferredColorScheme(.dark)
    }
}

struct TabContent<Content: View>: View {
    let title: String
    @ViewBuilder var content: () -> Content
    var body: some View {
        List {
            Text(title).font(.system(.title2, design: .serif, weight: .bold))
                .foregroundStyle(Palette.gold).accessibilityAddTraits(.isHeader)
                .accessibilityIdentifier("tabHeading")
            content()
        }
        .scrollContentBackground(.hidden)
        .background(Palette.background)
        .foregroundStyle(Palette.text)
        .tint(Palette.gold)
    }
}

struct LifelinesView: View {
    @EnvironmentObject private var store: GameStore
    let activate: (Lifeline) -> Void
    var body: some View {
        SheetContent(title: "Lifelines") {
            ForEach(Lifeline.allCases) { line in
                let used = store.game?.usedLifelines.contains(line) ?? false
                Button { activate(line) } label: {
                    VStack(alignment: .leading, spacing: 6) {
                        Text(line.name).font(.headline)
                        Text(used ? "Used this game" : line.detail).font(.caption)
                    }.fixedSize(horizontal: false, vertical: true)
                }
                .disabled(used || store.game?.phase != .question)
                .accessibilityLabel(line.name).accessibilityValue(used ? "Used" : "Available")
                .accessibilityHint(line.detail)
                .accessibilityIdentifier("lifeline-\(line.rawValue)")
            }
        }
    }
}

struct SettingsView: View {
    @EnvironmentObject private var store: GameStore
    @State private var reset = false
    var body: some View {
        TabContent(title: "Settings") {
            Section("Music") {
                Toggle("Background Music", isOn: toggle(.musicEnabled)).accessibilityIdentifier("musicEnabled")
                volume("Music Volume", key: .musicVolume)
            }
            Section("Feedback") {
                Toggle("Sound Effects", isOn: toggle(.effectsEnabled))
                volume("Sound Effects Volume", key: .effectsVolume)
                Toggle("Haptics", isOn: toggle(.hapticsEnabled))
            }
            Section("Preview Sounds") {
                ForEach(FeedbackEvent.allCases, id: \.rawValue) { event in
                    Button { store.feedback.play(event) } label: { Label(event.title, systemImage: "speaker.wave.2") }
                        .disabled(store.settings.effectsGain == 0)
                        .accessibilityHint("Plays this sound at your sound effects volume.")
                        .accessibilityIdentifier("preview-\(event.rawValue)")
                }
            }
            Section("Game Records") {
                Text("Highest prize reached: \(galleons(store.highScore))")
                Button("Reset Highest Prize", role: .destructive) { reset = true }
            }
            Section("About") {
                Text("Galleonaire 0.1.0\nThe Magical Quiz Game")
                Text("Your highest prize stays on this device. A fresh app launch returns to the main menu, without restoring an unfinished game. Music, sound and haptic preferences sync with your paired companion when available. No advertising, analytics, accounts or tracking.")
                Text("An independent fan-made quiz. Not affiliated with or endorsed by the authors, publishers or film studios referenced in the questions. Galleons are fictional points, not money.")
                Text("Original app artwork and nonverbal audio created for Galleonaire. No film music or recorded question speech is included.")
            }
        }
        .alert("Reset your highest prize? Your current game is kept.", isPresented: $reset) {
            Button("Reset Highest Prize", role: .destructive) { store.resetHighScore() }
            Button("Cancel", role: .cancel) {}
        }
    }
    private func toggle(_ key: SettingKey) -> Binding<Bool> { Binding(get: { store.settings.enabled(key) }, set: { store.set(key, value: $0 ? 1 : 0) }) }
    private func volume(_ label: String, key: SettingKey) -> some View {
        VStack(alignment: .leading, spacing: 8) {
            Text("\(label): \(store.settings.value(key)) percent").accessibilityHidden(true)
            Slider(value: Binding(get: { Double(store.settings.value(key)) }, set: { store.set(key, value: Int($0.rounded())) }), in: 0...100, step: 1)
                .accessibilityLabel(label).accessibilityValue("\(store.settings.value(key)) percent")
                .accessibilityAdjustableAction { direction in
                    switch direction {
                    case .increment: store.set(key, value: store.settings.value(key) + 5)
                    case .decrement: store.set(key, value: store.settings.value(key) - 5)
                    @unknown default: break
                    }
                }
                .accessibilityHint("Zero is off. One hundred percent is full volume. Adjusts in five percent steps with VoiceOver.")
                .accessibilityIdentifier(key.rawValue)
        }
    }
}

struct LadderView: View {
    @EnvironmentObject private var store: GameStore
    var body: some View {
        SheetContent(title: "Prize Ladder") {
            ForEach(Array(QuestionBank.prizeLadder.enumerated()), id: \.offset) { index, prize in
                let current = store.game?.level == index + 1
                let safe = index == 4 || index == 9
                HStack(alignment: .top) {
                    Text("\(index + 1)").foregroundStyle(Palette.gold)
                    VStack(alignment: .leading) {
                        Text(galleons(prize))
                        if current { Text("Current question").font(.caption) }
                        if safe { Text("Guaranteed milestone").font(.caption).foregroundStyle(Palette.mint) }
                    }
                    Spacer()
                    if safe { Image(systemName: "shield.lefthalf.filled").accessibilityHidden(true) }
                }.accessibilityElement(children: .combine)
            }
        }
    }
}

struct RulesView: View {
    var body: some View {
        TabContent(title: "How to play") {
            Section("The Challenge") {
                Text("Answer fifteen questions to win one million fictional galleons. Each question has four answers and exactly one is correct. There is no time limit.")
                Text("Activate an answer to reveal the result immediately. With VoiceOver, focus an answer and double-tap to choose it. There is no locking or confirmation step. The result gives the correct answer and a short explanation, followed by Next Question.")
                Text("Switch tabs or briefly leave the app running without losing your game. A fresh launch always returns to the main menu: unfinished games are not saved, but your highest prize is kept. When a game ends, Main Menu returns to the opening screen. Play Again starts a new game.")
            }
            Section("Prizes") {
                Text("Complete question 5 to guarantee 1,000 galleons; complete question 10 to guarantee 32,000. An incorrect answer ends the game with your guaranteed prize. Walk Away keeps your current winnings.")
                Text("Highest prize reached records your furthest progress, even when you later lose. These are game points, with no real-world value or payment.")
            }
            Section("Three Lifelines") {
                ForEach(Lifeline.allCases) { line in Text("\(line.name). \(line.detail)") }
                Text("Fifty-Fifty leaves only two answer buttons. Ask the Audience adds each vote percentage to its answer button; after Fifty-Fifty, votes are shown as a share of the remaining answers. The audience may be wrong.")
                Text("Swap Question does not restore lifelines already spent. A replacement question starts with all four answers available.")
            }
            Section("Question Sources") {
                Text("The original 300-question handheld collection covers magical books and their film adaptations. Each result includes an explanation and source note. Book and film details may differ.")
            }
        }
    }
}
