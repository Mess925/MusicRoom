//
//  SplashView.swift
//  MusicRoom
//
//  Created by Han Min Thant on 31/8/26.
//

import Foundation
import SwiftUI

struct SplashView: View {
    @Binding var appState: AppState
    
    var body: some View {
        Text("Splash Screen")
    }
}

#Preview {
    SplashView(appState: .constant(.splash))
}
