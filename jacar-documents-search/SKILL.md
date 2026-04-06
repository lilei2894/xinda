# JACAR 历史史料搜索自动化技能

## 技能描述

JACAR（亚洲历史资料中心 / Japan Center for Asian Historical Records）史料搜索自动化技能。利用浏览器自动化技术，在 JACAR 数据库中搜索历史史料，提取结果列表、详情页元数据、资料图像，并支持批量搜索与导出。

**核心特点：**
- 使用浏览器自动化（Playwright），无需额外依赖
- 支持关键词搜索、详细多条件搜索、Glossary 分类浏览
- 批量提取多页结果及完整元数据
- 支持资料图像（JPEG）下载与 PDF 导出
- 有头模式处理反机器人验证

## 前置要求

- OpenClaw 环境（已配置 Playwright 浏览器工具）
- 可访问 JACAR 网站（https://www.jacar.go.jp / https://www.jacar.archives.go.jp）
- **建议使用有头浏览器模式** 以便处理验证码
- 本地存储权限（用于保存搜索结果和下载的图像）

## JACAR 网站架构

JACAR 的实际搜索功能托管在独立域名上：

| 功能 | URL |
|------|-----|
| 中文首页 | `https://www.jacar.go.jp/chinese/` |
| 详细搜索（英文界面） | `https://www.jacar.archives.go.jp/aj/search-en` |
| 搜索指南 | `https://www.jacar.archives.go.jp/aj/help/search_guide.html` |
| Glossary 主题浏览 | `https://www.jacar.go.jp/english/glossary_en/` |
| 检索编码搜索 | `https://www.jacar.archives.go.jp/aj/search-code-en` |

**重要：** 所有搜索操作均在 `jacar.archives.go.jp` 域进行，中文首页仅作为入口。

---

## 功能1：关键词搜索 + 结果列表提取

### 执行步骤

**Step 1: 导航到搜索页面**

```
action: navigate
url: https://www.jacar.archives.go.jp/aj/search-en
```

**Step 2: 输入搜索关键词**

在关键词搜索框中输入查询词。JACAR 支持布尔逻辑：
- `AND` / `OR` / `NOT` 组合
- 精确短语用双引号 `"phrase"`
- 支持日文、中文、英文关键词

```
kind: fill
ref: 关键词搜索输入框
text: 日清戦争
```

**Step 3: 选择搜索范围（可选）**

JACAR 提供搜索范围选择：
- 全文（Full Text）— 默认
- 标题（Title）
- 注记（Notes）
- 件名（Subject）

```
kind: click
ref: 搜索范围下拉菜单
# 选择所需范围
```

**Step 4: 执行搜索**

```
kind: click
ref: 搜索按钮
```

**Step 5: 等待结果加载**

```
loadState: networkidle
timeMs: 10000
```

**Step 6: 提取结果列表**

在浏览器中执行以下 JavaScript 提取当前页结果：

```javascript
function extractJacarResults() {
  const results = [];
  
  // JACAR 搜索结果列表中的每条记录
  const items = document.querySelectorAll('.result-item, .search-result, table tr');
  
  items.forEach((item, index) => {
    // 跳过表头
    if (index === 0 && item.querySelector('th')) return;
    
    const titleLink = item.querySelector('a');
    const title = titleLink?.textContent?.trim() || '';
    const link = titleLink?.href || '';
    
    // 提取元数据字段
    const cells = item.querySelectorAll('td');
    const text = item.textContent?.trim() || '';
    
    results.push({
      index: index,
      title: title,
      link: link,
      // 根据实际 DOM 结构调整
      refCode: cells[0]?.textContent?.trim() || '',  // 检索编码
      title_raw: cells[1]?.textContent?.trim() || title,
      date: extractDate(text),
      organization: extractOrganization(text),
      type: extractDocumentType(text),
      thumbnail: item.querySelector('img')?.src || ''
    });
  });
  
  return results;
}

function extractDate(text) {
  // 匹配日期格式：明治XX年、大正XX年、昭和XX年、YYYY年等
  const patterns = [
    /(明治|大正|昭和|平成|令和)\d{1,2}年\d{1,2}月?\d{1,2}日?/,
    /\d{4}年\d{1,2}月?\d{1,2}日?/,
    /\d{4}-\d{2}-\d{2}/
  ];
  for (const p of patterns) {
    const m = text.match(p);
    if (m) return m[0];
  }
  return '';
}

function extractOrganization(text) {
  // 常见保管机关
  const orgs = ['外務省', '防衛省', '国立公文書館', 'Ministry of Foreign Affairs', 'Defense Ministry'];
  for (const org of orgs) {
    if (text.includes(org)) return org;
  }
  return '';
}

function extractDocumentType(text) {
  const types = ['公文書', '公文书', '公文', '記録', '報告', '書簡', '電報'];
  for (const t of types) {
    if (text.includes(t)) return t;
  }
  return '';
}

extractJacarResults();
```

