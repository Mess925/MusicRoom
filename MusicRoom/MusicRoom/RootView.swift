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
    
    var body: some View {
        switch appState {
        case .splash:
            SplashView(appState: $appState)
        case .onboarding:
            OnBoardingViews(appState: $appState)
//        case .welcome:
//            
//        case .home:
//            <#code#>
        }
    }
}
