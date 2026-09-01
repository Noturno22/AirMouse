package com.airmouse.mobile

import android.accessibilityservice.AccessibilityService
import android.content.Context
import android.media.AudioManager
import android.provider.Settings
import android.view.WindowManager
import com.facebook.react.bridge.Arguments
import com.facebook.react.bridge.Promise
import com.facebook.react.bridge.ReactApplicationContext
import com.facebook.react.bridge.ReactContextBaseJavaModule
import com.facebook.react.bridge.ReactMethod
import com.facebook.react.bridge.WritableMap

/**
 * SystemControllerModule: bridge para ações globais do sistema Android.
 *
 * Back/Home/Recents/Notificações/QuickSettings usam o AccessibilityService
 * (performGlobalAction). Volume usa AudioManager. Brilho usa Settings.System.
 * Tudo sem root. Requer o serviço de acessibilidade ativo para as ações
 * globais; volume e brilho funcionam sem ele.
 */
class SystemControllerModule(reactContext: ReactApplicationContext) :
    ReactContextBaseJavaModule(reactContext) {

    private val context: ReactApplicationContext = reactContext

    override fun getName(): String = "SystemController"

    private val service: AirMouseAccessibilityService?
        get() = AirMouseAccessibilityService.instance

    @ReactMethod
    fun goBack() {
        service?.performGlobalActionCompat(AccessibilityService.GLOBAL_ACTION_BACK)
    }

    @ReactMethod
    fun goHome() {
        service?.performGlobalActionCompat(AccessibilityService.GLOBAL_ACTION_HOME)
    }

    @ReactMethod
    fun openRecents() {
        service?.performGlobalActionCompat(AccessibilityService.GLOBAL_ACTION_RECENTS)
    }

    @ReactMethod
    fun openNotifications() {
        service?.performGlobalActionCompat(
            AccessibilityService.GLOBAL_ACTION_NOTIFICATIONS
        )
    }

    @ReactMethod
    fun toggleQuickSettings() {
        service?.performGlobalActionCompat(
            AccessibilityService.GLOBAL_ACTION_QUICK_SETTINGS
        )
    }

    @ReactMethod
    fun takeScreenshot() {
        service?.performGlobalActionCompat(
            AccessibilityService.GLOBAL_ACTION_TAKE_SCREENSHOT
        )
    }

    /** direction: +1 subir, -1 descer. */
    @ReactMethod
    fun adjustVolume(direction: Int) {
        val audio = context.getSystemService(Context.AUDIO_SERVICE) as AudioManager
        val dir = if (direction > 0) AudioManager.ADJUST_RAISE else AudioManager.ADJUST_LOWER
        audio.adjustStreamVolume(AudioManager.STREAM_MUSIC, dir, AudioManager.FLAG_SHOW_UI)
    }

    /** level: 0-255 (mapeado para 0-1 do sistema). */
    @ReactMethod
    fun setBrightness(level: Int) {
        try {
            Settings.System.putInt(
                context.contentResolver,
                Settings.System.SCREEN_BRIGHTNESS,
                level.coerceIn(0, 255)
            )
        } catch (_: Exception) {
            // Sem permissão WRITE_SETTINGS — ignora.
        }
    }

    @ReactMethod
    fun getScreenDimensions(promise: Promise) {
        try {
            val wm = context.getSystemService(Context.WINDOW_SERVICE) as WindowManager
            val metrics = android.util.DisplayMetrics()
            wm.defaultDisplay.getRealMetrics(metrics)
            val map: WritableMap = Arguments.createMap()
            map.putDouble("width", metrics.widthPixels.toDouble())
            map.putDouble("height", metrics.heightPixels.toDouble())
            map.putDouble("density", metrics.density.toDouble())
            promise.resolve(map)
        } catch (e: Exception) {
            promise.reject("SCREEN_DIMS_ERROR", e)
        }
    }

    @ReactMethod
    fun isAccessibilityEnabled(promise: Promise) {
        promise.resolve(service != null)
    }
}