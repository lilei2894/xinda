# JACAR 图像查看器与下载指南

## 图像查看器概述

JACAR 的资料图像通过内置查看器展示，支持以下功能：
- 逐页浏览（上一页/下一页）
- 缩放（放大/缩小/适应窗口）
- 旋转
- 全尺寸查看

## 查看器访问方式

### 方式1：从搜索结果进入

1. 在搜索结果列表中点击资料标题
2. 跳转到资料详情页
3. 详情页包含图像查看器或缩略图列表

### 方式2：直接通过 URL 访问

```
https://www.jacar.archives.go.jp/aj/image/{检索编码}
```

例如：
```
https://www.jacar.archives.go.jp/aj/image/A0123456789
```

## 图像 URL 结构

### 缩略图 URL

```
https://www.jacar.archives.go.jp/aj/thumbnail/{检索编码}
https://www.jacar.archives.go.jp/aj/thumbnail/{检索编码}_{页码}
```

### 全尺寸图像 URL

```
https://www.jacar.archives.go.jp/aj/image/{检索编码}/{页码}
```

### PDF 下载 URL

```
https://www.jacar.archives.go.jp/aj/pdf/{检索编码}
```

**注意：** 实际 URL 结构可能因 JACAR 版本更新而变化。建议通过浏览器开发者工具或 Playwright 网络拦截来确认当前 URL 模式。

## 提取图像 URL 的方法

### 方法1：DOM 提取

```javascript
function extractAllImageUrls() {
  const urls = {
    thumbnails: [],
    fullSize: [],
    pdf: null
  };
  
  // 缩略图列表
  const thumbs = document.querySelectorAll('.image-list img, .thumbnail img, [class*="thumb"] img');
  thumbs.forEach(img => {
    urls.thumbnails.push({
      page: img.alt || img.title || '',
      url: img.src
    });
  });
  
  // 查看器中的当前图像
  const viewerImg = document.querySelector('.viewer img, .image-viewer img, #viewer img');
  if (viewerImg) {
    urls.fullSize.push({
      page: 'current',
      url: viewerImg.src || viewerImg.dataset.src || ''
    });
  }
  
  // 从缩略图推导全尺寸 URL
  urls.thumbnails.forEach(thumb => {
    // 常见模式：去掉 _thumb 或 _s 后缀
    const fullUrl = thumb.url
      .replace('_thumb', '')
      .replace('_s.', '.')
      .replace('/thumbnail/', '/image/');
    urls.fullSize.push({
      page: thumb.page,
      url: fullUrl
    });
  });
  
  // PDF 下载链接
  const pdfLinks = document.querySelectorAll('a[href*=".pdf"], a[href*="pdf"], .pdf-download a');
  if (pdfLinks.length > 0) {
    urls.pdf = pdfLinks[0].href;
  }
  
  return urls;
}

extractAllImageUrls();
```

### 方法2：网络拦截（Playwright）

```javascript
// 在 Playwright 中拦截图像请求
// 监听所有图片加载事件
const imageUrls = [];

page.on('response', async (response) => {
  const url = response.url();
  if (url.match(/\.(jpg|jpeg|png|tif|tiff)$/i)) {
    imageUrls.push(url);
  }
  if (url.match(/\.pdf$/i)) {
    imageUrls.push(url);
  }
});
```

## 查看器翻页操作

### 按钮点击

```
# 下一页图像
kind: click
ref: 下一页按钮 / Next Page

# 上一页图像
kind: click
ref: 上一页按钮 / Previous Page

# 跳转到指定页
kind: click
ref: 页码输入框
kind: fill
ref: 页码输入框
text: 5
kind: press
key: Enter
```

### 键盘操作

```
# 下一页
kind: press
key: ArrowRight

# 上一页
kind: press
key: ArrowLeft

# 放大
kind: press
key: +

# 缩小
kind: press
key: -
```

## 批量下载流程

### 步骤

1. 导航到资料详情页
2. 获取总页数
3. 循环每一页：
   - 翻到该页
   - 等待图像加载
   - 提取图像 URL
   - 下载图像
4. 保存所有图像到本地

### 示例流程

```
# 1. 导航到详情页
action: navigate
url: https://www.jacar.archives.go.jp/aj/image/A0123456789

# 2. 获取总页数
evaluate: document.querySelector('.total-pages, .page-count')?.textContent

# 3. 循环下载
# 对每一页：
kind: click
ref: 缩略图第N页
timeMs: 3000
evaluate: document.querySelector('.viewer img')?.src
# 保存图像

# 4. 或下载 PDF
kind: click
ref: PDF下载链接
```

## 注意事项

1. **图像加载**：查看器中的图像可能懒加载，需要等待或滚动到可视区域
2. **分辨率**：全尺寸图像可能需要额外请求，缩略图 URL 不等于全尺寸 URL
3. **跨域**：图像可能从 CDN 或单独域名加载
4. **PDF 限制**：部分资料可能不提供 PDF 下载，仅支持逐页查看
5. **版权**：下载的图像需遵循 JACAR 的使用条款

## 常见问题

| 问题 | 解决方法 |
|------|----------|
| 图像加载缓慢 | 增加等待时间（5-10秒） |
| 找不到图像 URL | 检查网络拦截，查看实际请求 |
| PDF 下载失败 | 尝试右键另存为或使用 Playwright 下载 API |
| 查看器不响应 | 刷新页面重试，或尝试直接 URL 访问 |
