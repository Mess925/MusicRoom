//
//  RootView.swift
//  MusicRoom
//
//  Created by Han Min Thant on 31/8/26.
//

import Foundation
import SwiftUI

struct RootView: View {
    @State private var appState: AppState = .splash
    @AppStorage("alreadyInstalled")  var alreadyInstalled: Bool = false
    
    var body: some View {
        switch appState {
        case .splash:
            SplashView(appState: $appState, alreadyInstalled: alreadyInstalled)
        case .onboarding:
            OnBoardingViews(appState: $appState, alreadyInstalled: $alreadyInstalled)
        case .welcome:
            WelcomeView(appState: $appState)
        case .home:
            HomeView(appState: $appState)
        }
    }
}
