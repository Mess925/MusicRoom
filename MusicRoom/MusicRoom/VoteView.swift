//
//  VoteView.swift
//  MusicRoom
//
//  Created by Mess on 1/10/26.
//

import Foundation
import SwiftUI

enum EventFilter: String, CaseIterable, Identifiable {
    case all = "All", live = "Live", publicOnly = "Public", privateOnly = "Private", onSite = "On-site"

    var id: Self { self }

    func matches(_ event: MusicEvent) -> Bool {
        switch self {
        case .all: true
        case .live: event.isLive
        case .publicOnly: event.isPublic
        case .privateOnly: !event.isPublic
        case .onSite: event.voteRule == .onSite
        }
    }
}

struct VoteView: View {
    @State private var events = MusicEvent.samples
    @State private var searchText = ""
    @State private var filter: EventFilter = .all
    @State private var showCreate = false
    @State private var showJoin = false

    private var visibleEvents: [MusicEvent] {
        events.filter { event in
            filter.matches(event) && (searchText.isEmpty
                || event.name.localizedCaseInsensitiveContains(searchText)
                || event.ownerName.localizedCaseInsensitiveContains(searchText))
        }
    }

    private var sections: [(title: String, events: [MusicEvent])] {
        let visible = visibleEvents
        let yours = visible.filter { $0.isMine || $0.isJoined }
        let others = visible.filter { !$0.isMine && !$0.isJoined }
        return [
            ("Your Events", yours),
            ("Live Now", others.filter(\.isLive)),
            ("Coming Up", others.filter { $0.startsAt > .now }.sorted { $0.startsAt < $1.startsAt }),
            ("Earlier", others.filter(\.hasEnded)),
        ].filter { !$0.events.isEmpty }
    }

    var body: some View {
        NavigationStack {
            List {
                FilterChips(selection: $filter)
                    .listRowInsets(EdgeInsets())
                    .listRowBackground(Color.clear)
                    .listRowSeparator(.hidden)

                ForEach(sections, id: \.title) { section in
                    Section {
                        ForEach(section.events) { event in
                            EventRow(event: event)
                                .padding(.horizontal, 16)
                                .listRowBackground(
                                    RoundedRectangle(cornerRadius: 16)
                                        .fill(CustomColors.backgroundSecondary)
                                        .padding(.vertical, 4)
                                        .padding(.horizontal, 16)
                                )
                                .listRowSeparator(.hidden)
                                .swipeActions {
                                    if event.isMine {
                                        Button("Delete", systemImage: "trash", role: .destructive) {
                                            withAnimation { events.removeAll { $0.id == event.id } }
                                        }
                                    }
                                }
                        }
                    } header: {
                        SectionHeader(title: section.title, count: section.events.count,
                                      isLive: section.title == "Live Now")
                    }
                }
            }
            .listStyle(.plain)
            .scrollContentBackground(.hidden)
            .background(CustomColors.background)
            .overlay {
                if sections.isEmpty {
                    EmptyEventsView(isSearching: !searchText.isEmpty || filter != .all) {
                        showCreate = true
                    }
                }
            }
            .navigationTitle("Events")
            .searchable(text: $searchText,
                        placement: .navigationBarDrawer(displayMode: .always),
                        prompt: "Search events or hosts")
            .refreshable {
                // Placeholder until the backend exists.
                try? await Task.sleep(for: .seconds(1))
            }
            .toolbar {
                ToolbarItem(placement: .topBarLeading) {
                    Button("Join with code", systemImage: "key.fill") { showJoin = true }
                }
                ToolbarItem(placement: .topBarTrailing) {
                    Button("Create event", systemImage: "plus") { showCreate = true }
                }
            }
            .tint(CustomColors.accentPrimary)
            .sheet(isPresented: $showCreate) {
                CreateEventView { newEvent in
                    withAnimation { events.insert(newEvent, at: 0) }
                }
            }
            .sheet(isPresented: $showJoin) {
                JoinWithCodeView(events: events) { joined in
                    guard let index = events.firstIndex(where: { $0.id == joined.id }) else { return }
                    withAnimation {
                        events[index].isJoined = true
                        events[index].memberCount += 1
                    }
                }
                .presentationDetents([.medium])
            }
        }
    }
}

