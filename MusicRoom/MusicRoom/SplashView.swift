//
//  SplashView.swift
//  MusicRoom
//
//  Created by Han Min Thant on 31/8/26.
//

import Foundation
import SwiftUI

struct LogoView: View {
    var body: some View {
        Image(systemName: "beats.headphones")
            .font(.system(size: 60, weight: .bold, design: .serif))
            .foregroundStyle(CustomColors.accentPrimary)
            .italic()
    }
}

struct SplashView: View {
    @Binding var appState: AppState
    let alreadyInstalled: Bool

    @State private var rotationAngle: Double = 0

    var body: some View {
        ZStack {
            CustomColors.background
                .ignoresSafeArea()

                LogoView()
                    .rotation3DEffect(
                        .degrees(rotationAngle),
                        axis: (x: 0, y: 1, z: 0),
                        perspective: 0.5
                    )
        }
        .onAppear {
            withAnimation(.linear(duration: 3.0)) {
                rotationAngle = 360
            }

            DispatchQueue.main.asyncAfter(deadline: .now() + 3.0) {
                appState = alreadyInstalled ? .welcome : .onboarding
            }
        }
    }
}

#Preview {
    RootView()
}
