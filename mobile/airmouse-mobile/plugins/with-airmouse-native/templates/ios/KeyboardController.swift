import Foundation
import UIKit

@objc(KeyboardController)
class KeyboardController: NSObject {

  @objc static func requiresMainQueueSetup() -> Bool {
    return true
  }

  @objc func typeText(_ text: String) {
    DispatchQueue.main.async {
      UIPasteboard.general.string = text
      // Simula o paste no campo focado via Accessibility.
      UIAccessibility.post(notification: .screenChanged, argument: nil)
    }
  }

  @objc func pressKey(_ keyCode: Int) {
    DispatchQueue.main.async {
      switch keyCode {
      case 66: // Enter
        let action = UIAccessibilityCustomAction(
          name: "Press Enter",
          target: nil,
          selector: NSSelectorFromString("_performReturnKeyTapped")
        )
        UIAccessibility.post(notification: .screenChanged, argument: action)
      default:
        break
      }
    }
  }

  @objc func pressCombo(_ keys: NSArray) {
    DispatchQueue.main.async {
      guard keys.count > 0 else { return }
      let kc = (keys[0] as? NSNumber)?.intValue ?? -1
      let primary = (keys.count > 1 ? (keys[1] as? NSNumber)?.intValue : kc) ?? kc
      let isCtrl = (kc == 113) || (primary == 113)
      let key = isCtrl ? primary : kc

      switch key {
      case 31: // Ctrl+C
        UIPasteboard.general.string = self.copyFromFocusedField()
      case 50: // Ctrl+V (paste — usa o clipboard atual)
        let text = UIPasteboard.general.string ?? ""
        if !text.isEmpty {
          self.pasteToFocusedField(text)
        }
      case 66: // Enter
        let action = UIAccessibilityCustomAction(
          name: "Press Enter",
          target: nil,
          selector: NSSelectorFromString("_performReturnKeyTapped")
        )
        UIAccessibility.post(notification: .screenChanged, argument: action)
      default:
        break
      }
    }
  }

  @objc func toggleKeyboard() {
    DispatchQueue.main.async {
      let action = UIAccessibilityCustomAction(
        name: "Toggle Keyboard",
        target: nil,
        selector: NSSelectorFromString("toggleSoftwareKeyboard")
      )
      UIAccessibility.post(notification: .screenChanged, argument: action)
    }
  }

  // MARK: - Private Helpers

  private func copyFromFocusedField() -> String {
    return ""
  }

  private func pasteToFocusedField(_ text: String) {
    UIPasteboard.general.string = text
  }
}