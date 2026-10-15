//
//  CreateEventView.swift
//  MusicRoom
//
//  Created by Mess on 13/10/26.
//

import Foundation
import PhotosUI
import SwiftUI

struct CreateEventView: View {
    let onCreate: (MusicEvent) -> Void

    @Environment(\.dismiss) private var dismiss

    @State private var name = ""
    @State private var isPublic = true
    @State private var voteRule: VoteRule = .everyone
    @State private var startsNow = true
    @State private var startsAt = Date.now
    @State private var hasEnd = false
    @State private var endsAt = Date.now.addingTimeInterval(2 * 3600)
    @State private var locationName = ""
    @State private var playlistLink = ""
    @State private var photoItem: PhotosPickerItem?
    @State private var imageData: Data?
    @State private var createdPrivateEvent: MusicEvent?

    private var trimmedName: String { name.trimmingCharacters(in: .whitespaces) }

    private var canCreate: Bool {
        !trimmedName.isEmpty && (voteRule != .onSite || !locationName.trimmingCharacters(in: .whitespaces).isEmpty)
    }

    var body: some View {
        NavigationStack {
            Group {
                if let event = createdPrivateEvent {
                    AccessCodeView(event: event) { dismiss() }
                } else {
                    form
                }
            }
            .background(CustomColors.background.ignoresSafeArea())
            .navigationTitle(createdPrivateEvent == nil ? "New Event" : "")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                if createdPrivateEvent == nil {
                    ToolbarItem(placement: .cancellationAction) {
                        Button("Cancel") { dismiss() }
                    }
                }
            }
            .tint(CustomColors.accentPrimary)
        }
    }

    private var form: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 24) {
                HStack(spacing: 16) {
                    coverPicker
                    FormField(title: "Event name") {
                        TextField("Friday Night", text: $name)
                            .styledInput()
                    }
                }

                FormField(title: "Visibility") {
                    Picker("Visibility", selection: $isPublic) {
                        Text("Public").tag(true)
                        Text("Private").tag(false)
                    }
                    .pickerStyle(.segmented)
                    Text(isPublic
                         ? "Anyone can find and join this event."
                         : "Hidden from search. People join with an access code.")
                        .font(.caption)
                        .foregroundStyle(CustomColors.textSecondary)
                }

                FormField(title: "Who can vote") {
                    VStack(spacing: 8) {
                        ForEach(VoteRule.allCases) { rule in
                            VoteRuleCard(rule: rule, isSelected: voteRule == rule) {
                                withAnimation(.spring(duration: 0.25)) { voteRule = rule }
                            }
                        }
                    }
                }

                if voteRule == .onSite {
                    FormField(title: "Location") {
                        HStack {
                            Image(systemName: "mappin.and.ellipse")
                                .foregroundStyle(CustomColors.accentPrimary)
                            TextField("Where is it happening?", text: $locationName)
                        }
                        .styledInput()
                    }
                    .transition(.opacity.combined(with: .move(edge: .top)))
                }

                FormField(title: "When") {
                    VStack(spacing: 0) {
                        Toggle("Start now", isOn: $startsNow.animation())
                            .padding()
                        if !startsNow {
                            Divider().padding(.leading)
                            DatePicker("Starts", selection: $startsAt, in: Date.now...)
                                .padding()
                        }
                        Divider().padding(.leading)
                        Toggle(voteRule == .onSite ? "Voting window ends" : "Set an end time",
                               isOn: $hasEnd.animation())
                            .padding()
                        if hasEnd {
                            Divider().padding(.leading)
                            DatePicker("Ends", selection: $endsAt,
                                       in: (startsNow ? Date.now : startsAt)...)
                                .padding()
                        }
                    }
                    .foregroundStyle(CustomColors.textPrimary)
                    .background(CustomColors.backgroundSecondary)
                    .clipShape(RoundedRectangle(cornerRadius: 12))
                }

                Button(action: create) {
                    Text("Create Event")
                        .fontWeight(.medium)
                        .frame(maxWidth: .infinity)
                        .padding()
                        .background(CustomColors.accentPrimary.opacity(canCreate ? 1 : 0.4))
                        .foregroundStyle(.white)
                        .clipShape(RoundedRectangle(cornerRadius: 12))
                }
                .disabled(!canCreate)
            }
            .padding(24)
        }
        .scrollDismissesKeyboard(.interactively)
        .onChange(of: photoItem) {
            Task { imageData = try? await photoItem?.loadTransferable(type: Data.self) }
        }
    }

    private var coverPicker: some View {
        PhotosPicker(selection: $photoItem, matching: .images) {
            ZStack {
                if let imageData, let uiImage = UIImage(data: imageData) {
                    Image(uiImage: uiImage)
                        .resizable()
                        .scaledToFill()
                } else {
                    CustomColors.accentPrimary.opacity(0.15)
                    Image(systemName: "photo.badge.plus")
                        .font(.title2)
                        .foregroundStyle(CustomColors.accentPrimary)
                }
            }
            .frame(width: 72, height: 72)
            .clipShape(RoundedRectangle(cornerRadius: 16))
        }
        .padding(.top, 22)
    }

    private func create() {
        // Mock: the real flow is POST /rooms/public or /rooms/private, and the
        // access code comes back from the backend.
        let event = MusicEvent(
            name: trimmedName,
            ownerName: "You",
            isPublic: isPublic,
            memberCount: 1,
            imageData: imageData,
            voteRule: voteRule,
            startsAt: startsNow ? .now : startsAt,
            endsAt: hasEnd ? endsAt : nil,
            locationName: voteRule == .onSite ? locationName.trimmingCharacters(in: .whitespaces) : nil,
            isMine: true,
            accessCode: isPublic ? nil : Self.generateAccessCode()
        )
        onCreate(event)

        if isPublic {
            dismiss()
        } else {
            withAnimation { createdPrivateEvent = event }
        }
    }

    /// Same alphabet as the backend's `generate_access_code` (no 0/O/1/I/L).
    private static func generateAccessCode() -> String {
        let alphabet = Array("ABCDEFGHJKMNPQRSTUVWXYZ23456789")
        return String((0..<6).map { _ in alphabet.randomElement()! })
    }
}

