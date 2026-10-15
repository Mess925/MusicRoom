//
//  JoinWithCodeView.swift
//  MusicRoom
//
//  Created by Mess on 13/10/26.
//

import Foundation
import SwiftUI

struct JoinWithCodeView: View {
    let events: [MusicEvent]
    let onJoin: (MusicEvent) -> Void

    @Environment(\.dismiss) private var dismiss
    @FocusState private var focused: Bool

    @State private var code = ""
    @State private var error: String?
    @State private var shake = 0

    private static let length = 6
    private static let alphabet = Set("ABCDEFGHJKMNPQRSTUVWXYZ23456789")

    var body: some View {
        VStack(spacing: 20) {
            VStack(spacing: 8) {
                Text("Join a Private Event")
                    .font(.system(size: 24, weight: .bold, design: .serif))
                    .foregroundStyle(CustomColors.textPrimary)
                Text("Enter the 6-character code the host shared with you.")
                    .font(.subheadline)
                    .foregroundStyle(CustomColors.textSecondary)
                    .multilineTextAlignment(.center)
            }
            .padding(.top, 32)

            ZStack {
                TextField("", text: $code)
                    .focused($focused)
                    .textInputAutocapitalization(.characters)
                    .autocorrectionDisabled()
                    .keyboardType(.asciiCapable)
                    .opacity(0.01)
                    .onChange(of: code) { _, newValue in
                        let cleaned = String(newValue.uppercased().filter { Self.alphabet.contains($0) }
                            .prefix(Self.length))
                        if cleaned != newValue { code = cleaned }
                        error = nil
                        if cleaned.count == Self.length { join() }
                    }

                HStack(spacing: 8) {
                    ForEach(0..<Self.length, id: \.self) { index in
                        CodeBox(character: character(at: index),
                                isActive: focused && index == min(code.count, Self.length - 1),
                                isError: error != nil)
                    }
                }
                .modifier(Shake(trigger: shake))
                .onTapGesture { focused = true }
            }

            Text(error ?? " ")
                .font(.footnote)
                .foregroundStyle(.red)

            Spacer()
        }
        .padding(.horizontal, 24)
        .frame(maxWidth: .infinity)
        .background(CustomColors.background.ignoresSafeArea())
        .onAppear { focused = true }
    }

    private func character(at index: Int) -> String {
        guard index < code.count else { return "" }
        return String(code[code.index(code.startIndex, offsetBy: index)])
    }

    private func join() {
        // Mock: the real flow is POST /rooms/{id}/join with the access code.
        if let event = events.first(where: { $0.accessCode == code }) {
            onJoin(event)
            dismiss()
        } else {
            error = "No event found with that code."
            withAnimation(.default) { shake += 1 }
        }
    }
}

private struct CodeBox: View {
    let character: String
    let isActive: Bool
    let isError: Bool

    var body: some View {
        Text(character)
            .font(.system(size: 26, weight: .bold, design: .monospaced))
            .foregroundStyle(CustomColors.textPrimary)
            .frame(width: 46, height: 58)
            .background(CustomColors.backgroundSecondary, in: RoundedRectangle(cornerRadius: 12))
            .overlay {
                RoundedRectangle(cornerRadius: 12)
                    .stroke(isError ? .red : (isActive ? CustomColors.accentPrimary : CustomColors.divider),
                            lineWidth: isActive || isError ? 2 : 1)
            }
    }
}

private struct Shake: GeometryEffect {
    var trigger: Int
    var animatableData: CGFloat

    init(trigger: Int) {
        self.trigger = trigger
        animatableData = CGFloat(trigger)
    }

    func effectValue(size: CGSize) -> ProjectionTransform {
        ProjectionTransform(CGAffineTransform(translationX: 8 * sin(animatableData * .pi * 4), y: 0))
    }
}

#Preview {
    JoinWithCodeView(events: MusicEvent.samples) { _ in }
}
