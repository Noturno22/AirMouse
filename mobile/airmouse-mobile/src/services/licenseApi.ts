import Constants from 'expo-constants';

export interface EntitleResponse {
  tier: string;
  lease: string;
  session_id: string;
  first_time: boolean;
}

export interface EntitleParams {
  purchaseToken: string;
  productId: string;
  packageName: string;
  deviceId: string;
}

export function licenseServerUrl(): string {
  return (
    process.env.EXPO_PUBLIC_LICENSE_SERVER_URL ||
    (Constants.expoConfig?.extra?.licenseServerUrl as string) ||
    'https://license.maouse.app'
  );
}

export async function entitleMobilePurchase(
  params: EntitleParams
): Promise<EntitleResponse> {
  const res = await fetch(`${licenseServerUrl()}/api/v1/mobile/entitle`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(params),
  });
  if (!res.ok) {
    let message = `HTTP ${res.status}`;
    try {
      const body = await res.json();
      if (body && body.error) message = String(body.error);
    } catch {
      // fallback to HTTP message
    }
    throw new Error(message);
  }
  return (await res.json()) as EntitleResponse;
}
