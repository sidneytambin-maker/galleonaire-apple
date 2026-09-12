import SwiftUI

enum AppTab: String, CaseIterable, Identifiable {
    case game, rules, settings
    var id: String { rawValue }
    var title: String {
        switch self { case .game: return "Game"; case .rules: return "How to play"; case .settings: return "Settings" }
    }
    var icon: String {
        switch self { case .game: return "sparkles"; case .rules: return "book"; case .settings: return "gearshape" }
    }
}

struct AppRootView: View {
    @EnvironmentObject private var store: GameStore
    @Environment(\.scenePhase) private var scenePhase
    @State private var selected = AppTab.game

    var body: some View {
        Group {
            #if os(iOS)
            TabView(selection: $selected) {
                ForEach(AppTab.allCases) { tab in
                    page(tab)
                        .tabItem { Label(tab.title, systemImage: tab.icon) }
                        .tag(tab)
                }
            }
            #else
            page(selected)
                .safeAreaInset(edge: .bottom, spacing: 0) {
                    HStack(spacing: 0) {
                        ForEach(AppTab.allCases) { tab in
                            Button { selected = tab } label: {
                                Image(systemName: tab.icon)
                                    .font(.body.weight(.semibold))
                                    .frame(maxWidth: .infinity, minHeight: 44)
                                    .background(selected == tab ? Palette.gold.opacity(0.18) : Color.clear)
                                    .contentShape(Rectangle())
                            }
                            .buttonStyle(.plain)
                            .accessibilityLabel(tab.title)
                            .accessibilityValue("Tab \(AppTab.allCases.firstIndex(of: tab)! + 1) of 3")
                            .accessibilityAddTraits(selected == tab ? [.isSelected] : [])
                            .accessibilityIdentifier("tab-\(tab.rawValue)")
                            .help(tab.title)
                        }
                    }
                    .background(Palette.background)
                    .overlay(alignment: .top) { Rectangle().fill(Palette.gold.opacity(0.35)).frame(height: 1) }
                    .accessibilityIdentifier("tabBar")
                }
            #endif
        }
        .tint(Palette.gold)
        .preferredColorScheme(.dark)
        .onAppear { store.feedback.setActive(scenePhase == .active) }
        .onChange(of: scenePhase) { _, phase in store.feedback.setActive(phase == .active) }
    }

    @ViewBuilder private func page(_ tab: AppTab) -> some View {
        switch tab {
        case .game: GameView(selectedTab: $selected)
        case .rules: RulesView()
        case .settings: SettingsView()
        }
    }
}