**提取后数据示例：**

```json
[
  {
    "index": 0,
    "title": "日清戦争関係一件",
    "link": "https://www.jacar.archives.go.jp/aj/image/A0123456789",
    "refCode": "A0123456789",
    "title_raw": "日清戦争関係一件",
    "date": "明治27年8月",
    "organization": "外務省",
    "type": "公文書",
    "thumbnail": "https://www.jacar.archives.go.jp/aj/thumbnail/A0123456789"
  }
]
```

---

## 功能2：详细搜索（多条件组合）

### 执行步骤

**Step 1: 打开详细搜索页面**

```
action: navigate
url: https://www.jacar.archives.go.jp/aj/search-en
```

**Step 2: 切换到详细搜索模式**

点击"Advanced Search"或"詳細検索"链接/按钮展开高级搜索面板。

```
kind: click
ref: 详细搜索切换按钮
```

**Step 3: 设置搜索条件**

JACAR 详细搜索支持以下条件组合：

| 条件 | 说明 | 操作 |
|------|------|------|
| 关键词 | 搜索词 + 搜索范围 | fill 输入框 |
| 年代范围 | 开始年 ~ 结束年 | fill 两个年份输入框 |
| 日本纪年 | 明治/大正/昭和/平成 | select 下拉菜单 |
| 保管机关 | 外務省/防衛省/国立公文書館 | select 或 checkbox |
| 资料种类 | 公文書/図画/写真等 | checkbox 多选 |
| 语言 | 日文/英文/中文 | select |

```
# 关键词
kind: fill
ref: 关键词输入框
text: 辛亥革命

# 年代范围
kind: fill
ref: 开始年输入框
text: 1911

kind: fill
ref: 结束年输入框
text: 1912

# 保管机关
kind: click
ref: 保管机关下拉菜单
# 选择"外務省"

# 资料种类
kind: click
ref: 公文書 checkbox
```

**Step 4: 执行搜索并提取结果**

同功能1的 Step 4-6。

---

## 功能3：详情页元数据提取

### 执行步骤

**Step 1: 导航到详情页**

从搜索结果中获取详情页 URL，直接导航：

```
action: navigate
url: https://www.jacar.archives.go.jp/aj/image/A0123456789
```

**Step 2: 等待页面加载**

```
loadState: networkidle
timeMs: 8000
```

**Step 3: 提取详情页元数据**

```javascript
function extractJacarDetail() {
  const meta = {};
  
  // 检索编码（Reference Code）
  const refCodeEl = document.querySelector('.ref-code, .reference-code, [class*="refCode"]');
  meta.refCode = refCodeEl?.textContent?.trim() || '';
  
  // 标题
  const titleEl = document.querySelector('h1, .title, [class*="title"]');
  meta.title = titleEl?.textContent?.trim() || '';
  
  // 日期
  const dateEl = document.querySelector('.date, .publish-date, [class*="date"]');
  meta.date = dateEl?.textContent?.trim() || '';
  
  // 保管机关
  const orgEl = document.querySelector('.organization, .agency, [class*="org"]');
  meta.organization = orgEl?.textContent?.trim() || '';
  
  // 资料种类
  const typeEl = document.querySelector('.type, .document-type, [class*="type"]');
  meta.documentType = typeEl?.textContent?.trim() || '';
  
  // 明治/大正/昭和纪年
  const eraEl = document.querySelector('.era, [class*="era"]');
  meta.era = eraEl?.textContent?.trim() || '';
  
  // 描述/摘要
  const descEl = document.querySelector('.description, .abstract, .summary, [class*="desc"]');
  meta.description = descEl?.textContent?.trim() || '';
  
  // 图像信息
  const images = [];
  const imageLinks = document.querySelectorAll('.image-list a, .thumbnail-list a');
  imageLinks.forEach(link => {
    const img = link.querySelector('img');
    images.push({
      thumb: img?.src || '',
      full: link.href || '',
      page: img?.alt || link.textContent?.trim() || ''
    });
  });
  meta.images = images;
  
  // PDF 下载链接
  const pdfLink = document.querySelector('a[href*=".pdf"], .pdf-download, [class*="pdf"]');
  meta.pdfUrl = pdfLink?.href || '';
  
  return meta;
}

extractJacarDetail();
```

