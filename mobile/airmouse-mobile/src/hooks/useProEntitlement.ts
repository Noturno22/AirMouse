import Constants from 'expo-constants';
import type { Product, Purchase } from 'expo-iap';
import { useIAP } from 'expo-iap';
import { useCallback, useEffect, useState } from 'react';

import { entitleMobilePurchase } from '../services/licenseApi';
import { useLicenseStore } from '../store/license';
import { getDeviceId } from '../utils/deviceId';

export const PRO_PRODUCT_ID =
  (Constants.expoConfig?.extra?.mobileProductId as string) || 'maouse_mobile_pro';
const PACKAGE_NAME =
  (Constants.expoConfig?.extra?.androidPackage as string) || 'com.airmouse.mobile';

export interface ProEntitlement {
  isPro: boolean;
  status: 'loading' | 'ready' | 'error';
  product: Product | null;
  purchasing: boolean;
  actionError: string | null;
  purchasePro: () => Promise<void>;
  restorePro: () => Promise<void>;
  clearActionError: () => void;
}

export function useProEntitlement(): ProEntitlement {
  const tier = useLicenseStore((s) => s.tier);
  const status = useLicenseStore((s) => s.status);
  const hydrate = useLicenseStore((s) => s.hydrate);
  const unlockPro = useLicenseStore((s) => s.unlockPro);

  const [product, setProduct] = useState<Product | null>(null);
  const [purchasing, setPurchasing] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);

  const androidPackage = (purchase: Purchase): string =>
    (purchase as { packageNameAndroid?: string | null }).packageNameAndroid ||
    PACKAGE_NAME;

  const iap = useIAP({
    onPurchaseSuccess: async (purchase: Purchase) => {
      setPurchasing(true);
      try {
        const deviceId = await getDeviceId();
        await entitleMobilePurchase({
          purchaseToken: purchase.purchaseToken || '',
          productId: purchase.productId,
          packageName: androidPackage(purchase),
          deviceId,
        });
        await unlockPro();
      } catch (e) {
        const msg = e instanceof Error ? e.message : String(e);
        setActionError(msg);
        // Não finaliza a transação: o servidor não validou, será repetida.
        setPurchasing(false);
        return;
      }
      await iap.finishTransaction({ purchase, isConsumable: false });
      setPurchasing(false);
    },
    onPurchaseError: (error) => {
      setPurchasing(false);
      setActionError(error.message);
    },
  });

  // Hydrate a licença persistida + participação em produtos no arranque.
  useEffect(() => {
    hydrate();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    if (!iap.connected) return;
    iap.fetchProducts({ skus: [PRO_PRODUCT_ID], type: 'in-app' }).catch((e) => {
      const msg = e instanceof Error ? e.message : String(e);
      setActionError(msg);
    });
  }, [iap.connected]);

  useEffect(() => {
    const found = iap.products.find((p) => p.id === PRO_PRODUCT_ID);
    if (found) setProduct(found);
  }, [iap.products]);

  const purchasePro = useCallback(async () => {
    setActionError(null);
    setPurchasing(true);
    try {
      await iap.requestPurchase({
        request: {
          google: { skus: [PRO_PRODUCT_ID] },
          apple: { sku: PRO_PRODUCT_ID },
        },
        type: 'in-app',
      });
    } catch (e) {
      setPurchasing(false);
      const msg = e instanceof Error ? e.message : String(e);
      setActionError(msg);
    }
  }, [iap]);

  const restorePro = useCallback(async () => {
    setActionError(null);
    setPurchasing(true);
    try {
      await iap.getAvailablePurchases();
      const found = iap.availablePurchases.find(
        (p) => p.productId === PRO_PRODUCT_ID && p.purchaseState === 'purchased'
      );
      if (found && found.purchaseToken) {
        const deviceId = await getDeviceId();
        await entitleMobilePurchase({
          purchaseToken: found.purchaseToken,
          productId: found.productId,
          packageName: androidPackage(found),
          deviceId,
        });
        await unlockPro();
        await iap.finishTransaction({ purchase: found, isConsumable: false });
      } else {
        setActionError('Sem compras ativas para restaurar');
      }
    } catch (e) {
      const msg = e instanceof Error ? e.message : String(e);
      setActionError(msg);
    } finally {
      setPurchasing(false);
    }
  }, [iap, unlockPro]);

  return {
    isPro: tier === 'mobile_pro',
    status,
    product,
    purchasing,
    actionError,
    purchasePro,
    restorePro,
    clearActionError: () => setActionError(null),
  };
}
