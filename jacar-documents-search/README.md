# JACAR 史料搜索 Skill

日本亚洲历史资料中心（JACAR）史料自动化下载工具。

## 文件结构

```
jacar-historical-search/
├── SKILL.md                    # Skill 定义文档
├── references/
│   ├── jacar-fields.md         # 搜索字段参考
│   ├── query-examples.md       # 搜索案例
│   ├── image-download.md       # 图像下载指南
│   └── glossary-topics.md      # Glossary 主题分类
└── scripts/
    └── download-china-incident.js  # 下载脚本
```

## 使用方法

### 1. 安装依赖

```bash
npm install playwright
npx playwright install chromium
```

### 2. 运行下载脚本

```bash
node scripts/download-china-incident.js
```

下载的 PDF 会保存在 `jacar_beijing_results/` 目录。

## 搜索示例

- 支那事変（北京）— 抗日战争时期北京地区活动
- 日清戦争 — 甲午战争
- 日露戦争 — 日俄战争
- 満州事変 — 九一八事变
- 支那事変 — 七七事变/抗日战争

## 注意事项

1. 部分档案只有封面（<50KB），可能是 JACAR 只收录了目录页
2. digital.archives.go.jp 域名的档案需要到馆阅读，无法下载
3. 建议使用有头模式运行，避免验证码问题