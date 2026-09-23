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
    @Binding var selectedTab: AppTab
    @ScaledMetric(relativeTo: .headline) private var answerLetterWidth: CGFloat = 22
    @AccessibilityFocusState private var focus: Focus?
    @State private var sheet: Sheet?
    @State private var confirmation: Confirmation?
    @State private var lifelineResult: Lifeline?
    @State private var announceLifeline = false
    private enum Focus: Hashable { case heading, question(String), result }
    private var questionFocus: Focus { store.question.map { .question($0.id) } ?? .heading }
    private var destination: Focus { store.game == nil ? .heading : store.game?.phase == .question ? questionFocus : .result }
    private enum Sheet: String, Identifiable { case ladder, lifelines; var id: String { rawValue } }
    private enum Confirmation { case restart, walkAway }

    var body: some View {
        ScrollViewReader { scroll in
            ScrollView {
                VStack(alignment: .leading, spacing: pageSpacing) {
                    masthead.id("gameTop")
                    if let game = store.game, let question = store.question {
                        if game.phase == .question { questionContent(game, question).id(question.id) }
                        else { result(game, question) }
                    } else { home }
                }
                .frame(maxWidth: 680)
                .padding()
                .frame(maxWidth: .infinity)
            }
            .task(id: destination) {
                // Let the old answer controls leave the accessibility tree before moving focus.
                focus = nil
                await Task.yield()
                guard !Task.isCancelled, selectedTab == .game, sheet == nil else { return }
                scroll.scrollTo("gameTop", anchor: .top)
                focus = destination
            }
            .onChange(of: selectedTab) { _, tab in
                if tab == .game { scroll.scrollTo("gameTop", anchor: .top); focus = .heading }
            }
        }
        .background(Palette.background.ignoresSafeArea())
        .overlay { AnswerGlow(outcome: store.lastAnswer).allowsHitTesting(false).accessibilityHidden(true) }
        .foregroundStyle(Palette.text)
        .tint(Palette.gold)
        .preferredColorScheme(.dark)
        .sheet(item: $sheet, onDismiss: {
            if announceLifeline, let line = lifelineResult {
                focus = questionFocus
                let message: String
                switch line {
                case .fiftyFifty: message = "Fifty-Fifty used. Two answers remain."
                case .audience: message = "Audience votes are now on each answer. The audience may be wrong."
                case .freePass: message = "Question swapped. Here is your replacement at the same prize level."
                }
                AccessibilityNotification.Announcement(message).post()
                announceLifeline = false
            } else { focus = destination }
        }) { selected in
            switch selected {
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
            case .restart: Button("Start New Game", role: .destructive) { store.newGame(); lifelineResult = nil }
            case .walkAway: Button("Walk Away with \(galleons(store.game?.prize ?? 0))") { store.walkAway() }
            case nil: EmptyView()
            }
            Button("Cancel", role: .cancel) { confirmation = nil }
        }
        .alert("Game Not Saved", isPresented: Binding(get: { store.errorMessage != nil }, set: { if !$0 { store.errorMessage = nil } })) {
            Button("OK") { store.errorMessage = nil }
        } message: { Text(store.errorMessage ?? "") }
        .onAppear { focus = .heading }
    }

    private var masthead: some View {
        HStack(alignment: .center, spacing: 12) {
            VStack(alignment: .leading, spacing: 4) {
                Text("Galleonaire").font(brandFont).foregroundStyle(Palette.gold)
                Text("A magical quiz game").font(.subheadline).foregroundStyle(Palette.mint)
            }.frame(maxWidth: .infinity, alignment: .leading)
        }
        .fixedSize(horizontal: false, vertical: true)
        .accessibilityElement(children: .ignore)
        .accessibilityLabel("Galleonaire: a magical quiz game")
        .accessibilityAddTraits(.isHeader)
        .accessibilitySortPriority(1000)
        .accessibilityFocused($focus, equals: .heading)
        .accessibilityIdentifier("gameHeading")
    }

    private var home: some View {
        VStack(alignment: .leading, spacing: pageSpacing) {
            #if os(iOS)
            VStack(spacing: 0) {
                Color.clear.frame(height: 140).accessibilityHidden(true)
                VStack(alignment: .leading, spacing: 4) {
                    Text("The million-galleon challenge").font(.title3.weight(.bold))
                    Text("15 questions. 3 lifelines. Your knowledge.").font(.subheadline)
                }.fixedSize(horizontal: false, vertical: true)
                    .foregroundStyle(.white).padding(16)
                    .frame(maxWidth: .infinity, alignment: .leading).background(.black.opacity(0.86))
            }.background { QuizChamberArtwork() }
                .accessibilityElement(children: .ignore)
                .accessibilityLabel("Fifteen questions. Three lifelines. One million galleons.")
            #endif
            command("New Game", icon: "play.fill", emphasized: true) { store.newGame() }
                .disabled(store.engine == nil)
                .accessibilityIdentifier("newGame")
            #if os(watchOS)
            QuizChamberArtwork().aspectRatio(1.7, contentMode: .fit).accessibilityHidden(true)
            Text("Fifteen questions. One million galleons.").font(.caption)
            #endif
            Text("Highest prize reached: \(galleons(store.highScore))").font(.subheadline)
            command("Prize Ladder", icon: "list.number") { sheet = .ladder }
        }
    }

    private var pageSpacing: CGFloat {
        #if os(watchOS)
        12
        #else
        20
        #endif
    }
    private var brandFont: Font {
        #if os(watchOS)
        .system(.headline, design: .serif, weight: .bold)
        #else
        .system(.title2, design: .serif, weight: .bold)
        #endif
    }

    @ViewBuilder private func questionContent(_ game: GameState, _ q: Question) -> some View {
        if let previous = store.lastAnswer, previous.phase == .correct {
            VStack(alignment: .leading, spacing: 8) {
                Label("Correct! \(galleons(previous.prize))", systemImage: "checkmark.seal.fill")
                    .font(.subheadline.weight(.semibold)).foregroundStyle(Palette.mint)
                Text("Previous answer: \(previous.question.answers[previous.question.correctIndex])")
                    .font(.subheadline.weight(.semibold))
                Text(previous.question.explanation).font(.subheadline)
            }
            .fixedSize(horizontal: false, vertical: true)
            .padding(14).frame(maxWidth: .infinity, alignment: .leading)
            .background(Palette.panel, in: RoundedRectangle(cornerRadius: 12))
            .overlay(RoundedRectangle(cornerRadius: 12).stroke(Palette.mint, lineWidth: 2))
            .accessibilityElement(children: .combine)
            .accessibilityIdentifier("previousAnswer")
        }
        VStack(alignment: .leading, spacing: 10) {
            ViewThatFits(in: .horizontal) {
                HStack(alignment: .firstTextBaseline) {
                    Text("Question \(game.level) of 15")
                    Spacer(minLength: 12)
                    Text(galleons(QuestionBank.prizeLadder[game.level - 1]))
                }.fixedSize(horizontal: true, vertical: false)
                VStack(alignment: .leading, spacing: 4) {
                    Text("Question \(game.level) of 15")
                    Text(galleons(QuestionBank.prizeLadder[game.level - 1]))
                }
            }.font(.subheadline.weight(.semibold)).foregroundStyle(Palette.gold)
            PrizeTrack(completed: game.level - 1)
            Text(q.text).font(questionFont)
                .fixedSize(horizontal: false, vertical: true)
        }
        .padding(16).frame(maxWidth: .infinity, alignment: .leading)
        .background(LinearGradient(colors: [Palette.panel, Palette.background], startPoint: .topLeading, endPoint: .bottomTrailing), in: RoundedRectangle(cornerRadius: 14))
        .overlay(RoundedRectangle(cornerRadius: 14).stroke(Palette.gold.opacity(0.8), lineWidth: 1))
        .accessibilityElement(children: .ignore)
        .accessibilityLabel(questionSummary(game, q))
        .accessibilityAddTraits(.isHeader)
        .accessibilityFocused($focus, equals: .question(q.id))
        .accessibilityIdentifier("questionText")
        .accessibilityActions {
            Button("Lifelines") { sheet = .lifelines }
            Button("Prize Ladder") { sheet = .ladder }
            Button("Settings") { selectedTab = .settings }
        }

        #if os(iOS)
        QuizChamberArtwork().frame(height: 76).accessibilityHidden(true)
        #endif

        VStack(spacing: 10) {
            ForEach(game.visibleAnswers, id: \.self) { index in answer(index, game: game, question: q) }
        }
        command("Lifelines", icon: "sparkles") { sheet = .lifelines }
            .accessibilityValue("\(3 - game.usedLifelines.count) available")
            .accessibilityIdentifier("lifelines")
        VStack(alignment: .leading, spacing: 8) {
            Text("Playing for \(galleons(QuestionBank.prizeLadder[game.level - 1]))")
                .font(.headline).foregroundStyle(Palette.gold)
            Text("Won: \(galleons(game.prize)). Guaranteed: \(galleons(store.guarantee)).").font(.subheadline)
        }.accessibilityElement(children: .combine)
        command("Prize Ladder", icon: "list.number") { sheet = .ladder }
        command("Walk Away", icon: "door.left.hand.open") { confirmation = .walkAway }.accessibilityIdentifier("walkAway")
        command("Restart Game", icon: "arrow.counterclockwise") { confirmation = .restart }
    }

    private var questionFont: Font {
        #if os(watchOS)
        .system(.headline, design: .serif, weight: .semibold)
        #else
        .system(.title2, design: .serif, weight: .semibold)
        #endif
    }

    private func answer(_ index: Int, game: GameState, question: Question) -> some View {
        let votes = game.audiencePercentages?[index]
        let label = "\(letter(index)), " + (votes.map { "\($0) percent, " } ?? "") + question.answers[index]
        return Button { focus = nil; store.answer(index, questionID: question.id) } label: {
            HStack(alignment: .top, spacing: 10) {
                Text(letter(index)).font(.headline).foregroundStyle(Palette.gold).frame(width: answerLetterWidth)
                    .padding(.vertical, 4)
                VStack(alignment: .leading, spacing: 6) {
                    if let votes { Text("\(votes)% audience vote").font(.caption.weight(.semibold)).foregroundStyle(Palette.mint) }
                    Text(question.answers[index]).fixedSize(horizontal: false, vertical: true).font(.body.weight(.medium))
                    if let votes { ProgressView(value: Double(votes), total: 100).tint(Palette.mint).accessibilityHidden(true) }
                }.frame(maxWidth: .infinity, alignment: .leading)
            }
            .padding(12).frame(maxWidth: .infinity, minHeight: 52, alignment: .leading)
            .background(Palette.panel, in: RoundedRectangle(cornerRadius: 8))
            .overlay(RoundedRectangle(cornerRadius: 8).stroke(Palette.gold.opacity(0.72), lineWidth: 1))
            .contentShape(Rectangle())
        }
        .buttonStyle(AnswerButtonStyle()).foregroundStyle(Palette.text)
        .accessibilityElement(children: .combine)
        .accessibilityAddTraits(.isButton)
        .accessibilityLabel(label)
        .accessibilityHint("Correct answers move straight to the next question. An incorrect answer ends the game.")
        .accessibilityIdentifier("answer\(index)")
    }

    private func result(_ game: GameState, _ q: Question) -> some View {
        VStack(alignment: .leading, spacing: 16) {
            VStack(alignment: .leading, spacing: 12) {
                Label(resultTitle(game), systemImage: game.phase == .lost ? "flag.checkered" : game.phase == .walkedAway ? "checkmark.seal.fill" : "crown.fill")
                    .font(.title2.bold()).foregroundStyle(game.phase == .lost ? Palette.rose : Palette.mint)
                if game.phase != .walkedAway {
                    Text("You reached question \(game.level) of 15 and \(galleons(game.prize)). You leave with \(galleons(game.banked)).")
                        .fixedSize(horizontal: false, vertical: true)
                }
                if game.phase != .walkedAway {
                    Text("Correct answer: \(q.answers[q.correctIndex]). \(q.explanation)").fixedSize(horizontal: false, vertical: true)
                } else { Text("You leave with \(galleons(game.banked)).") }
            }
            .accessibilityElement(children: .combine)
            .accessibilityAddTraits(.isHeader)
            .accessibilityFocused($focus, equals: .result)
            .accessibilityIdentifier("gameResult")

            if game.isFinished {
                command("Main Menu", icon: "house.fill", emphasized: true) {
                    if store.returnToMenu() { lifelineResult = nil; selectedTab = .game }
                }.accessibilityIdentifier("mainMenu")
                command("Play Again", icon: "arrow.counterclockwise") { lifelineResult = nil; store.newGame() }
                Text("Highest prize reached: \(galleons(store.highScore)).")
            }
            if game.phase == .won { QuizChamberArtwork().aspectRatio(1.5, contentMode: .fit).accessibilityHidden(true) }
            PrizeTrack(completed: game.phase == .correct || game.phase == .won ? game.level : game.level - 1)
            if game.phase != .walkedAway { Text(q.source).font(.caption) }
        }
    }

    private var confirmationTitle: String {
        switch confirmation {
        case .restart: return "End this game and start again?"
        case .walkAway: return "Finish with \(galleons(store.game?.prize ?? 0))?"
        case nil: return ""
        }
    }
    private func resultTitle(_ game: GameState) -> String {
        switch game.phase {
        case .correct: return "Correct!"
        case .lost: return "Incorrect. Game over."
        case .won: return "Congratulations! One million galleons!"
        case .walkedAway: return "Prize banked"
        case .question: return ""
        }
    }
    private func letter(_ index: Int) -> String { ["A", "B", "C", "D"][index] }

    private func questionSummary(_ game: GameState, _ question: Question) -> String {
        "Question \(game.level) of 15. \(question.text)"
    }
}

