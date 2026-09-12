import SwiftUI

@main struct GalleonaireApp: App {
    @StateObject private var store = GameStore()
    var body: some Scene { WindowGroup { AppRootView().environmentObject(store) } }
}
