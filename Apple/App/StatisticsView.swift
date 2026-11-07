import SwiftUI
import GalleonaireCore

struct StatisticsView: View {
    @EnvironmentObject private var store: GameStore
    @EnvironmentObject private var exams: ExamStore
    private var stats: GameStatistics { store.engine?.archive.statistics ?? GameStatistics() }
    @AccessibilityFocusState private var heading: Bool
    var body: some View {
        NavigationStack {
            List {
                Text("Statistics").font(.title2.bold()).foregroundStyle(Palette.gold)
                    .accessibilityAddTraits(.isHeader).accessibilityIdentifier("tabHeading").accessibilityFocused($heading)
                Section("Classic record") {
                    classicAccuracy
                    summary("Games and wins", "\(stats.gamesStarted) started. \(stats.gamesFinished) finished. \(stats.gamesWon) won.")
                    summary("Prizes", "Highest prize reached: \(galleons(store.highScore)). Highest prize banked: \(galleons(stats.bestBanked)).")
                    summary("Answer streaks", "Current: \(stats.currentStreak). Best: \(stats.bestStreak).")
                    NavigationLink("Classic Details: Lifelines and Prize Levels") {
                        TabContent(title: "Classic Details") {
                            Text("Records begin with the statistics update; earlier games are not guessed. Highest prize reached retains your older record. A prize is banked when you win, lose or walk away. Closed and restarted games are not finished. Streaks continue across games and end with an incorrect answer.")
                            Section("Lifelines") {
                                summary("Total used", "\(stats.lifelinesUsed)")
                                ForEach(Lifeline.allCases) { line in summary(line.name, "\(stats.lifelines[line.rawValue, default: 0])") }
                            }
                            Section("Prize levels") {
                                ForEach(1...15, id: \.self) { level in
                                    accuracy("Level \(level), \(galleons(QuestionBank.prizeLadder[level - 1]))", record: stats.levels[level, default: AnswerRecord()])
                                }
                            }
                        }
                    }
                }.listRowBackground(Palette.panel)
                Section("Topic performance") {
                    let topics = TopicPerformance.grouped(stats.categories)
                    ForEach(ExamSubject.allCases) { subject in
                        accuracy(subject.name, record: topics.subjects[subject, default: AnswerRecord()])
                    }
                    if !topics.earlier.isEmpty {
                        NavigationLink {
                            TabContent(title: "Earlier Topic Records") {
                                Text("These older topic labels cannot be assigned reliably to one reviewed subject. Every answer remains included in your overall Classic accuracy.")
                                ForEach(topics.earlier.keys.sorted(), id: \.self) { key in
                                    accuracy(key, record: topics.earlier[key]!).accessibilityIdentifier("earlierTopic-\(key)")
                                }
                            }
                        } label: {
                            let total = topics.earlier.values.reduce(into: AnswerRecord()) { $0.answered += $1.answered; $0.correct += $1.correct }
                            accuracy("Earlier topic records", record: total)
                        }.accessibilityIdentifier("earlierTopics")
                    }
                }.listRowBackground(Palette.panel)
                Section("Exam results") {
                    Text("Best results on this device. Exam marks are separate from Classic records.").font(.caption)
                    ForEach(ExamSubject.allCases) { subject in
                        NavigationLink {
                            ExamAttemptsView(subject: subject)
                        } label: {
                            VStack(alignment: .leading, spacing: 6) {
                                Text(subject.name).font(.headline)
                                ForEach(ExamQualification.allCases) { q in
                                    if let best = exams.engine?.archive.best(subject: subject, qualification: q) {
                                        Text("\(q.name): \(best.grade.rawValue), \(best.score) out of \(q.count)")
                                    } else { Text("\(q.name): no completed exams") }
                                }
                            }.padding(.vertical, 6).fixedSize(horizontal: false, vertical: true)
                        }.accessibilityHint("Opens individual attempts").accessibilityIdentifier("examResults-\(subject.rawValue)")
                            .accessibilityElement(children: .ignore).accessibilityLabel(bestSummary(subject))
                    }
                }.listRowBackground(Palette.panel)
            }.examStyle().onAppear { heading = true }
        }
    }
    private var classicAccuracy: some View {
        VStack(alignment: .leading, spacing: 10) {
            Text("Answer accuracy").font(.headline)
            Text(stats.answers.answered == 0 ? "Your record starts here" : "\(stats.answers.accuracy)%")
                .font(.largeTitle.bold()).foregroundStyle(Palette.gold)
                .fixedSize(horizontal: false, vertical: true)
            Text(stats.answers.answered == 0 ? "Play Classic to build your record." : "\(stats.answers.correct.formatted()) correct · \(stats.answers.answered.formatted()) answered")
                .font(.subheadline).fixedSize(horizontal: false, vertical: true)
        }.padding(.vertical, 12).accessibilityElement(children: .ignore)
            .accessibilityLabel(stats.answers.answered == 0 ? "Answer accuracy. No answers recorded yet. Play Classic to build your record." : "Answer accuracy. \(stats.answers.accuracy) percent. \(stats.answers.correct) correct out of \(stats.answers.answered) answered.")
            .accessibilityIdentifier("answerAccuracy")
    }
    private func bestSummary(_ subject: ExamSubject) -> String {
        subject.name + ". " + ExamQualification.allCases.map { qualification in
            guard let best = exams.engine?.archive.best(subject: subject, qualification: qualification) else {
                return "\(qualification.name): no completed exams."
            }
            return "\(qualification.name): \(best.grade.rawValue), \(best.score) out of \(qualification.count)."
        }.joined(separator: " ")
    }
    private func summary(_ name: String, _ value: String) -> some View {
        VStack(alignment: .leading, spacing: 6) {
            Text(name).font(.headline).foregroundStyle(Palette.gold)
            Text(value).font(.subheadline).fixedSize(horizontal: false, vertical: true)
        }.padding(.vertical, 4).accessibilityElement(children: .ignore).accessibilityLabel("\(name). \(value)")
    }
    private func accuracy(_ name: String, record: AnswerRecord) -> some View {
        VStack(alignment: .leading, spacing: 6) {
            Text(name).font(.headline)
            Text(record.answered == 0 ? "No answers recorded yet" : "\(record.accuracy)% · \(record.correct) of \(record.answered) correct")
                .font(.subheadline).fixedSize(horizontal: false, vertical: true)
            if record.answered > 0 {
                ProgressView(value: Double(record.correct), total: Double(record.answered))
                    .tint(Palette.gold).accessibilityHidden(true)
            }
        }.padding(.vertical, 6)
            .accessibilityElement(children: .ignore)
            .accessibilityLabel(record.answered == 0 ? "\(name). No answers recorded yet." : "\(name). \(record.accuracy) percent. \(record.correct) correct out of \(record.answered) answered.")
    }
}

