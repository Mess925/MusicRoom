//
//  VoteView.swift
//  MusicRoom
//
//  Created by Mess on 1/10/26.
//

import Foundation
import SwiftUI

struct VoteView: View {
        let events =  [ MusicEvent(name: "Friday Night", ownerName: "DJ Soda",
                              memberCount: 200, nowPlaying: "Blinding Lights"),
                        MusicEvent(name: "Orange House", ownerName: "Lawrance", isPublic: false, memberCount: 8, nowPlaying: "Mr Brightside")]
        
        var body: some View {
            NavigationStack {
                List(events) { event in
                    EventRow(event: event)
                        .padding(.horizontal, 12)
                        .listRowBackground(
                            RoundedRectangle(cornerRadius: 16)
                                .fill(CustomColors.backgroundSecondary)
                                .padding(.vertical, 4)
                        )
                        .listRowSeparator(.hidden)
                }
                .scrollContentBackground(.hidden)
//                .navigationTitle("Rooms")
            }
        }
    }

struct EventLogo: View {
    let event: MusicEvent
    
    var body: some View {
        Group {
            if let data = event.imageData, let uiImage = UIImage(data: data) {
                Image(uiImage: uiImage)
                    .resizable()
                    .scaledToFit()
            }
            else{
                ZStack {
                    CustomColors.accentPrimary.opacity(event.isPublic ? 0.2 : 0.08)
                    Image(systemName: event.isPublic ? "music.note.house.fill" : "lock.fill")
                        .foregroundStyle(event.isPublic ? CustomColors.accentPrimary : CustomColors.textSecondary)
                    
                }
            }
        }
        .frame(width: 48, height: 48)
        .clipShape(RoundedRectangle(cornerRadius: 12))
    }
}

struct EventRow: View {
    let event: MusicEvent

    var body: some View {
        HStack(spacing: 12) {
        EventLogo(event: event)

            VStack(alignment: .leading, spacing: 6) {
                HStack {
                    Text(event.name)
                        .font(.headline)
                        .foregroundStyle(CustomColors.textPrimary)
                    Spacer()
                    Text(event.isPublic ? "Public" : "Private")
                        .font(.caption2.weight(.semibold))
                        .padding(.horizontal, 8)
                        .padding(.vertical, 3)
                        .background(
                            Capsule().fill(event.isPublic
                                ? CustomColors.accentPrimary.opacity(0.2)
                                : CustomColors.textSecondary.opacity(0.2))
                        )
                        .foregroundStyle(event.isPublic
                            ? CustomColors.accentPrimary
                            : CustomColors.textSecondary)
                }

                if event.isPublic {
                    Text("by \(event.ownerName)")
                        .font(.caption)
                        .foregroundStyle(CustomColors.textSecondary)

                    HStack(spacing: 12) {
                        Label("\(event.memberCount)", systemImage: "person.3.fill")
                            .foregroundStyle(CustomColors.textSecondary)
                        Label(event.nowPlaying ?? "Nothing playing", systemImage: "music.note")
                            .foregroundStyle(CustomColors.accentPrimary)
                            .lineLimit(1)
                        Spacer()
                        ShareLink(
                            item: URL(string: "musicroom://room/\(event.id)")!,
                            subject: Text("Join \(event.name)"),
                            message: Text("Come listen with me on MusicRoom!")
                        ) {
                            Image(systemName: "square.and.arrow.up")
                                .font(.title3)
                                .foregroundStyle(CustomColors.accentPrimary)
                                .frame(width: 36, height: 36)
                                .contentShape(Rectangle())
                        }
                        .buttonStyle(.borderless)
                    }
                    .font(.caption)
                } else {
                    Label("Join to see who's playing", systemImage: "eye.slash")
                        .font(.caption)
                        .foregroundStyle(CustomColors.textSecondary)
                }
            }
        }
        .padding(.vertical, 6)
    }
}
#Preview{
    VoteView()
}
