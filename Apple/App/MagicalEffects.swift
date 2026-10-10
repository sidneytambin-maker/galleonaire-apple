import SwiftUI

/// Decorative, finite effects. These never own focus, sound, input or game timing.
enum MagicalEffect: Equatable {
    case correct, incorrect, fiftyFifty, audience, swap, victory

    var colour: Color {
        switch self {
        case .correct: return Palette.mint
        case .incorrect: return Palette.rose
        case .audience: return Color(red: 0.68, green: 0.8, blue: 1)
        default: return Palette.gold
        }
    }
    var duration: Double { self == .victory ? 5.8 : 1.8 }
}

struct MagicalEffects: View {
    let effect: MagicalEffect?
    let activation: String
    @Environment(\.accessibilityReduceMotion) private var reduceMotion
    @Environment(\.accessibilityDimFlashingLights) private var dimFlashingLights
    @Environment(\.scenePhase) private var scenePhase
    @State private var started = Date.distantPast
    @State private var running = false

    private var permitted: Bool { !reduceMotion && !dimFlashingLights && scenePhase == .active }

    var body: some View {
        TimelineView(.animation(minimumInterval: 1.0 / 30, paused: !running || !permitted)) { timeline in
            Canvas { context, size in
                guard running, permitted, let effect else { return }
                let progress = min(1, max(0, timeline.date.timeIntervalSince(started) / effect.duration))
                let fade = min(1, progress * 8) * max(0, 1 - progress)
                let centre = CGPoint(x: size.width / 2, y: size.height * 0.16)
                // Restrict particles to the margins so questions and answers remain readable.
                let count = effect == .victory ? 42 : 18
                for index in 0..<count {
                    let seed = Double(index)
                    let side = index.isMultiple(of: 2) ? 1.0 : -1.0
                    let spread = Double(index % 9) / 9
                    let x: Double
                    let y: Double
                    switch effect {
                    case .victory:
                        x = size.width / 2 + side * (size.width * 0.38 + sin(seed + progress * 5) * 18)
                        y = size.height * (0.08 + spread * 0.85) - progress * 80
                    case .fiftyFifty:
                        x = size.width / 2 + side * (18 + progress * size.width * 0.45)
                        y = size.height * (0.08 + spread * 0.18)
                    case .audience:
                        x = size.width * (0.04 + Double(index % 3) * 0.02 + (side > 0 ? 0.84 : 0))
                        y = size.height * (0.3 + spread * 0.45) - progress * 60
                    case .swap:
                        let angle = seed * 0.5 + progress * .pi * 1.5
                        x = centre.x + cos(angle) * size.width * 0.43
                        y = centre.y + sin(angle) * 32
                    case .correct, .incorrect:
                        x = side > 0 ? size.width - 12 - spread * 12 : 12 + spread * 12
                        y = size.height * (0.12 + spread * 0.75) + (effect == .incorrect ? progress * 25 : -progress * 35)
                    }
                    let radius = effect == .victory ? 2 + Double(index % 3) : 1.8
                    let point = CGPoint(x: x, y: y)
                    var star = Path()
                    star.move(to: CGPoint(x: point.x - radius * 2, y: point.y))
                    star.addLine(to: CGPoint(x: point.x + radius * 2, y: point.y))
                    star.move(to: CGPoint(x: point.x, y: point.y - radius * 2))
                    star.addLine(to: CGPoint(x: point.x, y: point.y + radius * 2))
                    context.stroke(star, with: .color(effect.colour.opacity(fade * 0.8)), lineWidth: 1.2)
                    context.fill(Path(ellipseIn: CGRect(x: x - radius / 2, y: y - radius / 2, width: radius, height: radius)), with: .color(effect.colour.opacity(fade)))
                }
                if effect == .victory || effect == .swap {
                    let radius = 22 + progress * 45
                    let ring = CGRect(x: centre.x - radius, y: centre.y - radius / 3, width: radius * 2, height: radius * 2 / 3)
                    context.stroke(Path(ellipseIn: ring), with: .color(effect.colour.opacity(fade * 0.65)), lineWidth: 1.5)
                }
            }
        }
        .allowsHitTesting(false)
        .accessibilityHidden(true)
        .task(id: activation) {
            running = false
            guard permitted, let effect, !activation.isEmpty else { return }
            started = Date()
            running = true
            defer { running = false }
            try? await Task.sleep(for: .milliseconds(Int(effect.duration * 1000)))
        }
        .onChange(of: permitted) { _, allowed in if !allowed { running = false } }
        .onDisappear { running = false }
    }
}

/// Static victory treatment is retained when the user disables animated effects.
struct VictorySeal: View {
    var body: some View {
        VStack(spacing: 12) {
            Image(systemName: "crown.fill")
                .font(.system(size: 42, weight: .medium))
                .foregroundStyle(Palette.gold)
                .padding(22)
                .background(Circle().fill(Palette.panel))
                .overlay(Circle().stroke(Palette.gold, lineWidth: 2))
                .overlay(Circle().inset(by: 6).stroke(Palette.gold.opacity(0.5), lineWidth: 1))
            Text("1,000,000").font(.system(.largeTitle, design: .serif, weight: .bold))
                .foregroundStyle(Palette.gold).minimumScaleFactor(0.7)
            Text("GALLEONS").font(.caption.weight(.semibold)).tracking(3)
        }
        .frame(maxWidth: .infinity)
        .padding(24)
        .background(LinearGradient(colors: [Palette.panel, Palette.background], startPoint: .topLeading, endPoint: .bottomTrailing), in: RoundedRectangle(cornerRadius: 18))
        .overlay(RoundedRectangle(cornerRadius: 18).stroke(Palette.gold.opacity(0.8), lineWidth: 1))
        .accessibilityHidden(true)
    }
}
