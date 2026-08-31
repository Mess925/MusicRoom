//
//  WelcomeView.swift
//  MusicRoom
//
//  Created by Han Min Thant on 31/8/26.
//

import Foundation
import SwiftUI

struct WelcomeView : View {
    @Binding var appState: AppState
    var body: some View {
        /*@START_MENU_TOKEN@*//*@PLACEHOLDER=Hello, world!@*/Text("Hello, world!")/*@END_MENU_TOKEN@*/
    }
}

#Preview {
    WelcomeView(appState: .constant(.welcome))
}