// MARK: - Pieces

private struct FormField<Content: View>: View {
    let title: String
    @ViewBuilder let content: Content

    var body: some View {
        VStack(alignment: .leading, spacing: 6) {
            Text(title)
                .font(.footnote)
                .foregroundStyle(CustomColors.textSecondary)
            content
        }
    }
}

private struct VoteRuleCard: View {
    let rule: VoteRule
    let isSelected: Bool
    let action: () -> Void

    var body: some View {
        Button(action: action) {
            HStack(spacing: 12) {
                Image(systemName: rule.icon)
                    .font(.body.weight(.medium))
                    .frame(width: 32, height: 32)
                    .background(CustomColors.accentPrimary.opacity(isSelected ? 0.2 : 0.08), in: Circle())
                    .foregroundStyle(isSelected ? CustomColors.accentPrimary : CustomColors.textSecondary)
                VStack(alignment: .leading, spacing: 2) {
                    Text(rule.title)
                        .font(.subheadline.weight(.semibold))
                        .foregroundStyle(CustomColors.textPrimary)
                    Text(rule.detail)
                        .font(.caption)
                        .foregroundStyle(CustomColors.textSecondary)
                        .multilineTextAlignment(.leading)
                }
                Spacer()
                Image(systemName: isSelected ? "checkmark.circle.fill" : "circle")
                    .foregroundStyle(isSelected ? CustomColors.accentPrimary : CustomColors.divider)
            }
            .padding(12)
            .background(CustomColors.backgroundSecondary)
            .clipShape(RoundedRectangle(cornerRadius: 12))
            .overlay {
                RoundedRectangle(cornerRadius: 12)
                    .stroke(isSelected ? CustomColors.accentPrimary : .clear, lineWidth: 1.5)
            }
        }
        .buttonStyle(.plain)
    }
}

/// Shown once after creating a private event — the only time the code is visible.
private struct AccessCodeView: View {
    let event: MusicEvent
    let onDone: () -> Void

    @State private var copied = false

    var body: some View {
        VStack(spacing: 20) {
            Spacer()
            Image(systemName: "lock.open.fill")
                .font(.system(size: 44))
                .foregroundStyle(CustomColors.accentPrimary)
            Text("\(event.name) is ready")
                .font(.system(size: 26, weight: .bold, design: .serif))
                .foregroundStyle(CustomColors.textPrimary)
                .multilineTextAlignment(.center)
            Text("Share this code with your guests. You won't be able to see it again.")
                .font(.subheadline)
                .foregroundStyle(CustomColors.textSecondary)
                .multilineTextAlignment(.center)

            Text(event.accessCode ?? "")
                .font(.system(size: 40, weight: .bold, design: .monospaced))
                .tracking(8)
                .foregroundStyle(CustomColors.textPrimary)
                .padding(.vertical, 16)
                .padding(.horizontal, 24)
                .background(CustomColors.backgroundSecondary, in: RoundedRectangle(cornerRadius: 16))

            HStack(spacing: 12) {
                Button {
                    UIPasteboard.general.string = event.accessCode
                    withAnimation { copied = true }
                } label: {
                    Label(copied ? "Copied" : "Copy", systemImage: copied ? "checkmark" : "doc.on.doc")
                        .frame(maxWidth: .infinity)
                        .padding()
                        .background(CustomColors.backgroundSecondary, in: RoundedRectangle(cornerRadius: 12))
                }
                ShareLink(item: "Join \(event.name) on MusicRoom with code \(event.accessCode ?? "")") {
                    Label("Share", systemImage: "square.and.arrow.up")
                        .frame(maxWidth: .infinity)
                        .padding()
                        .background(CustomColors.backgroundSecondary, in: RoundedRectangle(cornerRadius: 12))
                }
            }
            .fontWeight(.medium)
            .foregroundStyle(CustomColors.accentPrimary)

            Spacer()
            Button(action: onDone) {
                Text("Done")
                    .fontWeight(.medium)
                    .frame(maxWidth: .infinity)
                    .padding()
                    .background(CustomColors.accentPrimary)
                    .foregroundStyle(.white)
                    .clipShape(RoundedRectangle(cornerRadius: 12))
            }
        }
        .padding(24)
    }
}

private extension View {
    func styledInput() -> some View {
        padding()
            .background(CustomColors.backgroundSecondary)
            .clipShape(RoundedRectangle(cornerRadius: 12))
    }
}

#Preview {
    CreateEventView { _ in }
}
