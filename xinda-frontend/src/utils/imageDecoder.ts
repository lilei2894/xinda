const KEY = new Uint8Array([0x5A, 0x3C, 0x7F, 0x9E, 0x2B, 0x4D, 0x8A, 0x1C]);

export async function decryptImage(url: string): Promise<string> {
  const response = await fetch(url);
  const arrayBuffer = await response.arrayBuffer();
  const encryptedData = new Uint8Array(arrayBuffer);

  const decrypted = new Uint8Array(encryptedData.length);
  for (let i = 0; i < encryptedData.length; i++) {
    decrypted[i] = encryptedData[i] ^ KEY[i % KEY.length];
  }

  const blob = new Blob([decrypted], { type: 'image/png' });
  return URL.createObjectURL(blob);
}