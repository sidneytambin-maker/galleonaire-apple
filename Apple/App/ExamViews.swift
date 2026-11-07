import SwiftUI
import Combine
import GalleonaireCore

private enum ExamRoute: Hashable {
    case subjects(ExamQualification)
    case briefing(ExamSubject, ExamQualification)
}

struct ExamModeView: View {
    @EnvironmentObject private var exams: ExamStore
    @Environment(\.dismiss) private var dismiss
    @State private var paperOpen = false
    @State private var path: [ExamRoute] = []
    var resume = false
    var body: some View {
        NavigationStack(path: $path) {
            Group {
                if let id = exams.resultID, let result = exams.results.first(where: { $0.id == id }) {
                    ExamResultView(result: result) { exams.resultID = nil; paperOpen = false }
                } else if paperOpen, exams.active != nil {
                    ExamPaperView()
                } else {
                    ExamQualificationView { openPaper() }
                }
            }
            .navigationDestination(for: ExamRoute.self) { route in
                switch route {
                case .subjects(let qualification): ExamSubjectView(qualification: qualification)
                case .briefing(let subject, let qualification):
                    ExamBriefingView(subject: subject, qualification: qualification) { openPaper() }
                }
            }
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    #if os(watchOS)
                    Button { dismiss() } label: { Image(systemName: "xmark").accessibilityHidden(true) }
                        .tint(Palette.panel).foregroundStyle(Palette.text)
                        .accessibilityElement(children: .ignore).accessibilityLabel("Save and Close")
                        .accessibilityIdentifier("closeExam")
                    #else
                    Button("Save and Close") { dismiss() }.accessibilityIdentifier("closeExam")
                    #endif
                }
            }
        }
        .tint(Palette.gold).preferredColorScheme(.dark)
        .onAppear { exams.checkDeadline(); paperOpen = resume && exams.active != nil }
        .onChange(of: exams.resultID) { _, id in if id != nil { path = [] } }
        .alert("Exam Not Saved", isPresented: Binding(get: { exams.errorMessage != nil }, set: { if !$0 { exams.errorMessage = nil } })) {
            Button("OK") { exams.errorMessage = nil }
        } message: { Text(exams.errorMessage ?? "") }
    }
    private func openPaper() { path = []; paperOpen = true }
}

private struct ExamQualificationView: View {
    @EnvironmentObject private var exams: ExamStore
    @AccessibilityFocusState private var heading: Bool
    let begin: () -> Void
    var body: some View {
        List {
            Text("Choose a qualification").font(.headline).accessibilityAddTraits(.isHeader).accessibilityFocused($heading)
            if let a = exams.active {
                Button("Resume Exam: \(a.subject.name), \(a.qualification.name), question \(a.currentIndex + 1) of \(a.questions.count)", action: begin)
                    .accessibilityIdentifier("resumeExam")
                Text("Finish your saved paper before starting another exam.")
            } else {
                ForEach(ExamQualification.allCases) { q in
                    NavigationLink(value: ExamRoute.subjects(q)) {
                        VStack(alignment: .leading, spacing: 6) {
                            Text(q.name).font(.headline)
                            Text(q == .owl ? "20 intermediate questions. Untimed." : "50 expert questions. Choose standard, extended or untimed.").font(.subheadline)
                        }.fixedSize(horizontal: false, vertical: true)
                    }.accessibilityIdentifier("qualification-\(q.rawValue)")
                }
            }
        }.examStyle().navigationTitle("Exam Mode").onAppear { heading = true }
    }
}

private struct ExamSubjectView: View {
    let qualification: ExamQualification
    @AccessibilityFocusState private var heading: Bool
    var body: some View {
        List {
            Text("Choose a subject for \(qualification.name)").font(.headline).accessibilityAddTraits(.isHeader).accessibilityFocused($heading)
            ForEach(ExamSubject.allCases) { subject in
                NavigationLink(subject.name, value: ExamRoute.briefing(subject, qualification))
                    .accessibilityIdentifier("subject-\(subject.rawValue)")
            }
        }.examStyle().navigationTitle("Subject").onAppear { heading = true }
    }
}

