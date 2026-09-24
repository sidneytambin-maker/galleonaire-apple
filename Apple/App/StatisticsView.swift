import SwiftUI
import GalleonaireCore

struct StatisticsView: View {
    @EnvironmentObject private var store: GameStore
    private var stats: GameStatistics { store.engine?.archive.statistics ?? GameStatistics() }
    var body: some View {
        TabContent(title: "Statistics") {
            Section("Your quiz record") {
                Text("Recorded on this device since the statistics update. Earlier games are not included. Highest prize retains your existing record.").font(.caption)
                accuracy("Answer accuracy", record: stats.answers)
                    .accessibilityIdentifier("answerAccuracy")
                record("Games started", stats.gamesStarted)
                record("Games finished", stats.gamesFinished)
                Text("Finished games include wins, incorrect answers and walking away. Restarted or closed games are not finished.").font(.caption)
                record("Games won", stats.gamesWon)
                record("Questions answered", stats.answers.answered)
                record("Correct answers", stats.answers.correct)
                record("Incorrect answers", stats.answers.answered - stats.answers.correct)
            }
            Section("Personal bests") {
                Text("Highest prize reached: \(galleons(store.highScore))")
                Text("Best prize kept since this update: \(galleons(stats.bestBanked))")
                record("Highest question reached since this update", stats.highestLevel)
                record("Current correct-answer streak", stats.currentStreak)
                record("Best correct-answer streak", stats.bestStreak)
                Text("Streaks continue across games and end with an incorrect answer.").font(.caption)
            }
            Section("Lifelines") {
                record("Total lifelines used", stats.lifelinesUsed)
                ForEach(Lifeline.allCases) { line in record(line.name, stats.lifelines[line.rawValue, default: 0]) }
            }
            Section("By prize level") {
                if stats.levels.isEmpty { Text("Answer a question to begin your record.") }
                ForEach(stats.levels.keys.sorted(), id: \.self) { level in
                    accuracy("Question level \(level)", record: stats.levels[level]!)
                }
            }
            Section("By topic") {
                ForEach(stats.categories.keys.sorted(), id: \.self) { category in
                    accuracy(category, record: stats.categories[category]!)
                }
            }
        }
    }
    private func record(_ name: String, _ value: Int) -> some View {
        VStack(alignment: .leading, spacing: 4) {
            Text(name).font(.subheadline)
            Text(value.formatted()).font(.title3.bold()).foregroundStyle(Palette.gold)
        }.accessibilityElement(children: .ignore).accessibilityLabel("\(name). \(value).")
    }
    private func accuracy(_ name: String, record: AnswerRecord) -> some View {
        VStack(alignment: .leading, spacing: 8) {
            Text(name).font(.headline)
            Text(record.answered == 0 ? "No answers recorded yet" : "\(record.accuracy)% · \(record.correct) of \(record.answered) correct")
                .font(.subheadline).fixedSize(horizontal: false, vertical: true)
            ProgressView(value: Double(record.correct), total: Double(max(1, record.answered)))
                .tint(Palette.mint).accessibilityHidden(true)
        }.padding(.vertical, 6)
            .accessibilityElement(children: .ignore)
            .accessibilityLabel(record.answered == 0 ? "\(name). No answers recorded yet." : "\(name). \(record.accuracy) percent. \(record.correct) correct out of \(record.answered) answered.")
    }
}