private struct AnswerGlow: View {
    let outcome: AnswerOutcome?
    @Environment(\.accessibilityReduceMotion) private var reduceMotion
    @Environment(\.accessibilityDimFlashingLights) private var dimFlashingLights
    @State private var strength = 0.0
    private var colour: Color { outcome?.phase == .lost ? .red : .green }
    var body: some View {
        RoundedRectangle(cornerRadius: 18)
            .stroke(colour.opacity(strength), lineWidth: 8)
            .shadow(color: colour.opacity(strength * 0.6), radius: 18)
            .padding(4)
            .task(id: outcome?.question.id) {
                strength = 0
                guard outcome != nil, !reduceMotion, !dimFlashingLights else { return }
                // A single gentle edge pulse, never a full-screen or repeating flash.
                withAnimation(.easeOut(duration: 0.25)) { strength = 0.85 }
                try? await Task.sleep(for: .milliseconds(350))
                guard !Task.isCancelled else { return }
                withAnimation(.easeOut(duration: 0.8)) { strength = 0 }
            }
            .onChange(of: reduceMotion) { _, reduced in if reduced { strength = 0 } }
            .onChange(of: dimFlashingLights) { _, dimmed in if dimmed { strength = 0 } }
    }
}

private struct QuizChamberArtwork: View {
    var body: some View {
        GeometryReader { geometry in
            Image("QuizChamber").resizable().scaledToFill()
                .frame(width: geometry.size.width, height: geometry.size.height)
                .clipped()
        }.allowsHitTesting(false)
    }
}

