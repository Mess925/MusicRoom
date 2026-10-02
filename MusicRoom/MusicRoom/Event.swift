//
//  Event.swift
//  MusicRoom
//
//  Created by Mess on 2/10/26.
//

import Foundation

struct Event: Identifiable {
    let id = UUID()
    var name: String
    var ownerName: String
    var isPublic: Bool = true
    var memberCount: Int = 0
    var nowPlaying: String? = nil
}
