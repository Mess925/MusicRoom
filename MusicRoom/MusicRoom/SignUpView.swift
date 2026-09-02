//
//  SignUpView.swift
//  MusicRoom
//
//  Created by Han Min Thant on 2/9/26.
//


import Foundation
import SwiftUI

struct SignUpView: View {
    @Binding var appState: AppState

    @State private var email = ""
    @State private var password = ""
    @State private var confirmPassword = ""

    var body: some View {
        ZStack {
                CustomColors.background
                    .ignoresSafeArea()
                
                ScrollView {
                    VStack(alignment: .leading, spacing: 24) {
                        VStack(alignment: .leading, spacing: 8) {
                            Text("Create Account")
                                .font(.system(size: 28, weight: .bold, design: .serif))
                                .foregroundStyle(CustomColors.textPrimary)
                            
                            Text("Start tracking what you read, today.")
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
                                
                                SecureField("Create a password", text: $password)
                                    .padding()
                                    .background(CustomColors.backgroundSecondary)
                                    .clipShape(RoundedRectangle(cornerRadius: 12))
                            }
                            
                            VStack(alignment: .leading, spacing: 6) {
                                Text("Confirm Password")
                                    .font(.footnote)
                                    .foregroundStyle(CustomColors.textSecondary)
                                
                                SecureField("Re-enter your password", text: $confirmPassword)
                                    .padding()
                                    .background(CustomColors.backgroundSecondary)
                                    .clipShape(RoundedRectangle(cornerRadius: 12))
                            }
                        }
                        
                        Button {
                            // Stub — swap for a real Supabase sign-up call, then
                            // only transition to .home once it succeeds.
                            // Deferred to the next run loop tick — same reason
                            // as SignInView's Sign In button.
                            DispatchQueue.main.async {
                                appState = .home
                            }
                        } label: {
                            Text("Create Account")
                                .fontWeight(.medium)
                                .frame(maxWidth: .infinity)
                                .padding()
                                .background(CustomColors.accentPrimary)
                                .foregroundStyle(.white)
                                .clipShape(RoundedRectangle(cornerRadius: 12))
                        }
                        
                        HStack(spacing: 4) {
                            Text("Already have an account?")
                                .foregroundStyle(CustomColors.textSecondary)
                            NavigationLink{
                                SignInView(appState: $appState)
                            } label: {
                                Text("Sign in")
                                    .foregroundStyle(CustomColors.accentPrimary)
                                    .fontWeight(.semibold)
                                    .underline(true, pattern: .dash, color: CustomColors.accentPrimary)
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
    SignUpView(appState: .constant(.welcome))
}
