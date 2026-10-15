//
//  Theme.swift
//  MusicRoom
//
//  Created by Han Min Thant on 31/8/26.
//

import Foundation
import SwiftUI
import UIKit

extension Color {
    init(light: Color, dark: Color) {
        self.init(UIColor {
            traitCollection in traitCollection.userInterfaceStyle == .dark ? UIColor(dark) : UIColor (light)
        })
    }
    
    init (hex: String){
        let scanner = Scanner(string: hex)
        var rgb: UInt64 = 0
        scanner.scanHexInt64(&rgb)
        
        let r = Double((rgb >> 16) & 0xFF) / 255
        let g = Double((rgb >> 8) & 0xFF) / 255
        let b = Double(rgb & 0xFF) / 255
        
        self.init(red: r, green: g, blue: b)
        
    }
    init(light: String, dark: String) {
        self.init(light: Color(hex: light), dark: Color(hex: dark))
    }
}


enum CustomColors {
    static let background = Color(
        light: Color(hex: "FFFFFF"),
        dark: Color(hex: "121212")
    )

    static let backgroundSecondary = Color(
        light: Color(hex: "F5F3EF"),
        dark: Color(hex: "1E1E1E")
    )

    static let accentPrimary = Color(
        light: Color(hex: "D97D54"),
        dark: Color(hex: "E8A87C")
    )

    static let textPrimary = Color(
        light: Color(hex: "1A1A1A"),
        dark: Color(hex: "F2F2F2")
    )

    static let textSecondary = Color(
        light: Color(hex: "6B6B6B"),
        dark: Color(hex: "A0A0A0")
    )

    static let divider = Color(
        light: Color(hex: "E0DDD6"),
        dark: Color(hex: "2C2C2C")
    )
}

// MARK: - Genre moods

struct GenreMood {
    let gradient: [Color]
    /// Text and icons tinted with the mood, readable in light and dark mode.
    let accent: Color
}

extension Genre {
    var mood: GenreMood {
        switch self {
        case .disco:
            GenreMood(gradient: [Color(hex: "FF2BD6"), Color(hex: "00E5FF")],
                      accent: Color(light: "C2189B", dark: "FF4FD8"))
        case .electronic:
            GenreMood(gradient: [Color(hex: "7B2FFF"), Color(hex: "00B3FF")],
                      accent: Color(light: "6A2BE0", dark: "A57CFF"))
        case .pop:
            GenreMood(gradient: [Color(hex: "FF5E9C"), Color(hex: "FFB86B")],
                      accent: Color(light: "D63A7A", dark: "FF7EB0"))
        case .hipHop:
            GenreMood(gradient: [Color(hex: "F5B700"), Color(hex: "7A4FD0")],
                      accent: Color(light: "A87900", dark: "FFC93C"))
        case .rock:
            GenreMood(gradient: [Color(hex: "D7263D"), Color(hex: "3A3A3A")],
                      accent: Color(light: "B81D30", dark: "FF5A6E"))
        case .jazz:
            GenreMood(gradient: [Color(hex: "3B5BA9"), Color(hex: "C8963E")],
                      accent: Color(light: "2F4B8F", dark: "8FA8E8"))
        case .lofi:
            GenreMood(gradient: [Color(hex: "A79BD9"), Color(hex: "9CC5A1")],
                      accent: Color(light: "6E61A8", dark: "B9AEF0"))
        }
    }
}