// MARK: - Header pieces

struct FilterChips: View {
    @Binding var selection: EventFilter

    var body: some View {
        ScrollView(.horizontal, showsIndicators: false) {
            HStack(spacing: 8) {
                ForEach(EventFilter.allCases) { filter in
                    Button {
                        withAnimation(.spring(duration: 0.25)) { selection = filter }
                    } label: {
                        Text(filter.rawValue)
                            .font(.footnote.weight(.medium))
                            .padding(.horizontal, 14)
                            .padding(.vertical, 7)
                            .background(
                                Capsule().fill(selection == filter
                                    ? CustomColors.accentPrimary
                                    : CustomColors.backgroundSecondary)
                            )
                            .foregroundStyle(selection == filter ? .white : CustomColors.textSecondary)
                    }
                    .buttonStyle(.plain)
                }
            }
            .padding(.horizontal, 16)
            .padding(.vertical, 8)
        }
    }
}

struct SectionHeader: View {
    let title: String
    let count: Int
    var isLive = false

    var body: some View {
        HStack(spacing: 6) {
            if isLive { LiveDot() }
            Text(title)
                .font(.system(.title3, design: .serif).weight(.bold))
                .foregroundStyle(CustomColors.textPrimary)
            Text("\(count)")
                .font(.caption.weight(.semibold))
                .foregroundStyle(CustomColors.textSecondary)
            Spacer()
        }
        .textCase(nil)
        .padding(.top, 8)
    }
}

struct LiveDot: View {
    @State private var pulse = false

    var body: some View {
        Circle()
            .fill(.red)
            .frame(width: 8, height: 8)
            .overlay {
                Circle()
                    .stroke(.red, lineWidth: 2)
                    .scaleEffect(pulse ? 2.2 : 1)
                    .opacity(pulse ? 0 : 0.8)
            }
            .onAppear {
                withAnimation(.easeOut(duration: 1.2).repeatForever(autoreverses: false)) {
                    pulse = true
                }
            }
    }
}

struct EmptyEventsView: View {
    let isSearching: Bool
    let onCreate: () -> Void

    var body: some View {
        VStack(spacing: 12) {
            Image(systemName: isSearching ? "magnifyingglass" : "music.note.house")
                .font(.system(size: 44))
                .foregroundStyle(CustomColors.accentPrimary)
            Text(isSearching ? "No matching events" : "No events yet")
                .font(.system(.title3, design: .serif).weight(.bold))
                .foregroundStyle(CustomColors.textPrimary)
            Text(isSearching ? "Try another search or filter." : "Start one and let the crowd pick the music.")
                .font(.subheadline)
                .foregroundStyle(CustomColors.textSecondary)
            if !isSearching {
                Button("Create Event", action: onCreate)
                    .fontWeight(.medium)
                    .padding(.horizontal, 24)
                    .padding(.vertical, 12)
                    .background(CustomColors.accentPrimary, in: RoundedRectangle(cornerRadius: 12))
                    .foregroundStyle(.white)
                    .padding(.top, 4)
            }
        }
        .multilineTextAlignment(.center)
        .padding(32)
    }
}

// MARK: - Row

struct EventLogo: View {
    let event: MusicEvent

    var body: some View {
        Group {
            if let data = event.imageData, let uiImage = UIImage(data: data) {
                Image(uiImage: uiImage)
                    .resizable()
                    .scaledToFill()
            }
            else {
                ZStack {
                    CustomColors.accentPrimary.opacity(event.isPublic ? 0.2 : 0.08)
                    Image(systemName: event.isPublic ? "music.note.house.fill" : "lock.fill")
                        .foregroundStyle(event.isPublic ? CustomColors.accentPrimary : CustomColors.textSecondary)
                }
            }
        }
        .frame(width: 48, height: 48)
        .clipShape(RoundedRectangle(cornerRadius: 12))
        .overlay(alignment: .topTrailing) {
            if event.isLive {
                LiveDot()
                    .padding(3)
                    .background(CustomColors.backgroundSecondary, in: Circle())
                    .offset(x: 5, y: -5)
            }
        }
    }
}

