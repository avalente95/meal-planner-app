const apiUrl = process.env.EXPO_PUBLIC_API_URL;
const apiKey = process.env.EXPO_PUBLIC_API_KEY;

if (!apiUrl || !apiKey) {
  throw new Error("Missing EXPO_PUBLIC_API_URL or EXPO_PUBLIC_API_KEY");
}
if (!__DEV__ && !apiUrl.startsWith("https://")) {
  throw new Error("API URL must use HTTPS in production builds");
}

export const config = { apiUrl: apiUrl.replace(/\/$/, ""), apiKey } as const;