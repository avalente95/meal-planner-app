import * as SecureStore from 'expo-secure-store';

const CHUNK_SIZE = 1000; 

const OPTIONS: SecureStore.SecureStoreOptions = {
  keychainAccessible: SecureStore.WHEN_UNLOCKED_THIS_DEVICE_ONLY,
};

const countKey = (key: string) => `${key}.count`;
const chunkKey = (key: string, i: number) => `${key}.${i}`;

async function readCount(key: string): Promise<number> {
  const raw = await SecureStore.getItemAsync(countKey(key), OPTIONS);
  const n = raw === null ? 0 : Number.parseInt(raw, 10);
  return Number.isInteger(n) && n > 0 ? n : 0;
}

async function removeChunks(key: string, from: number, to: number): Promise<void> {
  for (let i = from; i < to; i++) {
    await SecureStore.deleteItemAsync(chunkKey(key, i), OPTIONS);
  }
}

async function getItem(key: string): Promise<string | null> {
  const count = await readCount(key);
  if (count === 0) return null;

  const parts: string[] = [];
  for (let i = 0; i < count; i++) {
    const part = await SecureStore.getItemAsync(chunkKey(key, i), OPTIONS);
    if (part === null) {
      await removeItem(key);
      return null;
    }
    console.log("part read: "+part)
    parts.push(part);
  }
  return parts.join('');
}

async function setItem(key: string, value: string): Promise<void> {
  const oldCount = await readCount(key);
  console.log("setItem: "+key)
  const chunks: string[] = [];
  for (let i = 0; i < value.length; i += CHUNK_SIZE) {
    chunks.push(value.slice(i, i + CHUNK_SIZE));
  }

  for (let i = 0; i < chunks.length; i++) {
    await SecureStore.setItemAsync(chunkKey(key, i), chunks[i], OPTIONS);
  }
  await SecureStore.setItemAsync(countKey(key), String(chunks.length), OPTIONS);
  await removeChunks(key, chunks.length, oldCount);
}

async function removeItem(key: string): Promise<void> {
  const count = await readCount(key);
  await removeChunks(key, 0, count);
  await SecureStore.deleteItemAsync(countKey(key), OPTIONS);
}

export const secureChunkedStorage = { getItem, setItem, removeItem };