private struct ExamBriefingView: View {
    @EnvironmentObject private var exams: ExamStore
    let subject: ExamSubject
    let qualification: ExamQualification
    let begin: () -> Void
    @State private var timing = ExamTiming.standard
    @AccessibilityFocusState private var heading: Bool
    var body: some View {
        List {
            Text("\(subject.name). \(qualification.name). Exam briefing.").font(.headline)
                .accessibilityAddTraits(.isHeader).accessibilityFocused($heading)
            Text("Series-wide spoilers: both qualifications cover the full Harry Potter universe, including later books and films.")
            Text("\(qualification.count) questions. You can skip, revisit and change any answer before submitting. Each answer is saved immediately. Marks and explanations appear only after submission.")
            if qualification == .newt {
                Picker("Timing", selection: $timing) {
                    ForEach(ExamTiming.allCases) { option in Text(option.name).tag(option) }
                }.accessibilityIdentifier("examTiming")
                Text("The timer starts when you activate Begin Exam. Time continues while the app is closed or your Watch sleeps. At the deadline, your saved answers are submitted automatically. Unanswered questions receive zero marks.")
            } else {
                Text("This paper is untimed. You can close the app and resume later.")
            }
            Text("The pass mark is 60 percent. The same grade boundaries apply to every timing option.")
            Button("Begin Exam") {
                if exams.begin(subject: subject, qualification: qualification, timing: qualification == .owl ? .untimed : timing) { begin() }
            }.accessibilityIdentifier("beginExam").disabled(exams.engine == nil || exams.bank == nil)
        }.examStyle().navigationTitle("Briefing").onAppear { heading = true }
    }
}

struct ExamPaperView: View {
    @EnvironmentObject private var exams: ExamStore
    @Environment(\.scenePhase) private var phase
    @AccessibilityFocusState private var questionFocus: String?
    @State private var confirmSubmit = false
    @State private var showQuestions = false
    @State private var time = Date()
    private let ticker = Timer.publish(every: 5, on: .main, in: .common).autoconnect()
    var body: some View {
        Group {
            if let a = exams.active {
                let q = a.questions[a.currentIndex]
                ScrollViewReader { scroll in
                    List {
                        Text("Question \(a.currentIndex + 1) of \(a.questions.count). \(q.item.question.text)")
                            .font(.headline).fixedSize(horizontal: false, vertical: true)
                            .accessibilityAddTraits(.isHeader).accessibilityFocused($questionFocus, equals: q.id)
                            .accessibilityIdentifier("examQuestion").id(q.id)
                        ForEach(0..<4, id: \.self) { index in
                            Button { exams.answer(index, questionID: q.id, attemptID: a.id) } label: {
                                VStack(alignment: .leading, spacing: 4) {
                                    Text(q.item.question.answers[q.answerOrder[index]])
                                    if q.answer == index { Text("Recorded answer").font(.caption) }
                                }.fixedSize(horizontal: false, vertical: true)
                            }
                            .accessibilityLabel(q.item.question.answers[q.answerOrder[index]])
                            .accessibilityValue(q.answer == index ? "Recorded answer" : "")
                            .accessibilityAddTraits(q.answer == index ? .isSelected : [])
                            .accessibilityIdentifier("examAnswer\(index)")
                        }
                        if q.answer != nil { Button("Clear Answer") { exams.answer(nil, questionID: q.id, attemptID: a.id) } }
                        if a.currentIndex > 0 { Button("Previous Question") { exams.navigate(a.currentIndex - 1) } }
                        if a.currentIndex + 1 < a.questions.count {
                            Button(q.answer == nil ? "Skip Question" : "Next Question") { exams.navigate(a.currentIndex + 1) }
                                .accessibilityIdentifier("examNext")
                        }
                        Button("Review Questions: \(a.questions.count - a.unanswered) of \(a.questions.count) answered") { showQuestions = true }
                            .accessibilityIdentifier("examNavigator")
                        Button { time = exams.now(); exams.checkDeadline(); AccessibilityNotification.Announcement(remaining(a)).post() } label: {
                            Text(remaining(a))
                        }.accessibilityIdentifier("examTimeRemaining")
                        Button("Submit Exam") { exams.checkDeadline(); if exams.active != nil { confirmSubmit = true } }
                            .accessibilityIdentifier("submitExam")
                    }.examStyle()
                    .task(id: q.id) {
                        questionFocus = nil; await Task.yield()
                        guard !Task.isCancelled else { return }
                        scroll.scrollTo(q.id, anchor: .top); questionFocus = q.id
                    }
                }
                .navigationTitle(a.qualification.name)
                .alert("Submit this exam?", isPresented: $confirmSubmit) {
                    Button("Submit Saved Answers") { exams.submit(a.id) }
                    Button("Return to Paper", role: .cancel) { questionFocus = q.id }
                } message: { Text("\(a.unanswered) of \(a.questions.count) questions are unanswered. Unanswered questions receive zero marks. Answers cannot be changed after submission.") }
                .sheet(isPresented: $showQuestions, onDismiss: {
                    if let current = exams.active { questionFocus = current.questions[current.currentIndex].id }
                }) {
                    SheetContent(title: "Review Questions") {
                        ForEach(Array(a.questions.enumerated()), id: \.element.id) { index, item in
                            Button("Question \(index + 1). \(item.answer == nil ? "Unanswered" : "Answered")") {
                                exams.navigate(index); showQuestions = false
                            }.accessibilityIdentifier("examJump\(index)")
                        }
                    }
                }
            }
        }
        .onReceive(ticker) { _ in time = exams.now(); if phase == .active { exams.checkDeadline(announce: true) } }
        .onChange(of: phase) { _, value in if value == .active { time = exams.now(); exams.checkDeadline(announce: true) } }
        .onAppear { time = exams.now(); exams.checkDeadline(announce: true) }
        .onChange(of: exams.resultID) { _, value in if value != nil { showQuestions = false; confirmSubmit = false } }
    }
    private func remaining(_ a: ExamAttempt) -> String {
        guard let interval = a.remaining(at: time) else { return "Time remaining: untimed" }
        let seconds = Int(ceil(interval))
        return "Time remaining: \(seconds / 60) minutes, \(seconds % 60) seconds"
    }
}

