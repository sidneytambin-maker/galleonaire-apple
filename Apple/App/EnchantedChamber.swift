import SwiftUI
import GalleonaireCore

/// Original celestial-library dressing. No timers, hit targets or accessibility children.
struct EnchantedChamber: View {
    var level = 1
    @Environment(\.accessibilityReduceMotion) private var reduceMotion
    @Environment(\.accessibilityDimFlashingLights) private var dimFlashingLights
    @Environment(\.scenePhase) private var scenePhase
    private var energy: Double { Double(max(1, min(15, level))) / 15 }
    var body: some View {
        GeometryReader { proxy in
            ZStack {
                Image("QuizChamber").resizable().scaledToFill()
                    .frame(width: proxy.size.width, height: proxy.size.height).clipped()
                LinearGradient(colors: [.black.opacity(0.25 * (1 - energy)), .clear, Palette.background.opacity(0.2)], startPoint: .top, endPoint: .bottom)
                RadialGradient(colors: [Palette.mint.opacity(energy * 0.22), .clear], center: .center, startRadius: 2, endRadius: proxy.size.width * 0.45)
                Canvas { context, size in
                    let count = 3 + min(15, max(1, level))
                    for index in 0..<count {
                        let x = size.width * (0.18 + Double((index * 37) % 67) / 100)
                        let y = size.height * (0.12 + Double((index * 23) % 72) / 100)
                        let radius = index.isMultiple(of: 3) ? 2.2 : 1.2
                        let dot = CGRect(x: x, y: y, width: radius * 2, height: radius * 2)
                        context.fill(Path(ellipseIn: dot), with: .color(Palette.gold.opacity(0.45 + energy * 0.4)))
                    }
                }
            }
            .animation(reduceMotion || dimFlashingLights || scenePhase != .active ? nil : .easeInOut(duration: 0.8), value: level)
        }
        .clipShape(RoundedRectangle(cornerRadius: 16))
        .overlay(RoundedRectangle(cornerRadius: 16).stroke(Palette.gold.opacity(0.3 + energy * 0.45), lineWidth: level == 15 ? 2 : 1))
        .allowsHitTesting(false).accessibilityHidden(true)
    }
}

struct ArtefactSeal: View {
    let lifeline: Lifeline
    let used: Bool
    private var symbol: String {
        switch lifeline { case .fiftyFifty: return "circle.lefthalf.filled"; case .audience: return "person.3.fill"; case .freePass: return "arrow.triangle.2.circlepath" }
    }
    var body: some View {
        ZStack {
            Circle().fill(LinearGradient(colors: [Palette.panel, Palette.background], startPoint: .topLeading, endPoint: .bottomTrailing))
            Circle().stroke(used ? Palette.text.opacity(0.4) : Palette.gold, lineWidth: 2)
            Circle().inset(by: 5).stroke(Palette.gold.opacity(used ? 0.15 : 0.45), lineWidth: 1)
            Image(systemName: used ? "checkmark" : symbol).font(.title3.weight(.semibold))
                .foregroundStyle(used ? Palette.text : Palette.gold)
        }.frame(width: 48, height: 48).accessibilityHidden(true)
    }
}

struct MagicalPressStyle: ButtonStyle {
    @Environment(\.accessibilityReduceMotion) private var reduceMotion
    func makeBody(configuration: Configuration) -> some View {
        configuration.label
            .overlay(RoundedRectangle(cornerRadius: 12).stroke(configuration.isPressed ? Palette.mint : .clear, lineWidth: 3))
            .brightness(configuration.isPressed ? 0.08 : 0)
            .animation(reduceMotion ? nil : .easeOut(duration: 0.12), value: configuration.isPressed)
    }
}
