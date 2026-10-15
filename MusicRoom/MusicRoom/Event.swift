//
//  Event.swift
//  MusicRoom
//
//  Created by Mess on 2/10/26.
//

import Foundation

enum VoteRule: String, CaseIterable, Identifiable {
    case everyone, invitedOnly, onSite

    var id: Self { self }

    var title: String {
        switch self {
        case .everyone: "Everyone"
        case .invitedOnly: "Invited only"
        case .onSite: "On-site only"
        }
    }

    var detail: String {
        switch self {
        case .everyone: "Anyone in the event can vote."
        case .invitedOnly: "Only people you invite can vote."
        case .onSite: "Only people at the location, during the time window, can vote."
        }
    }

    var icon: String {
        switch self {
        case .everyone: "globe"
        case .invitedOnly: "envelope.fill"
        case .onSite: "mappin.and.ellipse"
        }
    }
}

enum Genre: String, CaseIterable, Identifiable {
    case disco, electronic, pop, hipHop, rock, jazz, lofi

    var id: Self { self }

    var title: String {
        switch self {
        case .disco: "Disco"
        case .electronic: "Electronic"
        case .pop: "Pop"
        case .hipHop: "Hip-Hop"
        case .rock: "Rock"
        case .jazz: "Jazz"
        case .lofi: "Lo-Fi"
        }
    }
}

struct TopTrack {
    var title: String
    var votes: Int
}

struct MusicEvent: Identifiable {
    let id = UUID()
    var name: String
    var ownerName: String
    var isPublic: Bool = true
    var memberCount: Int = 0
    var nowPlaying: String? = nil
    /// Genre of the track playing right now, from the track's metadata. It changes
    /// with every song, since the crowd can vote anything in.
    var nowPlayingGenre: Genre? = nil
    var imageData: Data? = nil
    var voteRule: VoteRule = .everyone
    var topTrack: TopTrack? = nil
    var startsAt: Date = .now
    var endsAt: Date? = nil
    var locationName: String? = nil
    var isMine: Bool = false
    var isJoined: Bool = false
    var accessCode: String? = nil
    var canSeeDetails: Bool { isPublic || isMine || isJoined }

    var playingGenre: Genre? {
        isLive && canSeeDetails && nowPlaying != nil ? nowPlayingGenre : nil
    }

    var isLive: Bool {
        startsAt <= .now && (endsAt.map { $0 > .now } ?? true)
    }

    var hasEnded: Bool {
        endsAt.map { $0 <= .now } ?? false
    }
    var timeLabel: String? {
        let formatter = DateComponentsFormatter()
        formatter.unitsStyle = .abbreviated
        formatter.allowedUnits = [.day, .hour, .minute]
        formatter.maximumUnitCount = 2

        if hasEnded { return "Ended" }
        if startsAt > .now, let span = formatter.string(from: .now, to: startsAt) {
            return "Starts in \(span)"
        }
        if let endsAt, let span = formatter.string(from: .now, to: endsAt) {
            return "Ends in \(span)"
        }
        return nil
    }
}


// Mock datas
extension MusicEvent {
    static let samples: [MusicEvent] = {
        let hour: TimeInterval = 3600
        return [
            MusicEvent(name: "Friday Night", ownerName: "DJ Soda", memberCount: 200,
                       nowPlaying: "Blinding Lights", nowPlayingGenre: .disco, topTrack: TopTrack(title: "Levitating", votes: 34),
                       startsAt: .now - hour, endsAt: .now + 2 * hour),
            MusicEvent(name: "Orange House", ownerName: "Lawrance", isPublic: false, memberCount: 8,
                       nowPlaying: "Mr Brightside", nowPlayingGenre: .rock, voteRule: .invitedOnly,
                       startsAt: .now - 2 * hour, accessCode: "K7Q2M9"),
            MusicEvent(name: "Rooftop Sunset Set", ownerName: "Mess", memberCount: 42,
                       nowPlaying: "Sunflower", nowPlayingGenre: .hipHop, voteRule: .onSite,
                       topTrack: TopTrack(title: "Golden Hour", votes: 12),
                       startsAt: .now - 0.5 * hour, endsAt: .now + 1.5 * hour,
                       locationName: "Marina Rooftop", isMine: true),
            MusicEvent(name: "Study Lo-Fi", ownerName: "Mess", memberCount: 5,
                       topTrack: TopTrack(title: "Snowman", votes: 3),
                       startsAt: .now + 3 * hour, endsAt: .now + 6 * hour, isMine: true),
            MusicEvent(name: "42 Campus Party", ownerName: "BDE 42", memberCount: 128,
                       nowPlaying: "Titanium", nowPlayingGenre: .electronic, voteRule: .onSite,
                       topTrack: TopTrack(title: "One More Time", votes: 57),
                       startsAt: .now - 3 * hour, endsAt: .now + 0.75 * hour, locationName: "42 Cluster"),
            MusicEvent(name: "Throwback Thursday", ownerName: "Nina", memberCount: 76,
                       nowPlaying: "Smells Like Teen Spirit", nowPlayingGenre: .rock,
                       topTrack: TopTrack(title: "Wonderwall", votes: 21),
                       startsAt: .now - hour),
            MusicEvent(name: "Gym Hype", ownerName: "Coach K", memberCount: 19,
                       topTrack: TopTrack(title: "Till I Collapse", votes: 9),
                       startsAt: .now + 20 * hour, endsAt: .now + 22 * hour),
            MusicEvent(name: "Wedding Reception", ownerName: "Aye & Min", isPublic: false, memberCount: 150,
                       voteRule: .invitedOnly, startsAt: .now + 30 * hour, accessCode: "WD8H3P"),
            MusicEvent(name: "Jazz Brunch", ownerName: "Blue Note", memberCount: 33,
                       nowPlaying: "So What", nowPlayingGenre: .jazz,
                       startsAt: .now - 0.5 * hour, endsAt: .now + 2 * hour),
        ]
    }()
}