struct ExamResultView: View {
    let result: ExamAttempt
    var onFinish: (() -> Void)? = nil
    @AccessibilityFocusState private var heading: Bool
    var body: some View {
        List {
            VStack(alignment: .leading, spacing: 10) {
                Text(result.subject.name).font(.headline)
                Text(result.qualification.name)
                Text(result.grade.rawValue).font(.title2.bold()).foregroundStyle(Palette.gold)
                Text("\(result.score) out of \(result.qualification.count) · \(result.percentage)%")
                Text(result.grade.passed ? "Pass" : "Fail").font(.headline)
            }.fixedSize(horizontal: false, vertical: true)
                .accessibilityElement(children: .ignore).accessibilityLabel(result.summary)
                .accessibilityAddTraits(.isHeader).accessibilityFocused($heading).accessibilityIdentifier("examResult")
            if result.expired { Text("Time expired. Your saved answers were submitted automatically.") }
            Text("\(result.unanswered) unanswered. \(result.timing.name).")
            NavigationLink("Review Answers and Explanations") { ExamAnswerReviewView(result: result) }
                .accessibilityIdentifier("examAnswerReview")
            if let onFinish { Button("Choose Another Exam", action: onFinish).accessibilityIdentifier("anotherExam") }
            Text("Result reference: \(result.id.uuidString)").font(.caption)
        }.examStyle().navigationTitle("Exam Result").onAppear { heading = true }
    }
}

private struct ExamAnswerReviewView: View {
    let result: ExamAttempt
    @AccessibilityFocusState private var heading: Bool
    var body: some View {
        List {
            Text("Answer review. \(result.subject.name), \(result.qualification.name)")
                .font(.headline).accessibilityAddTraits(.isHeader).accessibilityFocused($heading)
            ForEach(Array(result.questions.enumerated()), id: \.element.id) { index, paper in
                let q = paper.item.question
                Section("Question \(index + 1)") {
                    Text(q.text).font(.headline)
                    Text(paper.answer.map { "Your answer: \(q.answers[paper.answerOrder[$0]])" } ?? "Unanswered")
                    Text(paper.correct ? "Correct. 1 mark." : "0 marks.")
                    Text("Correct answer: \(q.answers[q.correctIndex])")
                    Text(q.explanation)
                    if let address = q.sourceURL, let url = URL(string: address) {
                        Link("Source: \(q.source)", destination: url).font(.caption)
                    } else { Text(q.source).font(.caption) }
                }
            }
        }.examStyle().navigationTitle("Answer Review").onAppear { heading = true }
    }
}

extension View {
    func examStyle() -> some View {
        self.scrollContentBackground(.hidden).background(Palette.background)
            .foregroundStyle(Palette.text).tint(Palette.gold)
    }
}
