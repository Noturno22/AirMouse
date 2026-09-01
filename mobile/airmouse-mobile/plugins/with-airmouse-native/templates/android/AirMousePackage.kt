package com.airmouse.mobile

import com.facebook.react.ReactPackage
import com.facebook.react.bridge.NativeModule
import com.facebook.react.bridge.ReactApplicationContext
import com.facebook.react.uimanager.ViewManager

/**
 * AirMousePackage: regista os módulos nativos (Touch, Keyboard, System).
 * Adicionado no MainApplication.kt à lista de packages do React Native.
 */
class AirMousePackage : ReactPackage {
    override fun createNativeModules(reactContext: ReactApplicationContext): List<NativeModule> =
        listOf(
            TouchControllerModule(reactContext),
            KeyboardControllerModule(reactContext),
            SystemControllerModule(reactContext),
        )

    override fun createViewManagers(reactContext: ReactApplicationContext): List<ViewManager<*, *>> =
        emptyList()
}