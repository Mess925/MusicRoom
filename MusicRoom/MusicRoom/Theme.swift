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
