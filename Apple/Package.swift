// swift-tools-version: 5.10
import PackageDescription

let package = Package(
    name: "GalleonaireCore",
    platforms: [.iOS(.v17), .watchOS(.v10), .macOS(.v14)],
    products: [.library(name: "GalleonaireCore", targets: ["GalleonaireCore"])],
    targets: [
        .target(name: "GalleonaireCore", resources: [.process("Resources")]),
        .testTarget(name: "GalleonaireCoreTests", dependencies: ["GalleonaireCore"])
    ]
)
