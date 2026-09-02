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
        NavigationStack{
            ZStack{
                CustomColors.background.edgesIgnoringSafeArea(.all)
                VStack{
                    Spacer()
                    VStack(spacing: 12) {
                        LogoView()
                        
                        Text("Music Room")
                            .font(.title3)
                            .fontWeight(.medium)
                            .foregroundStyle(CustomColors.textSecondary)
                            .tracking(2)
                        
                        Text("Vote on tracks, build playlists,\nand share control of the music.")
                            .font(.subheadline)
                            .foregroundStyle(CustomColors.textSecondary)
                            .multilineTextAlignment(.center)
                            .padding(.top, 8)
                    }
                    Spacer()
                    
                    VStack(spacing: 12) {
                        Button {
                            
                        } label: {
                            HStack {
                                Image(systemName: "apple.logo")
                                Text("Continue with Apple")
                                    .fontWeight(.medium)
                            }
                            .frame(maxWidth: .infinity)
                            .padding()
                            .background(CustomColors.textPrimary)
                            .foregroundStyle(CustomColors.background)
                            .clipShape(RoundedRectangle(cornerRadius: 12))
                        }
                        
                        Button {
                            print("Sign in with Google tapped")
                        } label: {
                            HStack {
                                Image(systemName: "globe")
                                Text("Continue with Google")
                                    .fontWeight(.medium)
                            }
                            .frame(maxWidth: .infinity)
                            .padding()
                            .background(CustomColors.backgroundSecondary)
                            .foregroundStyle(CustomColors.textPrimary)
                            .overlay(
                                RoundedRectangle(cornerRadius: 12)
                                    .stroke(CustomColors.divider, lineWidth: 5)
                            )
                            .clipShape(RoundedRectangle(cornerRadius: 12))
                        }
                        
                        HStack {
                            Rectangle()
                                .fill(CustomColors.divider)
                                .frame(height: 1)
                            Text("or")
                                .font(.footnote)
                                .foregroundStyle(CustomColors.textSecondary)
                            Rectangle()
                                .fill(CustomColors.divider)
                                .frame(height: 1)
                        }
                        .padding(.vertical, 8)
                        
                        NavigationLink {
                            SignUpView(appState: $appState)
                        } label: {
                            Text("Sign up with email")
                                .fontWeight(.medium)
                                .frame(maxWidth: .infinity)
                                .padding()
                                .background(CustomColors.accentPrimary)
                                .foregroundStyle(.white)
                                .clipShape(RoundedRectangle(cornerRadius: 12))
                        }
                        HStack (spacing: 4){
                            Text("Already have an account? ")
                                .foregroundStyle(CustomColors.textSecondary)
                            NavigationLink {
                                SignInView(appState: $appState)
                            }
                            label: {
                                Text("Sign in")
                                    .foregroundStyle(CustomColors.accentPrimary)
                                    .fontWeight(.semibold)
                                    .underline(true, pattern: .dash, color: CustomColors.accentPrimary)
                            }
                        }
                    }
                    
                    .font(.footnote)
                    .padding(.top, 4)
                }
                .padding(.horizontal, 24)
                .padding(.bottom, 32)
            }
        }
    }
}

#Preview {
    WelcomeView(appState: .constant(.welcome))
}

