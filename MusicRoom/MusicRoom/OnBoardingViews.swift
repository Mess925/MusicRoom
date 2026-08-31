//
//  OnBoardingViews.swift
//  MusicRoom
//
//  Created by Han Min Thant on 31/8/26.
//

import Foundation
import SwiftUI

struct OnBoardingViews: View {
    @Binding var appState: AppState
    
    var body: some View {
        Text("On Borading Views")
    }
}

#Preview{
    OnBoardingViews(appState: .constant(.onboarding))
}