private struct ExamAttemptsView: View {
    @EnvironmentObject private var exams: ExamStore
    let subject: ExamSubject
    @AccessibilityFocusState private var heading: Bool
    var body: some View {
        List {
            Text(subject.name).font(.headline).accessibilityAddTraits(.isHeader).accessibilityFocused($heading)
            ForEach(ExamQualification.allCases) { qualification in
                Section(qualification.name) {
                    let attempts = exams.results.filter { $0.subject == subject && $0.qualification == qualification }
                        .sorted { ($0.submittedAt ?? $0.startedAt) > ($1.submittedAt ?? $1.startedAt) }
                    if attempts.isEmpty { Text("No completed exams") }
                    ForEach(attempts) { result in
                        NavigationLink { ExamResultView(result: result) } label: {
                            VStack(alignment: .leading, spacing: 6) {
                                Text("\(result.grade.rawValue). \(result.score) out of \(qualification.count). \(result.grade.passed ? "Pass" : "Fail").")
                                Text(result.submittedAt ?? result.startedAt, format: .dateTime.day().month().year().hour().minute())
                                Text(result.timing.name).font(.caption)
                            }.fixedSize(horizontal: false, vertical: true).accessibilityElement(children: .combine)
                        }
                    }
                }
            }
        }.examStyle().navigationTitle("Exam Attempts").onAppear { heading = true }
    }
}
