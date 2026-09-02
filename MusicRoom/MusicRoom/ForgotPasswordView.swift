//
//  ForgotPasswordView.swift
//  MusicRoom
//
//  Created by Han Min Thant on 2/9/26.
//

import Foundation
import SwiftUI

struct ForgotPasswordView: View {
    @State private var email = ""
    @State private var didSubmit = false

    var body: some View {
        ZStack {
            CustomColors.background
                .ignoresSafeArea()

            VStack(alignment: .leading, spacing: 24) {
                VStack(alignment: .leading, spacing: 8) {
                    Text("Reset Password")
                        .font(.system(size: 28, weight: .bold, design: .serif))
                        .foregroundStyle(CustomColors.textPrimary)

                    Text("Enter your email and we'll send you a link to reset your password.")
                        .font(.subheadline)
                        .foregroundStyle(CustomColors.textSecondary)
                }
                .padding(.top, 24)

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

                if didSubmit {
                    Text("If an account exists for that email, a reset link is on its way.")
                        .font(.footnote)
                        .foregroundStyle(CustomColors.accentPrimary)
                }

                Button {
                    print("Reset link requested for \(email)")
                    didSubmit = true
                } label: {
                    Text("Send Reset Link")
                        .fontWeight(.medium)
                        .frame(maxWidth: .infinity)
                        .padding()
                        .background(CustomColors.accentPrimary)
                        .foregroundStyle(.white)
                        .clipShape(RoundedRectangle(cornerRadius: 12))
                }

                Spacer()
            }
            .padding(.horizontal, 24)
        }
    }
}

#Preview {
    ForgotPasswordView()
}
