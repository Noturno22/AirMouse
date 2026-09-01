package com.airmouse.mobile

import android.accessibilityservice.AccessibilityService
import android.accessibilityservice.GestureDescription
import android.graphics.Path
import android.view.accessibility.AccessibilityEvent
import android.view.accessibility.AccessibilityNodeInfo

/**
 * AirMouseAccessibilityService: serviço de acessibilidade que permite ao Mãouse
 * injetar gestos (tap, longPress, swipe, drag) e ações globais (back, home,
 * recents, notificações) em qualquer app — sem root.
 *
 * Utilizadores têm de ativar o serviço em:
 *   Definições > Acessibilidade > AirMouse (AirMouse Accessibility)
 *
 * O serviço é referenciado estaticamente pelos módulos nativos
 * (TouchControllerModule / SystemControllerModule) para despachar gestos.
 */
class AirMouseAccessibilityService : AccessibilityService() {

    companion object {
        @Volatile
        var instance: AirMouseAccessibilityService? = null
    }

    private var isDragging = false
    private var lastDragX = 0f
    private var lastDragY = 0f

    override fun onServiceConnected() {
        super.onServiceConnected()
        instance = this
    }

    override fun onAccessibilityEvent(event: AccessibilityEvent?) {
        // Sem lógica de eventos por agora — apenas despachamos gestos on-demand.
    }

    override fun onInterrupt() {
        // Nada a interromper.
    }

    override fun onDestroy() {
        instance = null
        super.onDestroy()
    }

    fun isReady(): Boolean = true

    /** Tap simples: toque rápido num ponto do ecrã. */
    fun tap(x: Float, y: Float) {
        val path = Path()
        path.moveTo(x, y)
        val stroke = GestureDescription.StrokeDescription(path, 0, 80L)
        dispatchGesture(GestureDescription.Builder().addStroke(stroke).build(), null, null)
    }

    /** Long press: manter o dedo num ponto durante `durationMs`. */
    fun longPress(x: Float, y: Float, durationMs: Long) {
        val path = Path()
        path.moveTo(x, y)
        val stroke = GestureDescription.StrokeDescription(path, 0, durationMs)
        dispatchGesture(GestureDescription.Builder().addStroke(stroke).build(), null, null)
    }

    /** Swipe linear de (x1,y1) para (x2,y2) em `durationMs`. */
    fun swipe(x1: Float, y1: Float, x2: Float, y2: Float, durationMs: Long) {
        val path = Path()
        path.moveTo(x1, y1)
        path.lineTo(x2, y2)
        val stroke = GestureDescription.StrokeDescription(path, 0, durationMs)
        dispatchGesture(GestureDescription.Builder().addStroke(stroke).build(), null, null)
    }

    /**
     * Início de drag. Despacha um gesto de manutenção (long-press) para manter o
     * dedo "em baixo" enquanto o utilizador arrasta.
     */
    fun dragStart(x: Float, y: Float, holdMs: Long = 1000L) {
        isDragging = true
        lastDragX = x
        lastDragY = y
        val path = Path()
        path.moveTo(x, y)
        val stroke = GestureDescription.StrokeDescription(path, 0, holdMs)
        dispatchGesture(GestureDescription.Builder().addStroke(stroke).build(), null, null)
    }

    /** Continuação do drag: desloca o dedo para o novo ponto. */
    fun dragMove(x: Float, y: Float, durationMs: Long = 60L) {
        if (!isDragging) {
            dragStart(x, y)
            return
        }
        val path = Path()
        path.moveTo(lastDragX, lastDragY)
        path.lineTo(x, y)
        val stroke = GestureDescription.StrokeDescription(path, 0, durationMs)
        dispatchGesture(GestureDescription.Builder().addStroke(stroke).build(), null, null)
        lastDragX = x
        lastDragY = y
    }

    /** Fim do drag: pequeno tap de ruído para largar o dedo. */
    fun dragEnd() {
        if (!isDragging) {
            return
        }
        isDragging = false
        tap(lastDragX, lastDragY)
    }

    fun performGlobalActionCompat(action: Int): Boolean =
        performGlobalAction(action)
}