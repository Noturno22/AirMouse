package com.airmouse.mobile

import com.facebook.react.bridge.Callback
import com.facebook.react.bridge.ReactApplicationContext
import com.facebook.react.bridge.ReactContextBaseJavaModule
import com.facebook.react.bridge.ReactMethod

/**
 * TouchControllerModule: bridge React Native → AirMouseAccessibilityService.
 *
 * Permite simular toques/gestos no ecrã do telemóvel a partir do JS
 * (por exemplo Aparece 4 dedos abertos → longPress no centro do ecrã).
 *
 * Requer que o AirMouseAccessibilityService esteja ativo em
 * Definições > Acessibilidade > AirMouse.
 */
class TouchControllerModule(reactContext: ReactApplicationContext) :
    ReactContextBaseJavaModule(reactContext) {

    override fun getName(): String = "TouchController"

    private val service: AirMouseAccessibilityService?
        get() = AirMouseAccessibilityService.instance

    @ReactMethod
    fun tap(x: Double, y: Double) {
        service?.tap(x.toFloat(), y.toFloat())
    }

    @ReactMethod
    fun longPress(x: Double, y: Double, duration: Double) {
        val ms = (duration * 1000).toLong().coerceAtLeast(1)
        service?.longPress(x.toFloat(), y.toFloat(), ms)
    }

    @ReactMethod
    fun swipe(x1: Double, y1: Double, x2: Double, y2: Double, duration: Double) {
        val ms = (duration * 1000).toLong().coerceAtLeast(1)
        service?.swipe(x1.toFloat(), y1.toFloat(), x2.toFloat(), y2.toFloat(), ms)
    }

    @ReactMethod
    fun dragStart(x: Double, y: Double) {
        service?.dragStart(x.toFloat(), y.toFloat())
    }

    @ReactMethod
    fun dragMove(x: Double, y: Double) {
        service?.dragMove(x.toFloat(), y.toFloat())
    }

    @ReactMethod
    fun dragEnd() {
        service?.dragEnd()
    }

    /** moveCursor: alias de dragMove para mover "o cursor" continuamente. */
    @ReactMethod
    fun moveCursor(x: Double, y: Double) {
        service?.dragMove(x.toFloat(), y.toFloat())
    }

    /** Indicador para o JS de que o serviço de acessibilidade está ativo. */
    @ReactMethod
    fun isAccessibilityEnabled(callback: Callback) {
        callback.invoke(service != null)
    }
}