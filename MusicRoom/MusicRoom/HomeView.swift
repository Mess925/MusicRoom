//
//  HomeView.swift
//  MusicRoom
//
//  Created by Han Min Thant on 2/9/26.
//

import Foundation
import SwiftUI

struct HomeView : View {
    @Binding var appState: AppState
    var body: some View {
        MiniTabBarView()
    }
}
