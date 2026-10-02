//
//  VoteView.swift
//  MusicRoom
//
//  Created by Mess on 1/10/26.
//

import Foundation
import SwiftUI

struct VoteView: View {
        let events =  [ Event(name: "Friday Night", ownerName: "DJ Soda",
                              memberCount: 200, nowPlaying: "Blinding Lights"),
                        Event(name: "Orange House", ownerName: "Lawrance", isPublic: false, memberCount: 8, nowPlaying: "Mr Brightside")]
        
        var body: some View {
            NavigationStack {
                List(events) { event in
                    HStack {
                        VStack(alignment: .leading, spacing: 4) {
                            Text(event.name)
                                .foregroundStyle(CustomColors.textPrimary)
                            Text("by \(event.ownerName)")
                                .font(.caption)
                                .foregroundStyle(CustomColors.textSecondary)
                            Label("\(event.memberCount)", systemImage: "person.3.fill")
                                .font(.caption)
                                .foregroundStyle(CustomColors.textSecondary)
                            if let song = event.nowPlaying {
                                Label(song, systemImage: "music.note")
                                    .font(.caption)
                                    .foregroundStyle(CustomColors.accentPrimary)
                            }
                        }
                        Spacer()
                        Image(systemName: event.isPublic ? "globe" : "lock.fill")
                            .foregroundStyle(CustomColors.textSecondary)
                    }
                    .listRowBackground(CustomColors.backgroundSecondary)
                }
                .scrollContentBackground(.hidden)
            }
        }
    }

#Preview{
    VoteView()
}