private struct AnswerButtonStyle: ButtonStyle {
    func makeBody(configuration: Configuration) -> some View {
        configuration.label.opacity(configuration.isPressed ? 0.65 : 1)
    }
}

private struct PrizeTrack: View {
    let completed: Int
    var body: some View {
        HStack(alignment: .center, spacing: 4) {
            ForEach(1...15, id: \.self) { level in
                RoundedRectangle(cornerRadius: 1)
                    .fill(level <= completed ? Palette.gold : level == completed + 1 ? Palette.mint : Palette.text.opacity(0.2))
                    .frame(maxWidth: .infinity)
                    .frame(height: [5, 10, 15].contains(level) ? 10 : 5)
            }
        }.frame(height: 12).accessibilityHidden(true)
    }
}

func command(_ title: String, icon: String, emphasized: Bool = false, action: @escaping () -> Void) -> some View {
    Button(action: action) {
        Label(title, systemImage: icon).font(.body.weight(.semibold))
            .frame(maxWidth: .infinity, minHeight: 44, alignment: .leading)
            .padding(.horizontal, 12)
            #if os(iOS)
            .padding(.vertical, 5)
            #endif
            .background(emphasized ? Palette.gold : Palette.panel, in: RoundedRectangle(cornerRadius: 8))
            .contentShape(Rectangle())
    }.buttonStyle(.plain).foregroundStyle(emphasized ? Palette.background : Palette.gold)
}
