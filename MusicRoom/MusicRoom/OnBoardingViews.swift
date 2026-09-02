//
//  OnBoardingViews.swift
//  MusicRoom
//
//  Created by Han Min Thant on 31/8/26.
//

import Foundation
import SwiftUI

struct OnBoardingPage {
    let title: String
    let descripton: String
}

struct OnBoardingPageView: View {
    let page: OnBoardingPage
    
    var body: some View {
        VStack(alignment: .leading, spacing: 16) {
            Spacer()
            
            Text (page.title)
                .font(.system(size: 32, weight: .bold, design: .serif))
                .foregroundStyle(CustomColors.accentPrimary)
            Text(page.descripton)
                .font(.body)
                .foregroundStyle(CustomColors.textSecondary)
                .lineSpacing(4)
            Spacer()
            Spacer()
        }
        .padding(.horizontal, 32)
        .frame(maxWidth: .infinity, alignment: .leading)
    }
}

//#Preview {OnBoardingPageView(page: OnBoardingPage(title: "hello", descripton: "StringStringStringStringStringStringStringStringStringStringStringStringStringStringStringStringStringStringStringStringStringStringStringStringStringStringStringStringStringStringStringStringString"))}

struct OnBoardingViews: View {
    @Binding var appState: AppState
    @Binding var alreadyInstalled: Bool
    
    @State private var currentPage: Int = 0
    
    private let pages: [OnBoardingPage] = [
        OnBoardingPage(title:"Welcome to Music Room" , descripton: "Your music, your crowd. Vote, collaborate, and control the playlist together — wherever you are."),
        OnBoardingPage(title:"Vote for What Plays Next" , descripton: "At a party or event, suggest a track or vote up your favorites. The more votes a song gets, the sooner it plays."),
        OnBoardingPage(title:"Build Playlist Together" , descripton: "Collaborate with friends in real time to create shared playlists — like your own radio station, curated as a group."),
        OnBoardingPage(title:"Hand Off the Aux" , descripton: "Delegate music control to a friend from any of your devices, and take it back whenever you want."),
        OnBoardingPage(title:"Make It Yours" , descripton: "Set your music taste, choose what's public or private, and decide who can join in. Ready to get started?")
    ]
    
    var body: some View {
        ZStack {
            CustomColors.background
                .ignoresSafeArea()
            VStack(spacing: 0){
                HStack(spacing: 4){
                    ForEach(pages.indices, id: \.self) { page in
                        Capsule()
                            .fill(page <= currentPage ? CustomColors.accentPrimary: CustomColors.divider)
                            .frame(height: 3)
                    }
                }
                .padding(.horizontal, 32)
                .padding(.top, 16)
                
                OnBoardingPageView(page: pages[currentPage])
                    .id(currentPage)
                
                Button {
                    if currentPage < pages.count - 1 {
                        withAnimation{
                            currentPage += 1
                        }
                    }
                    else {
                        finishOnboarding()
                    }
                }
                label: {
                    Text(currentPage < pages.count - 1 ? "Next" : "Get Started")
                        .fontWeight(.medium)
                        .frame(maxWidth: .infinity)
                        .padding()
                        .background(CustomColors.accentPrimary)
                        .foregroundStyle(.white)
                        .clipShape(RoundedRectangle(cornerRadius: 12))
                }
                .padding(.horizontal, 32)
                
                if currentPage < pages.count - 1 {
                    Button {
                        finishOnboarding()
                    }
                    label: {
                        Text ("Skip")
                            .font(.footnote)
                            .foregroundStyle(CustomColors.textSecondary)
                    }
                    .padding(.top, 12)
                }
                else {
                    Color.clear.frame(height: 12).padding(.top, 12)
                }
            }
            .padding(.bottom, 32)

        }
    }
    private func finishOnboarding() {
        alreadyInstalled = true
        appState = .welcome
    }
}

//#Preview{
//    OnBoardingViews(appState: .constant(.onboarding), alreadyInstalled: .constant(false))
//}

#Preview{
    RootView()
}
