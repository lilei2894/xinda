/**
 * 图片加密脚本 - 将二维码图片加密为dat文件
 * 使用简单的XOR混淆 + Base64编码，防止直接传播
 */

const fs = require('fs');
const path = require('path');

const PUBLIC_DIR = path.join(__dirname, '..', 'public');
const IMAGES = ['donate-5.png', 'donate-10.png', 'donate-20.png'];

// 简单的XOR密钥（8字节）
const KEY = Buffer.from([0x5A, 0x3C, 0x7F, 0x9E, 0x2B, 0x4D, 0x8A, 0x1C]);

/**
 * 简单加密：XOR混淆
 */
function encrypt(data) {
  const result = Buffer.alloc(data.length);
  for (let i = 0; i < data.length; i++) {
    result[i] = data[i] ^ KEY[i % KEY.length];
  }
  return result;
}

IMAGES.forEach((imageName) => {
  const imagePath = path.join(PUBLIC_DIR, imageName);
  const datPath = path.join(PUBLIC_DIR, imageName.replace('.png', '.dat'));

  if (!fs.existsSync(imagePath)) {
    console.error(`❌ 图片不存在: ${imagePath}`);
    return;
  }

  const imageData = fs.readFileSync(imagePath);
  const encryptedData = encrypt(imageData);

  fs.writeFileSync(datPath, encryptedData);
  console.log(`✅ 已加密: ${imageName} -> ${imageName.replace('.png', '.dat')}`);
});

console.log('\n加密完成！原始PNG文件可以删除或备份。');