**提取后数据示例：**

```json
{
  "refCode": "A0123456789",
  "title": "日清戦争関係一件",
  "date": "1894年8月",
  "organization": "外務省",
  "documentType": "公文書",
  "era": "明治27年",
  "description": "日清戦争に関する外交文書...",
  "images": [
    {
      "thumb": "https://.../A0123456789_001_thumb.jpg",
      "full": "https://.../A0123456789_001.jpg",
      "page": "1"
    }
  ],
  "pdfUrl": "https://.../A0123456789.pdf"
}
```

---

## 功能4：批量搜索与导出

### 执行步骤

**Step 1: 准备搜索关键词列表**

```
# 示例：批量搜索多个历史事件
keywords = [
  "日清戦争",
  "日露戦争", 
  "辛亥革命",
  "満州事変",
  "支那事変",
  "大東亜戦争"
]
```

**Step 2: 循环执行搜索**

对每个关键词：
1. 导航到搜索页面
2. 输入关键词
3. 执行搜索
4. 提取结果列表
5. 翻页提取所有页
6. 保存该关键词的结果

**Step 3: 翻页处理**

```
# 点击下一页按钮
kind: click
ref: 下一页按钮

# 或使用键盘
kind: press
key: ArrowRight

# 等待加载
timeMs: 3000
```

**Step 4: 合并并导出结果**

```javascript
// 合并所有关键词的结果
const allResults = [];
// ... 每次搜索结果 push 到 allResults

// 去重（基于 refCode）
const unique = [];
const seen = new Set();
for (const r of allResults) {
  if (r.refCode && !seen.has(r.refCode)) {
    seen.add(r.refCode);
    unique.push(r);
  }
}

unique;
```

### 导出格式

**JSON 导出：**

```json
[
  {
    "keyword": "日清戦争",
    "refCode": "A0123456789",
    "title": "...",
    "date": "...",
    "organization": "...",
    "documentType": "...",
    "link": "...",
    "detail": { /* 详情页元数据 */ }
  }
]
```

**CSV 导出：**

```csv
keyword,refCode,title,date,organization,documentType,link
日清戦争,A0123456789,日清戦争関係一件,明治27年8月,外務省,公文書,https://...
```

---

## 功能5：资料图像下载

### 执行步骤

**Step 1: 导航到资料详情页**

```
action: navigate
url: https://www.jacar.archives.go.jp/aj/image/A0123456789
```

**Step 2: 打开图像查看器**

```
kind: click
ref: 图像查看器/缩略图
```

**Step 3: 提取图像 URL**

```javascript
function extractImageUrls() {
  const urls = [];
  
  // 图像列表中的缩略图
  const thumbs = document.querySelectorAll('.image-list img, .thumbnail img');
  thumbs.forEach(img => {
    urls.push({
      page: img.alt || '',
      thumb: img.src,
      // 从缩略图 URL 推导全尺寸 URL
      full: img.src.replace('_thumb', '').replace('_s', '')
    });
  });
  
  // 查看器中的当前图像
  const viewerImg = document.querySelector('.viewer img, .image-viewer img, canvas');
  if (viewerImg) {
    urls.push({
      page: 'current',
      viewer: viewerImg.src || viewerImg.getAttribute('data-src')
    });
  }
  
  return urls;
}

extractImageUrls();
```

**Step 4: 下载图像**

使用 Playwright 的网络拦截或直接下载：

```
# 获取图像 URL 后，使用网络工具下载
# 或使用 evaluate 触发下载
```

