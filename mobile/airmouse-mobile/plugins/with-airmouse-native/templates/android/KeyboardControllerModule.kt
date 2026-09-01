package com.airmouse.mobile

import android.accessibilityservice.AccessibilityService
import android.content.ClipData
import android.content.ClipboardManager
import android.content.Context
import android.view.inputmethod.InputMethodManager
import android.view.accessibility.AccessibilityNodeInfo
import com.facebook.react.bridge.ReactApplicationContext
import com.facebook.react.bridge.ReactContextBaseJavaModule
import com.facebook.react.bridge.ReactMethod
import com.facebook.react.bridge.ReadableArray

/**
 * KeyboardControllerModule: bridge para ações de teclado via AccessibilityService.
 *
 * typeText: cola o texto no campo focado (clipboard + paste action).
 * pressKey/pressCombo: mapeia keycodes do Mãouse (113=Ctrl, 67=Backspace, 66=Enter)
 * para ações de acessibilidade no nó focado.
 */
class KeyboardControllerModule(reactContext: ReactApplicationContext) :
    ReactContextBaseJavaModule(reactContext) {

    private val context: ReactApplicationContext = reactContext

    override fun getName(): String = "KeyboardController"

    private val service: AirMouseAccessibilityService?
        get() = AirMouseAccessibilityService.instance

    private fun focusedEditable(): AccessibilityNodeInfo? {
        val root = service?.rootInActiveWindow ?: return null
        return root.findFocus(AccessibilityNodeInfo.FOCUS_INPUT)
            ?: findEditable(root, 0)
    }

    /** Digita texto no campo focado via clipboard + paste. */
    @ReactMethod
    fun typeText(text: String) {
        try {
            val clipboard = context.getSystemService(Context.CLIPBOARD_SERVICE) as ClipboardManager
            clipboard.setPrimaryClip(ClipData.newPlainText("airmouse", text))
            focusedEditable()?.performAction(AccessibilityNodeInfo.ACTION_PASTE)
        } catch (_: Exception) {
        }
    }

    /**
     * pressKey: keycode único (sem modificadores).
     * 66=Enter, 67=Backspace, 61=Tab, 62=Space.
     */
    @ReactMethod
    fun pressKey(keyCode: Int) {
        val node = focusedEditable()
        if (node == null) return
        try {
            when (keyCode) {
                66 -> node.performAction(AccessibilityNodeInfo.ACTION_CLICK)
                61 -> node.performAction(AccessibilityNodeInfo.ACTION_FOCUS)
                else -> node.performAction(AccessibilityNodeInfo.ACTION_CLICK)
            }
        } catch (_: Exception) {
        }
    }

    /**
     * pressCombo: recebe um array de keycodes (formato compatível com o
     * Mãouse desktop — 113=Ctrl). Mapeia Ctrl+C / Ctrl+V / Ctrl+X / Ctrl+D
     * para ações de acessibilidade no campo focado.
     */
    @ReactMethod
    fun pressCombo(keys: ReadableArray) {
        if (keys.size() == 0) return
        val kc = keys.getInt(0)
        val key2 = if (keys.size() > 1) keys.getInt(1) else -1
        val isCtrl = kc == 113 || key2 == 113
        val primary = if (kc == 113) key2 else kc

        val node = focusedEditable()
        if (node == null) return
        try {
            if (isCtrl) {
                when (primary) {
                    31 -> node.performAction(AccessibilityNodeInfo.ACTION_COPY)           // C
                    32 -> node.performAction(AccessibilityNodeInfo.ACTION_CUT)            // X
                    50 -> node.performAction(AccessibilityNodeInfo.ACTION_PASTE)          // V: usa clipboard atual
                    40 -> onCtrlD()                                                        // D
                    else -> node.performAction(AccessibilityNodeInfo.ACTION_CLICK)
                }
            } else {
                when (primary) {
                    66 -> node.performAction(AccessibilityNodeInfo.ACTION_CLICK)          // Enter
                    else -> node.performAction(AccessibilityNodeInfo.ACTION_CLICK)
                }
            }
        } catch (_: Exception) {
        }
    }

    @ReactMethod
    fun toggleKeyboard() {
        try {
            val imm = context.getSystemService(Context.INPUT_METHOD_SERVICE) as InputMethodManager
            // Abre/fecha o teclado no campo focado (ACC_AÇÃO_SHOW_IME / HIDE_IME).
            val node = focusedEditable()
            if (node != null) {
                val root = service?.rootInActiveWindow
                if (root != null) {
                    try {
                        node.performAction(AccessibilityNodeInfo.ACTION_SHOW_IME)
                        return
                    } catch (_: Exception) {
                    }
                }
            }
            imm.toggleSoftInput(InputMethodManager.SHOW_IMPLICIT, 0)
        } catch (_: Exception) {
        }
    }

    override fun getConstants(): Map<String, Any> = mapOf(
        // Keycodes compatíveis com o desktop (Ctrl etc.)
        "KEYCODE_CTRL_LEFT" to 113,
        "KEYCODE_ENTER" to 66,
        "KEYCODE_BACKSPACE" to 67,
    )

    private fun onCtrlD() {
        // Ctrl+D: "minimizar/duplicar" — sem equivalente direto; vira Escape (back).
        service?.performGlobalActionCompat(AccessibilityService.GLOBAL_ACTION_BACK)
    }

    private fun findEditable(node: AccessibilityNodeInfo, depth: Int): AccessibilityNodeInfo? {
        if (node.isEditable) return node
        if (depth > 8) return null
        for (i in 0 until node.childCount) {
            val child = node.getChild(i) ?: continue
            val found = findEditable(child, depth + 1)
            if (found != null) return found
        }
        return null
    }
}