struct EventRow: View {
    let event: MusicEvent

    var body: some View {
        HStack(alignment: .top, spacing: 12) {
            EventLogo(event: event)

            VStack(alignment: .leading, spacing: 6) {
                HStack {
                    Text(event.name)
                        .font(.headline)
                        .foregroundStyle(CustomColors.textPrimary)
                        .lineLimit(1)
                    Spacer()
                    Badge(text: event.isPublic ? "Public" : "Private", highlighted: event.isPublic)
                }

                HStack(spacing: 4) {
                    Text(event.isMine ? "Hosted by you" : "by \(event.ownerName)")
                    if let time = event.timeLabel {
                        Text("·")
                        Text(time)
                            .foregroundStyle(event.isLive && time.hasPrefix("Ends") ? CustomColors.accentPrimary : CustomColors.textSecondary)
                    }
                }
                .font(.caption)
                .foregroundStyle(CustomColors.textSecondary)

                if event.canSeeDetails {
                    details
                } else {
                    Label("Join to see who's playing", systemImage: "eye.slash")
                        .font(.caption)
                        .foregroundStyle(CustomColors.textSecondary)
                }
            }
        }
        .padding(.vertical, 8)
        .opacity(event.hasEnded ? 0.6 : 1)
    }

    @ViewBuilder
    private var details: some View {
        if let nowPlaying = event.nowPlaying, event.isLive {
            Label(nowPlaying, systemImage: "waveform")
                .font(.subheadline.weight(.medium))
                .foregroundStyle(CustomColors.accentPrimary)
                .lineLimit(1)
                .symbolEffect(.variableColor.iterative, options: .repeating)
        }

        if let top = event.topTrack, !event.hasEnded {
            HStack(spacing: 6) {
                Text("UP NEXT")
                    .font(.caption2.weight(.bold))
                    .foregroundStyle(CustomColors.textSecondary)
                Label("\(top.votes)", systemImage: "arrowtriangle.up.fill")
                    .font(.caption.weight(.semibold))
                    .foregroundStyle(CustomColors.accentPrimary)
                Text(top.title)
                    .font(.caption)
                    .foregroundStyle(CustomColors.textPrimary)
                    .lineLimit(1)
            }
        }

        HStack(spacing: 12) {
            Label("\(event.memberCount)", systemImage: "person.3.fill")
            Label(event.locationName ?? event.voteRule.title, systemImage: event.voteRule.icon)
                .lineLimit(1)
            Spacer()
            if event.isPublic || event.isMine {
                ShareLink(
                    item: URL(string: "musicroom://room/\(event.id)")!,
                    subject: Text("Join \(event.name)"),
                    message: Text(shareMessage)
                ) {
                    Image(systemName: "square.and.arrow.up")
                        .font(.body)
                        .foregroundStyle(CustomColors.accentPrimary)
                        .frame(width: 32, height: 32)
                        .contentShape(Rectangle())
                }
                .buttonStyle(.borderless)
            }
        }
        .font(.caption)
        .foregroundStyle(CustomColors.textSecondary)
    }

    private var shareMessage: String {
        if let code = event.accessCode {
            return "Come listen with me on MusicRoom! Access code: \(code)"
        }
        return "Come listen with me on MusicRoom!"
    }
}

struct Badge: View {
    let text: String
    var highlighted = true

    var body: some View {
        Text(text)
            .font(.caption2.weight(.semibold))
            .padding(.horizontal, 8)
            .padding(.vertical, 3)
            .background(Capsule().fill(highlighted
                ? CustomColors.accentPrimary.opacity(0.2)
                : CustomColors.textSecondary.opacity(0.2)))
            .foregroundStyle(highlighted ? CustomColors.accentPrimary : CustomColors.textSecondary)
    }
}

#Preview {
    VoteView()
}
