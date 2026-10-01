//
//  MiniTabBarView.swift
//  MusicRoom
//
//  Created by Mess on 1/10/26.
//

import Foundation
import SwiftUI


enum MusicTab: CaseIterable {
    case vote, control, playlist, profile

    var title: String {
        switch self {
        case .vote: "Vote"
        case .control: "Control"
        case .playlist: "Playlist"
        case .profile: "Profile"
        }
    }

    var icon: String {
        switch self {
        case .vote: "music.note"
        case .control: "slider.horizontal.3"
        case .playlist: "music.note.list"
        case .profile: "person"
        }
    }
}

struct MiniTabBarView: View {
    @State private var selectedTab: MusicTab = .vote

    var body: some View {
        Group {
            switch selectedTab {
            case .vote: VoteView()
            case .control: ControlView()
            case .playlist: PlaylistView()
            case .profile: ProfileView()
            }
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
        .background(CustomColors.background.ignoresSafeArea())
        .safeAreaInset(edge: .bottom) {
            LiquidGlassTabBar(selectedTab: $selectedTab)
                .padding(.horizontal, 12)
                .padding(.bottom, 10)
        }
        .ignoresSafeArea(.keyboard)
    }
}

struct LiquidGlassTabBar: View {
    @Binding var selectedTab: MusicTab
    @Namespace private var ns

    var body: some View {
        HStack(spacing: 0) {
            ForEach(MusicTab.allCases, id: \.self) { tab in
                Button {
                    withAnimation(.spring(duration: 0.3)) {
                        selectedTab = tab
                    }
                } label: {
                    VStack(spacing: 4) {
                        Image(systemName: tab.icon)
                            .font(.system(size: 20, weight: .medium))
                            .frame(width: 24, height: 20)
                        Text(tab.title)
                            .font(.caption2.weight(.medium))
                    }
                    .foregroundStyle(
                        selectedTab == tab
                        ? CustomColors.accentPrimary
                        : CustomColors.textSecondary
                    )
                    .frame(maxWidth: .infinity)
                    .padding(.vertical, 8)
                    .background {
                        if selectedTab == tab {
                            Capsule()
                                .fill(CustomColors.accentPrimary.opacity(0.18))
                                .matchedGeometryEffect(id: "pill", in: ns)
                        }
                    }
                    .contentShape(Capsule())
                }
                .buttonStyle(.plain)
            }
        }
        .padding(8)
        .background(CustomColors.backgroundSecondary, in: Capsule())
        .overlay {
            Capsule()
                .stroke(CustomColors.divider, lineWidth: 1)
        }
        .shadow(color: .black.opacity(0.15), radius: 20, y: 10)
    }
}

#Preview {
    MiniTabBarView()
}
