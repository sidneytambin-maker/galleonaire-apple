import SwiftUI
import GalleonaireCore

enum Palette {
    static let background = Color(red: 0.025, green: 0.045, blue: 0.045)
    static let panel = Color(red: 0.075, green: 0.13, blue: 0.13)
    static let gold = Color(red: 1, green: 0.83, blue: 0.36)
    static let mint = Color(red: 0.54, green: 0.94, blue: 0.76)
    static let rose = Color(red: 1, green: 0.68, blue: 0.69)
    static let text = Color(red: 0.97, green: 0.98, blue: 0.95)
}

func galleons(_ value: Int) -> String { "\(value.formatted()) galleons" }

struct GameView: View {
    @EnvironmentObject private var store: GameStore
    @Environment(\.scenePhase) private var scenePhase
    @Environment(\.accessibilityVoiceOverEnabled) private var voiceOver
    @Environment(\.accessibilityReduceMotion) private var reduceMotion
    @AccessibilityFocusState private var focus: Focus?
    @State private var sheet: Sheet?
    @State private var confirmation: Confirmation?
    @State private var lifelineResult: Lifeline?
    @State private var announceLifeline = false
    private enum Focus: Hashable { case question, result, lifeline, start }
    private enum Sheet: String, Identifiable { case settings, rules, ladder, lifelines; var id: String { rawValue } }
    private enum Confirmation { case restart, walkAway, lock }

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 20) {
                masthead
                if let game = store.game, let question = store.question {
                    questionContent(game, question)
                } else {
                    home
                }
            }
            .frame(maxWidth: 680)
            .padding()
            .frame(maxWidth: .infinity)
        }
        .background(Palette.background.ignoresSafeArea())
        .foregroundStyle(Palette.text)
        .tint(Palette.gold)
        .preferredColorScheme(.dark)
        .sheet(item: $sheet, onDismiss: {
            if announceLifeline {
                focus = lifelineResult == .freePass ? .question : .lifeline
                store.feedback.play(.lifelineResult)
                if lifelineResult == .freePass { AccessibilityNotification.Announcement("Free Pass used. Replacement question at the same prize level.").post() }
                announceLifeline = false
            } else { focus = store.game == nil ? .start : .question }
        }) { selected in
            switch selected {
            case .settings: SettingsView()
            case .rules: RulesView()
            case .ladder: LadderView()
            case .lifelines: LifelinesView { line in
                if store.use(line) {
                    lifelineResult = line
                    announceLifeline = true
                    sheet = nil
                }
            }
            }
        }
        .alert(confirmationTitle, isPresented: Binding(get: { confirmation != nil }, set: { if !$0 { confirmation = nil } })) {
            switch confirmation {
            case .restart: Button("Start New Game", role: .destructive) { store.newGame(); lifelineResult = nil; focus = .question }
            case .walkAway: Button("Walk Away with \(galleons(store.game?.prize ?? 0))") { store.walkAway(); focus = .result }
            case .lock: Button("Lock Answer") { store.lockAnswer(); focus = .result }
            case nil: EmptyView()
            }
            Button("Cancel", role: .cancel) { confirmation = nil }
        }
        .alert("Game Not Saved", isPresented: Binding(get: { store.errorMessage != nil }, set: { if !$0 { store.errorMessage = nil } })) {
            Button("OK") { store.errorMessage = nil }
        } message: { Text(store.errorMessage ?? "") }
        .onAppear { updateAudio(); focus = store.game == nil ? .start : .question }
        .onChange(of: scenePhase) { _, _ in updateAudio() }
        .onChange(of: voiceOver) { _, _ in updateAudio() }
        .onChange(of: store.question?.id) { _, _ in focus = .question }
        .task(id: store.game?.phase) {
            guard store.game?.phase != .question else { return }
            try? await Task.sleep(for: .milliseconds(200))
            guard !Task.isCancelled else { return }
            store.resultFeedback()
        }
    }

    private var masthead: some View {
        HStack(alignment: .center, spacing: 12) {
            #if os(iOS)
            Image("GalleonMark").resizable().scaledToFit().frame(width: 46, height: 46).accessibilityHidden(true)
            #endif
            Text("Galleonaire").font(mastheadFont).foregroundStyle(Palette.gold)
                .accessibilityHidden(store.game != nil).accessibilitySortPriority(-10)
            Spacer(minLength: 4)
            Button { sheet = .settings } label: {
                Image(systemName: "gearshape")
                    .frame(width: 48, height: 48)
                    .contentShape(Rectangle())
            }
            .buttonStyle(.plain).frame(width: 48, height: 48)
            .accessibilityLabel("Settings").accessibilitySortPriority(-10)
            .accessibilityIdentifier("settingsButton").help("Settings")
        }
    }

    private var mastheadFont: Font {
        #if os(watchOS)
        .system(.headline, design: .serif, weight: .bold)
        #else
        .system(.title3, design: .serif, weight: .bold)
        #endif
    }

    private var home: some View {
        VStack(alignment: .leading, spacing: 20) {
            #if os(iOS)
            Image("GalleonMark").resizable().scaledToFit().frame(maxWidth: 220).frame(maxWidth: .infinity).accessibilityHidden(true)
            Text("The Magical Quiz Game").font(.system(.title2, design: .serif, weight: .semibold)).accessibilityAddTraits(.isHeader)
            Text("Fifteen questions. One million galleons.").font(.headline)
            #endif
            command("New Game", icon: "play.fill") { store.newGame(); focus = .question }
                .accessibilityFocused($focus, equals: .start).disabled(store.engine == nil)
            #if os(watchOS)
            HStack(spacing: 8) {
                Image("GalleonMark").resizable().scaledToFit().frame(width: 36, height: 36).accessibilityHidden(true)
                Text("The Magical Quiz Game").font(.subheadline).foregroundStyle(Palette.mint)
            }
            #endif
            Text("Highest prize reached: \(galleons(store.highScore))").font(.subheadline)
            command("How to Play", icon: "book") { sheet = .rules }
            command("Prize Ladder", icon: "list.number") { sheet = .ladder }
        }
    }

    @ViewBuilder private func questionContent(_ game: GameState, _ q: Question) -> some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("Question \(game.level) of 15").font(.headline).foregroundStyle(Palette.gold).accessibilityAddTraits(.isHeader)
            Text(q.text).font(.system(.title2, design: .serif, weight: .semibold))
                .fixedSize(horizontal: false, vertical: true)
                .accessibilityFocused($focus, equals: .question)
                .accessibilityIdentifier("questionText")
                .accessibilityActions {
                    if game.phase == .question { Button("Lifelines") { sheet = .lifelines } }
                    Button("Prize Ladder") { sheet = .ladder }
                    Button("Settings") { sheet = .settings }
                }
        }
        .accessibilitySortPriority(100)
        VStack(spacing: 10) {
            ForEach(Array(q.answers.indices), id: \.self) { index in answer(index, game: game, question: q) }
        }.accessibilitySortPriority(90)

        if game.phase == .question {
            if let selected = game.selectedAnswer {
                command("Lock Answer \(letter(selected))", icon: "lock.fill") { confirmation = .lock }
                    .accessibilityLabel("Lock answer \(letter(selected)), \(q.answers[selected])")
                    .accessibilityIdentifier("lockAnswer")
                    .accessibilitySortPriority(80)
            }
            command("Lifelines", icon: "sparkles") { store.feedback.play(.lifelineSelected); sheet = .lifelines }
                .accessibilityValue("\(3 - game.usedLifelines.count) available")
                .accessibilitySortPriority(70)
            if let result = lifelineResult, result != .freePass {
                Text(result == .fiftyFifty ? "Fifty-Fifty used. Two incorrect answers eliminated." : "Audience vote received. The audience may be wrong.")
                    .accessibilityFocused($focus, equals: .lifeline)
                    .accessibilitySortPriority(65)
            }
            if let votes = game.audience {
                VStack(alignment: .leading, spacing: 6) {
                    Text("Audience Vote").font(.headline).accessibilityAddTraits(.isHeader)
                    ForEach(0..<4) { i in
                        VStack(alignment: .leading, spacing: 4) {
                            Text("\(letter(i)): \(q.answers[i]), \(votes[i]) percent")
                            ProgressView(value: Double(votes[i]), total: 100).tint(Palette.mint).accessibilityHidden(true)
                        }.accessibilityElement(children: .combine)
                    }
                    Text("A simulated vote, not a guarantee.").font(.caption)
                }.accessibilitySortPriority(60)
            }
        } else {
            result(game, q).accessibilitySortPriority(80)
        }

        VStack(alignment: .leading, spacing: 8) {
            Text(game.isFinished ? "Final prize: \(galleons(game.banked))" : "Playing for \(galleons(QuestionBank.prizeLadder[game.level - 1]))")
                .font(.headline).foregroundStyle(Palette.gold)
            if !game.isFinished { Text("Won: \(galleons(game.prize)). Guaranteed: \(galleons(store.guarantee)).").font(.subheadline) }
            ProgressView(value: Double(game.phase == .correct || game.phase == .won ? game.level : game.level - 1), total: 15)
                .tint(Palette.gold).accessibilityHidden(true)
        }.accessibilityElement(children: .combine).accessibilitySortPriority(40)

        command("Prize Ladder", icon: "list.number") { sheet = .ladder }.accessibilitySortPriority(30)
        if !game.isFinished {
            command("Walk Away", icon: "door.left.hand.open") { confirmation = .walkAway }.accessibilitySortPriority(20)
            command("Restart Game", icon: "arrow.counterclockwise") { confirmation = .restart }.accessibilitySortPriority(10)
        }
    }

    private func answer(_ index: Int, game: GameState, question: Question) -> some View {
        let eliminated = game.eliminated.contains(index)
        let selected = game.selectedAnswer == index
        let revealed = [.correct, .lost, .won].contains(game.phase)
        let correct = revealed && question.correctIndex == index
        let wrong = revealed && selected && !correct
        let state = eliminated ? "Eliminated" : correct ? "Correct answer" : wrong ? "Locked, incorrect answer" : selected ? (revealed ? "Locked" : "Selected") : ""
        let accent = correct ? Palette.mint : wrong ? Palette.rose : selected ? Palette.gold : Palette.text
        return Button {
            if reduceMotion { store.select(index) }
            else { withAnimation(.easeOut(duration: 0.15)) { store.select(index) } }
        } label: {
            HStack(alignment: .top, spacing: 10) {
                Text(letter(index)).font(.headline).foregroundStyle(accent).frame(width: 22)
                VStack(alignment: .leading, spacing: 5) {
                    Text(question.answers[index]).fixedSize(horizontal: false, vertical: true).font(.body.weight(.medium))
                    if !state.isEmpty { Text(state).font(.caption.weight(.semibold)).foregroundStyle(accent) }
                }.frame(maxWidth: .infinity, alignment: .leading)
                if correct { Image(systemName: "checkmark.circle.fill").foregroundStyle(Palette.mint) }
                else if wrong || eliminated { Image(systemName: "xmark.circle").foregroundStyle(wrong ? Palette.rose : Palette.text) }
                else if selected { Image(systemName: "checkmark").foregroundStyle(Palette.gold) }
            }
            .padding(12).frame(maxWidth: .infinity, minHeight: 52, alignment: .leading)
            .background(Palette.panel, in: RoundedRectangle(cornerRadius: 8))
            .overlay(RoundedRectangle(cornerRadius: 8).stroke(selected || correct || wrong ? accent : Palette.text.opacity(0.3), lineWidth: selected ? 2 : 1))
            .contentShape(Rectangle())
        }
        .buttonStyle(.plain).foregroundStyle(Palette.text)
        .disabled(game.phase != .question || eliminated)
        .accessibilityElement(children: .combine)
        .accessibilityLabel("\(letter(index)), \(question.answers[index])")
        .accessibilityValue(state == "Selected" ? "" : state)
        .accessibilityAddTraits(selected ? [.isButton, .isSelected] : .isButton)
        .accessibilityHint(game.phase == .question && !eliminated ? "Selects this answer. You can review it before locking." : "")
        .accessibilityIdentifier("answer\(index)")
    }

    private func result(_ game: GameState, _ q: Question) -> some View {
        VStack(alignment: .leading, spacing: 12) {
            Text(resultTitle(game)).font(.title2.bold()).foregroundStyle(game.phase == .lost ? Palette.rose : Palette.mint)
                .accessibilityAddTraits(.isHeader).accessibilityFocused($focus, equals: .result)
                .accessibilityIdentifier("gameResult")
            if game.phase != .walkedAway {
                Text("Correct answer: \(q.answers[q.correctIndex]). \(q.explanation)").fixedSize(horizontal: false, vertical: true)
                Text(q.source).font(.caption)
            }
            if game.phase == .correct {
                if [1000, 32000].contains(game.prize) { Label("\(galleons(game.prize)) guaranteed", systemImage: "shield.lefthalf.filled").foregroundStyle(Palette.gold) }
                command("Next Question", icon: "arrow.right") { lifelineResult = nil; store.nextQuestion(); focus = .question }
                    .accessibilityIdentifier("nextQuestion")
            } else {
                Text("You leave with \(galleons(game.banked)). Highest prize reached: \(galleons(store.highScore)).")
                command("Play Again", icon: "arrow.counterclockwise") { lifelineResult = nil; store.newGame(); focus = .question }
            }
        }
    }

    private var confirmationTitle: String {
        switch confirmation {
        case .restart: return "End this game and start again?"
        case .walkAway: return "Finish with \(galleons(store.game?.prize ?? 0))?"
        case .lock:
            if let index = store.game?.selectedAnswer, let q = store.question { return "Final answer: \(letter(index)), \(q.answers[index])?" }
            return "Lock this answer?"
        case nil: return ""
        }
    }
    private func resultTitle(_ game: GameState) -> String {
        switch game.phase {
        case .correct: return "Correct!"
        case .lost: return "Not this time"
        case .won: return "A million-galleon triumph!"
        case .walkedAway: return "Prize banked"
        case .question: return ""
        }
    }
    private func updateAudio() { store.feedback.setActive(scenePhase == .active, voiceOver: voiceOver) }
    private func letter(_ index: Int) -> String { ["A", "B", "C", "D"][index] }
}

func command(_ title: String, icon: String, action: @escaping () -> Void) -> some View {
    Button(action: action) {
        Label(title, systemImage: icon).font(.body.weight(.semibold))
            .frame(maxWidth: .infinity, minHeight: 44, alignment: .leading)
            .padding(.horizontal, 12).padding(.vertical, 5)
            .background(Palette.panel, in: RoundedRectangle(cornerRadius: 8))
            .contentShape(Rectangle())
    }.buttonStyle(.plain).foregroundStyle(Palette.gold)
}
