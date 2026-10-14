const apiUrl = process.env.EXPO_PUBLIC_API_URL;

if (!apiUrl) {
  throw new Error("Missing EXPO_PUBLIC_API_URL");
}
if (!__DEV__ && !apiUrl.startsWith("https://")) {
  throw new Error("API URL must use HTTPS in production builds");
}

export const config = { apiUrl: apiUrl.replace(/\/$/, "") } as const;