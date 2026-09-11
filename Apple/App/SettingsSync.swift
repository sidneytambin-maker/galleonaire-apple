import Foundation
import WatchConnectivity
import GalleonaireCore

@MainActor final class SettingsSync: NSObject, WCSessionDelegate {
    private var latest = GameSettings()
    private let receive: (GameSettings) -> Void
    init(receive: @escaping (GameSettings) -> Void) { self.receive = receive }
    func start(_ settings: GameSettings) {
        latest = settings
        guard WCSession.isSupported() else { return }
        WCSession.default.delegate = self
        WCSession.default.activate()
    }
    func publish(_ settings: GameSettings) {
        latest = settings
        guard WCSession.isSupported(), WCSession.default.activationState == .activated,
              let data = try? JSONEncoder().encode(settings) else { return }
        // Application context is latest-state delivery, not a reachability requirement.
        try? WCSession.default.updateApplicationContext(["galleonaire.settings.v1": data])
    }
    nonisolated func session(_ session: WCSession, activationDidCompleteWith activationState: WCSessionActivationState, error: Error?) {
        let data = session.receivedApplicationContext["galleonaire.settings.v1"] as? Data
        Task { @MainActor [weak self] in
            guard let self else { return }
            if let data { self.decode(data) }
            self.publish(self.latest)
        }
    }
    nonisolated func session(_ session: WCSession, didReceiveApplicationContext applicationContext: [String: Any]) {
        guard let data = applicationContext["galleonaire.settings.v1"] as? Data, data.count < 32768 else { return }
        Task { @MainActor [weak self] in self?.decode(data) }
    }
    private func decode(_ data: Data) {
        guard data.count < 32768, let value = try? JSONDecoder().decode(GameSettings.self, from: data), value.isValid else { return }
        receive(value)
    }
    #if os(iOS)
    nonisolated func sessionDidBecomeInactive(_ session: WCSession) {}
    nonisolated func sessionDidDeactivate(_ session: WCSession) { session.activate() }
    #endif
}