**Step 5: 翻页下载所有页**

```
# 查看器中翻页
kind: click
ref: 下一页图像按钮
timeMs: 2000
# 提取并下载当前页图像
```

---

## 功能6：Glossary / 分类浏览

### 执行步骤

**Step 1: 导航到 Glossary 页面**

```
action: navigate
url: https://www.jacar.go.jp/english/glossary_en/
```

**Step 2: 选择主题分类**

JACAR Glossary 提供以下主题分类：

| 主题分类 | 时期 | 说明 |
|----------|------|------|
| Japan's Army | 明治·大正 | 陆军相关（省部、参谋、教育、战时体制等） |
| Meiji Government | 明治 | 明治政府（决策、外交、内政、司法等） |
| Colonies/Occupied Territories | 明治/大正/昭和 | 殖民地（台湾、朝鲜、满洲、南洋等） |
| Wartime Regime | 昭和 | 战时体制（动员、经济、军事管制等） |
| Allied Occupation | 昭和 | 盟军占领期 |
| Demobilization/Repatriation | 昭和 | 复员·引扬 |

```
kind: click
ref: 主题分类链接（如"Taiwan"、"Korea"等）
```

**Step 3: 浏览术语条目**

```javascript
function extractGlossaryEntries() {
  const entries = [];
  
  // 术语列表
  const terms = document.querySelectorAll('.term-item, .glossary-term, dt');
  terms.forEach(term => {
    entries.push({
      term: term.textContent?.trim() || '',
      link: term.querySelector('a')?.href || '',
      description: term.nextElementSibling?.textContent?.trim() || ''
    });
  });
  
  return entries;
}

extractGlossaryEntries();
```

**Step 4: 从 Glossary 条目跳转到数据库搜索**

每个 Glossary 条目通常包含指向 JACAR 数据库搜索的链接。点击这些链接可自动执行预设搜索。

```
kind: click
ref: 数据库搜索链接
# 跳转到搜索结果页，然后使用功能1提取
```

---

## 反机器人验证处理

JACAR 可能出现验证码，需要用户手动处理：

### 处理方法

**有头浏览器模式（推荐）：**

```
profile: user
action: navigate
url: https://www.jacar.archives.go.jp/aj/search-en
```

出现验证时：
> "检测到 JACAR 验证，请手动完成验证后继续"

### 避免验证的建议

- 使用有头模式
- 操作间隔 2-3 秒
- 保持会话，不要频繁新建浏览器实例
- 避免过快翻页

---

## 完整工作流示例

### 搜索"日清战争"相关史料

```
1. 导航到搜索页面
   action: navigate
   url: https://www.jacar.archives.go.jp/aj/search-en

2. 输入关键词
   kind: fill
   ref: 搜索框
   text: 日清戦争

3. 执行搜索
   kind: click
   ref: 搜索按钮

4. 等待结果
   loadState: networkidle
   timeMs: 10000

5. 提取当前页结果
   evaluate: extractJacarResults()

6. 翻页提取所有页
   循环：提取 → 翻页 → 等待 → 提取

7. 对每条结果提取详情页元数据
   导航到详情页 → 提取元数据 → 提取图像 URL

8. 保存结果
   导出为 JSON/CSV
```

---

## 注意事项

1. **验证码处理**：有头模式下用户可手动处理
2. **请求频率**：每页操作间隔 2-3 秒
3. **语言**：搜索界面为英文，但史料标题和描述多为日文/中文
4. **图像访问**：部分图像可能需要通过查看器逐页加载
5. **数据完整性**：部分老旧文献可能缺少某些元数据字段

## 错误处理

| 错误情况 | 解决方法 |
|----------|----------|
| 页面加载超时 | 增加等待时间或刷新重试 |
| 找不到元素 | 使用备选选择器 |
| 验证码出现 | 等待用户手动完成 |
| 数据提取为空 | 检查页面结构是否变化 |
| 图像加载失败 | 等待更长时间或重试 |

## 相关文件

- `references/jacar-fields.md` — JACAR 搜索字段一览表
- `references/query-examples.md` — 搜索查询案例
- `references/image-download.md` — 图像查看器与下载指南
- `references/glossary-topics.md` — Glossary 主题分类结构
