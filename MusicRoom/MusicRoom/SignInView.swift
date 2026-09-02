//
//  SignInView.swift
//  MusicRoom
//
//  Created by Han Min Thant on 2/9/26.
//


import Foundation
import SwiftUI

struct SignInView: View {
    @Binding var appState: AppState
    @State private var email = ""
    @State private var password = ""

    var body: some View {
        ZStack {
                CustomColors.background
                    .ignoresSafeArea()
                
                ScrollView {
                    VStack(alignment: .leading, spacing: 24) {
                        VStack(alignment: .leading, spacing: 8) {
                            Text("Welcome Back")
                                .font(.system(size: 28, weight: .bold, design: .serif))
                                .foregroundStyle(CustomColors.textPrimary)
                            
                            Text("Sign in to continue tracking your reads.")
                                .font(.subheadline)
                                .foregroundStyle(CustomColors.textSecondary)
                        }
                        .padding(.top, 24)
                        
                        VStack(spacing: 16) {
                            VStack(alignment: .leading, spacing: 6) {
                                Text("Email")
                                    .font(.footnote)
                                    .foregroundStyle(CustomColors.textSecondary)
                                
                                TextField("you@example.com", text: $email)
                                    .textInputAutocapitalization(.never)
                                    .keyboardType(.emailAddress)
                                    .autocorrectionDisabled()
                                    .padding()
                                    .background(CustomColors.backgroundSecondary)
                                    .clipShape(RoundedRectangle(cornerRadius: 12))
                            }
                            
                            VStack(alignment: .leading, spacing: 6) {
                                Text("Password")
                                    .font(.footnote)
                                    .foregroundStyle(CustomColors.textSecondary)
                                
                                SecureField("Enter your password", text: $password)
                                    .padding()
                                    .background(CustomColors.backgroundSecondary)
                                    .clipShape(RoundedRectangle(cornerRadius: 12))
                            }
                            
                            HStack {
                                Spacer()
                                NavigationLink {
                                    ForgotPasswordView()
                                }
                                label: {
                                    Text("Forgot password?")
                                        .font(.footnote)
                                        .foregroundStyle(CustomColors.accentPrimary)
                                        .underline(true, pattern: .dash, color: CustomColors.accentPrimary)
                                }
                            }
                        }
                        
                        Button {
                            // Stub — swap for a real Supabase auth call, then
                            // only transition to .home once it succeeds.
                            // Deferred to the next run loop tick — setting appState
                            // directly here tears down WelcomeView's NavigationStack
                            // (which this view is currently pushed onto) mid-tap,
                            // which crashes.
                            DispatchQueue.main.async {
                                appState = .home
                            }
                        } label: {
                            Text("Sign In")
                                .fontWeight(.medium)
                                .frame(maxWidth: .infinity)
                                .padding()
                                .background(CustomColors.accentPrimary)
                                .foregroundStyle(.white)
                                .clipShape(RoundedRectangle(cornerRadius: 12))
                        }
                        
                        HStack(spacing: 4) {
                            Text("Don't have an account?")
                                .foregroundStyle(CustomColors.textSecondary)
                            NavigationLink {
                                SignUpView(appState: $appState)
                            } label: {
                                Text("Sign up")
                                    .foregroundStyle(CustomColors.accentPrimary)
                                    .fontWeight(.semibold)
                            }
                        }
                        .font(.footnote)
                        .frame(maxWidth: .infinity)
                    }
                    .padding(.horizontal, 24)
                }
            }
    }
}

#Preview {
    SignInView(appState: .constant(.welcome))
}
