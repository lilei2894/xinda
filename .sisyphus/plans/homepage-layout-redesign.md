# 主页布局改造 - 右侧设置面板 + 模型管理

## TL;DR

> **Quick Summary**: 将主页拖拽上传区移至左侧(60%)，右侧新增40%设置面板（文档语言、识别模型、翻译模型下拉框），并在面板顶部添加"模型设置"按钮弹出模型选择弹窗。后端新增提供商/模型管理 API 和扩展配置存储。
> 
> **Deliverables**: 
> - 主页左右分栏布局（60/40）
> - 右侧设置面板组件（3个下拉框 + 模型设置按钮）
> - 模型选择弹窗组件（预设4大提供商 + 自定义）
> - 后端提供商/模型管理 API（CRUD + 模型列表发现）
> - 后端配置扩展（保存语言/OCR模型/翻译模型选择）
> 
> **Estimated Effort**: Medium
> **Parallel Execution**: YES - 3 waves
> **Critical Path**: T1 → T3 → T5 → T6

---

## Context

### Original Request
主页，拖拽框向左移动，右侧加上下拉条。包括：文档语言（默认自动检测，可选英文、日文）、识别模型（根据用户设置）、翻译模型（根据用户设置）。上面加"模型设置"按钮，点击弹出窗口选择大模型。选择模型面板照搬 OpenCode 代码，预设提供商 + 自定义。

### Interview Summary
**Key Discussions**:
- 布局比例: 左侧60% / 右侧40%
- 预设提供商: Ollama, OpenAI, Anthropic, Google + 自定义
- 模型列表数据源: 后端 API 动态获取
- 设置持久化: 保存到后端数据库

**Research Findings**:
- 项目无测试基础设施 → 用户选择不设置自动化测试
- 现有 settings 页面仅处理 model_endpoint，需扩展
- FileUpload 组件当前居中，需重构为左侧布局

---

## Work Objectives

### Core Objective
改造主页为左右分栏布局，右侧提供文档处理配置面板，支持多模型提供商管理和动态模型选择。

### Concrete Deliverables
- `src/app/page.tsx` - 左右分栏主页布局
- `src/components/FileUpload.tsx` - 适配左侧布局的上传组件
- `src/components/SettingsPanel.tsx` - 右侧设置面板（3个下拉框 + 模型设置按钮）
- `src/components/ModelSettingsModal.tsx` - 模型选择弹窗
- `src/lib/providers.ts` - 预设提供商配置
- `src/lib/api.ts` - 新增 API 调用（提供商/模型/扩展配置）
- `xinda-backend/routers/providers.py` - 提供商/模型管理 API
- `xinda-backend/routers/config.py` - 扩展配置端点
- `xinda-backend/models/database.py` - 新增 Provider/Model 数据库表

### Definition of Done
- [x] 主页显示左右分栏布局，拖拽区在左(60%)，设置面板在右(40%)
- [x] 右侧面板包含：文档语言下拉（默认自动检测）、识别模型下拉、翻译模型下拉
- [x] "模型设置"按钮点击弹出模型选择面板
- [x] 模型选择面板支持 Ollama/OpenAI/Anthropic/Google 预设 + 自定义提供商
- [x] 所有设置保存到后端数据库，刷新页面后恢复
- [ ] 上传文件时携带当前选择的配置参数

### Must Have
- 左右分栏布局 60/40
- 三个下拉框：文档语言、识别模型、翻译模型
- 模型设置弹窗（预设4提供商 + 自定义）
- 后端 API 支持提供商 CRUD 和模型列表
- 配置持久化到数据库

### Must NOT Have (Guardrails)
- 不修改现有 result 页面逻辑
- 不删除现有 settings 页面（保留但可后续废弃）
- 不引入新的 UI 库（仅用 Tailwind CSS）
- 不改变现有上传/处理流程的核心逻辑

---

## Verification Strategy

### Test Decision
- **Infrastructure exists**: NO
- **Automated tests**: None
- **Agent-Executed QA**: ALWAYS (mandatory for all tasks)

### QA Policy
Every task MUST include agent-executed QA scenarios.
Evidence saved to `.sisyphus/evidence/task-{N}-{scenario-slug}.{ext}`.

- **Frontend/UI**: Use Playwright — Navigate, interact, assert DOM, screenshot
- **API/Backend**: Use Bash (curl) — Send requests, assert status + response fields

---

## Execution Strategy

### Parallel Execution Waves

```
Wave 1 (Start Immediately — backend foundation + frontend scaffolding):
├── T1: Backend provider/model database models + API [deep]
├── T2: Backend config extension [quick]
├── T3: Frontend provider config + API layer [quick]
└── T4: Frontend SettingsPanel component [visual-engineering]

Wave 2 (After Wave 1 — modal + homepage integration):
├── T5: ModelSettingsModal component [visual-engineering]
└── T6: Homepage layout integration [visual-engineering]

Wave FINAL (After ALL tasks — 4 parallel reviews):
├── F1: Plan compliance audit [oracle]
├── F2: Code quality review [unspecified-high]
├── F3: Real manual QA [unspecified-high]
└── F4: Scope fidelity check [deep]

Critical Path: T1 → T3 → T4 → T6
                T2 ─┘
Parallel Speedup: ~60% faster than sequential
Max Concurrent: 4 (Wave 1)
```

### Dependency Matrix

- **T1**: None — T2, T3
- **T2**: T1 — T6
- **T3**: T1 — T4, T5
- **T4**: T3 — T6
- **T5**: T3 — T6
- **T6**: T2, T4, T5 — F1-F4

### Agent Dispatch Summary

- **Wave 1**: **4** — T1 → `deep`, T2 → `quick`, T3 → `quick`, T4 → `visual-engineering`
- **Wave 2**: **2** — T5 → `visual-engineering`, T6 → `visual-engineering`
- **FINAL**: **4** — F1 → `oracle`, F2 → `unspecified-high`, F3 → `unspecified-high`, F4 → `deep`

---

## TODOs

- [x] 1. Backend: Provider/Model Database Models + API

  **What to do**:
  - Create `Provider` and `ModelEntry` SQLAlchemy models in `models/database.py`
    - Provider: id, name (ollama/openai/anthropic/google/custom), display_name, base_url, api_key (encrypted), is_active, created_at
    - ModelEntry: id, provider_id, model_id (string like "gpt-4"), display_name, model_type (ocr/translate/both), is_default
  - Seed default providers: Ollama (base_url from env), OpenAI, Anthropic, Google (base_url only, no API key preset)
  - Seed default models per provider (e.g., Ollama: qwen2.5-vl, OpenAI: gpt-4o, Anthropic: claude-sonnet-4-5, Google: gemini-2.5-pro)
  - Create `routers/providers.py` with endpoints:
    - `GET /api/providers` — list all providers with their models
    - `POST /api/providers` — add custom provider (name, base_url, api_key)
    - `PUT /api/providers/{id}` — update provider
    - `DELETE /api/providers/{id}` — delete provider
    - `GET /api/providers/{id}/models` — list models for a provider (for Ollama, query /api/tags; for others, use seeded list)
    - `POST /api/providers/{id}/test` — test connection (ping base_url)
  - Register router in `main.py`

  **Must NOT do**:
  - Do not modify existing upload/process logic
  - Do not add authentication/authz

  **Recommended Agent Profile**:
  - **Category**: `deep`
    - Reason: Complex backend work involving database models, API design, and seeding logic
  - **Skills**: []
  - **Skills Evaluated but Omitted**:
    - `quick`: Too complex for quick category — involves multiple files and database design

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1 (with T2, T3, T4)
  - **Blocks**: T2, T3
  - **Blocked By**: None

  **References**:
  - `xinda-backend/models/database.py` - Existing database models (ProcessingHistory, Config) — follow same SQLAlchemy patterns
  - `xinda-backend/routers/config.py` - Existing router pattern — follow same structure for new providers router
  - `xinda-backend/main.py:27` - Router registration pattern — add providers router here
  - OpenCode providers docs: `https://opencode.ai/docs/providers/` - Provider configuration format for reference

  **Acceptance Criteria**:
  - [ ] `python -c "from models.database import Provider, ModelEntry; print('OK')"` → OK
  - [ ] `curl http://localhost:8000/api/providers` → 200, returns 4 default providers
  - [ ] `curl -X POST http://localhost:8000/api/providers -H "Content-Type: application/json" -d '{"name":"custom","display_name":"Custom","base_url":"http://example.com"}'` → 201, provider created
  - [ ] `curl http://localhost:8000/api/providers/1/models` → 200, returns model list

  **QA Scenarios**:

  ```
  Scenario: List default providers
    Tool: Bash (curl)
    Preconditions: Backend running, database migrated
    Steps:
      1. curl -s http://localhost:8000/api/providers
      2. Assert response contains "ollama", "openai", "anthropic", "google"
    Expected Result: 200 status, JSON array with 4 provider objects
    Failure Indicators: 500 error, missing providers, empty array
    Evidence: .sisyphus/evidence/task-1-list-providers.json

  Scenario: Add custom provider
    Tool: Bash (curl)
    Preconditions: Backend running
    Steps:
      1. curl -s -X POST http://localhost:8000/api/providers -H "Content-Type: application/json" -d '{"name":"custom-ai","display_name":"Custom AI","base_url":"http://custom.example.com/v1"}'
      2. Assert response contains "custom-ai" and id field
    Expected Result: 201 status, new provider object returned
    Evidence: .sisyphus/evidence/task-1-add-provider.json

  Scenario: Get models for Ollama provider
    Tool: Bash (curl)
    Preconditions: Backend running, Ollama provider exists (id=1)
    Steps:
      1. curl -s http://localhost:8000/api/providers/1/models
      2. Assert response contains model entries
    Expected Result: 200 status, array of model objects
    Evidence: .sisyphus/evidence/task-1-ollama-models.json

  Scenario: Delete provider
    Tool: Bash (curl)
    Preconditions: Custom provider exists
    Steps:
      1. curl -s -X DELETE http://localhost:8000/api/providers/{id}
      2. curl -s http://localhost:8000/api/providers
      3. Assert deleted provider no longer in list
    Expected Result: 200 status, provider removed from subsequent list
    Evidence: .sisyphus/evidence/task-1-delete-provider.json
  ```

  **Commit**: YES (groups with T2)
  - Message: `feat(backend): add provider/model management API`
  - Files: `models/database.py`, `routers/providers.py`, `main.py`
  - Pre-commit: `python -c "from routers import providers; print('OK')"`

- [x] 2. Backend: Config Extension

  **What to do**:
  - Extend `GET /api/config` to return: `model_endpoint`, `doc_language`, `ocr_model_id`, `translate_model_id`, `providers` (list)
  - Extend `POST /api/config` to accept: `doc_language`, `ocr_model_id`, `translate_model_id` (in addition to existing `model_endpoint`)
  - Store these in a new `AppConfig` database table (key-value pairs for simplicity)
  - Default values: doc_language="auto", ocr_model_id=null, translate_model_id=null

  **Must NOT do**:
  - Do not change existing model_endpoint behavior
  - Do not remove existing config endpoint signatures

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: Small extension to existing config logic — adding fields to existing pattern
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1 (with T1, T3, T4)
  - **Blocks**: T6
  - **Blocked By**: T1 (needs Provider model for providers list)

  **References**:
  - `xinda-backend/routers/config.py:79-91` - Existing config GET/POST endpoints — extend these
  - `xinda-backend/models/database.py` - Add AppConfig table following existing model patterns

  **Acceptance Criteria**:
  - [ ] `curl http://localhost:8000/api/config` → returns doc_language, ocr_model_id, translate_model_id fields
  - [ ] `curl -X POST http://localhost:8000/api/config -H "Content-Type: application/json" -d '{"doc_language":"en","ocr_model_id":"openai/gpt-4o"}'` → 200, config saved
  - [ ] Subsequent GET returns saved values

  **QA Scenarios**:

  ```
  Scenario: Get extended config with defaults
    Tool: Bash (curl)
    Preconditions: Backend running, fresh database
    Steps:
      1. curl -s http://localhost:8000/api/config
      2. Assert response contains doc_language="auto", ocr_model_id=null, translate_model_id=null
    Expected Result: 200 status, JSON with all config fields including defaults
    Evidence: .sisyphus/evidence/task-2-get-config-defaults.json

  Scenario: Update config
    Tool: Bash (curl)
    Preconditions: Backend running
    Steps:
      1. curl -s -X POST http://localhost:8000/api/config -H "Content-Type: application/json" -d '{"doc_language":"ja","ocr_model_id":"ollama/qwen2.5-vl","translate_model_id":"openai/gpt-4o"}'
      2. curl -s http://localhost:8000/api/config
      3. Assert saved values match
    Expected Result: 200 on POST, GET returns saved values
    Evidence: .sisyphus/evidence/task-2-update-config.json
  ```

  **Commit**: YES (groups with T1)
  - Message: `feat(backend): add provider/model management API`
  - Files: `routers/config.py`, `models/database.py`

- [x] 3. Frontend: Provider Config + API Layer

  **What to do**:
  - Create `src/lib/providers.ts` with:
    - Provider interface: `{ id, name, display_name, base_url, api_key?, is_active, models: ModelEntry[] }`
    - ModelEntry interface: `{ id, model_id, display_name, model_type, is_default }`
    - PRESET_PROVIDERS constant with Ollama, OpenAI, Anthropic, Google configs (icons, names, base_url patterns)
  - Extend `src/lib/api.ts` with:
    - `getProviders(): Promise<Provider[]>` — GET /api/providers
    - `createProvider(data): Promise<Provider>` — POST /api/providers
    - `updateProvider(id, data): Promise<Provider>` — PUT /api/providers/{id}
    - `deleteProvider(id): Promise<void>` — DELETE /api/providers/{id}
    - `getProviderModels(id): Promise<ModelEntry[]>` — GET /api/providers/{id}/models
    - `getExtendedConfig(): Promise<ExtendedConfig>` — GET /api/config (extended)
    - `updateExtendedConfig(data): Promise<void>` — POST /api/config (extended)

  **Must NOT do**:
  - Do not modify existing API functions
  - Do not add UI components here (only types and API calls)

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: Pure TypeScript types and API wrapper functions — straightforward additions
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1 (with T1, T2, T4)
  - **Blocks**: T4, T5
  - **Blocked By**: T1 (needs API endpoint structure)

  **References**:
  - `src/lib/api.ts` - Existing API pattern — follow same axios.create + function pattern
  - `src/lib/api.ts:34-51` - Existing interface definitions — follow same TypeScript pattern

  **Acceptance Criteria**:
  - [ ] `npx tsc --noEmit` passes with new types and functions
  - [ ] All new API functions follow existing axios pattern

  **QA Scenarios**:

  ```
  Scenario: TypeScript compilation
    Tool: Bash (npx tsc)
    Preconditions: Frontend dependencies installed
    Steps:
      1. cd xinda-frontend && npx tsc --noEmit
      2. Assert exit code 0, no errors
    Expected Result: Clean compilation, zero errors
    Evidence: .sisyphus/evidence/task-3-tsc-output.txt
  ```

  **Commit**: YES (groups with T4)
  - Message: `feat(frontend): add provider config and settings panel`
  - Files: `src/lib/providers.ts`, `src/lib/api.ts`

- [x] 4. Frontend: SettingsPanel Component

  **What to do**:
  - Create `src/components/SettingsPanel.tsx`
  - Layout: vertical card with header "处理设置" + "模型设置" button
  - Three dropdown sections:
    1. **文档语言**: `<select>` with options: 自动检测 (auto), 英文 (en), 日文 (ja). Default: auto
    2. **识别模型**: `<select>` populated from `getProviders()` → flatten all models of type "ocr" or "both". Show as "Provider / Model" format. Default: first available
    3. **翻译模型**: `<select>` populated from `getProviders()` → flatten all models of type "translate" or "both". Default: first available
  - On mount: fetch config, set dropdown values
  - On change: call `updateExtendedConfig()` to persist
  - "模型设置" button: calls `onOpenModelSettings()` callback (passed as prop)
  - Styling: Tailwind CSS, clean card design matching existing app style

  **Must NOT do**:
  - Do not implement the modal itself (that's T5)
  - Do not modify FileUpload component
  - Do not add complex form validation beyond basic select

  **Recommended Agent Profile**:
  - **Category**: `visual-engineering`
    - Reason: UI component requiring clean design, dropdown styling, and responsive layout
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1 (with T1, T2, T3)
  - **Blocks**: T6
  - **Blocked By**: T3 (needs API functions and types)

  **References**:
  - `src/app/settings/page.tsx` - Existing settings page styling — match the same visual language
  - `src/components/FileUpload.tsx` - Existing component patterns (useState, useCallback usage)
  - `src/app/globals.css` - Global styles to ensure consistency

  **Acceptance Criteria**:
  - [ ] Component renders with 3 dropdowns and "模型设置" button
  - [ ] Dropdowns populate from API on mount
  - [ ] Changing dropdown value persists to backend
  - [ ] "模型设置" button triggers callback

  **QA Scenarios**:

  ```
  Scenario: SettingsPanel renders with default values
    Tool: Playwright
    Preconditions: Backend running with default config, frontend running
    Steps:
      1. Navigate to http://localhost:3000
      2. Wait for SettingsPanel to render (selector: [data-testid="settings-panel"])
      3. Assert "文档语言" dropdown shows "自动检测"
      4. Assert "识别模型" dropdown has options
      5. Assert "翻译模型" dropdown has options
      6. Assert "模型设置" button is visible
    Expected Result: Panel renders with all 3 dropdowns populated and button visible
    Failure Indicators: Empty dropdowns, panel not rendering, missing button
    Evidence: .sisyphus/evidence/task-4-settings-panel-render.png

  Scenario: Change document language persists
    Tool: Playwright
    Preconditions: SettingsPanel rendered
    Steps:
      1. Select "英文" from 文档语言 dropdown
      2. Wait 500ms for API call
      3. Refresh page
      4. Assert 文档语言 dropdown still shows "英文"
    Expected Result: Selection persists after page refresh
    Evidence: .sisyphus/evidence/task-4-language-persist.png
  ```

  **Commit**: YES (groups with T3)
  - Message: `feat(frontend): add provider config and settings panel`
  - Files: `src/components/SettingsPanel.tsx`, `src/lib/providers.ts`, `src/lib/api.ts`

---

- [x] 5. Frontend: ModelSettingsModal Component

  **What to do**:
  - Create `src/components/ModelSettingsModal.tsx`
  - Modal overlay: full-screen semi-transparent backdrop, centered panel (max-w-2xl)
  - Panel structure:
    - Header: "模型设置" + close button (×)
    - Tab/Section: "预设提供商" — grid of provider cards (Ollama, OpenAI, Anthropic, Google)
      - Each card shows: provider icon, name, status (connected/not), "选择" button
      - Clicking a provider expands to show its models as selectable radio buttons
    - Section: "自定义提供商" — form to add custom provider
      - Fields: 提供商名称, API 地址 (base_url), API 密钥 (optional), 测试连接按钮
      - "添加" button to save
    - Section: "已添加的自定义提供商" — list with edit/delete actions
  - State management:
    - `isOpen` controlled by parent via prop
    - `onClose` callback
    - Fetch providers on mount, refresh after add/edit/delete
  - Test connection: call `POST /api/providers/{id}/test`, show success/error toast
  - Styling: Tailwind CSS, modal with backdrop blur, smooth transitions

  **Must NOT do**:
  - Do not implement provider backend logic (already in T1)
  - Do not add settings to the main SettingsPanel (this is a separate modal)
  - Do not use external modal libraries — implement with pure React + Tailwind

  **Recommended Agent Profile**:
  - **Category**: `visual-engineering`
    - Reason: Complex UI component with modal, tabs, forms, and interactive cards
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 2 (with T6)
  - **Blocks**: T6
  - **Blocked By**: T3 (needs API functions and provider types)

  **References**:
  - `src/lib/providers.ts` - Provider types and PRESET_PROVIDERS constant
  - `src/lib/api.ts` - Provider CRUD API functions
  - `src/components/SettingsPanel.tsx` - Styling patterns to match

  **Acceptance Criteria**:
  - [ ] Modal opens/closes correctly
  - [ ] Preset providers displayed as cards
  - [ ] Clicking preset provider shows its models
  - [ ] Custom provider form works (add, test, delete)
  - [ ] Test connection shows result feedback

  **QA Scenarios**:

  ```
  Scenario: Open and close modal
    Tool: Playwright
    Preconditions: Frontend running, SettingsPanel rendered
    Steps:
      1. Navigate to http://localhost:3000
      2. Click "模型设置" button (selector: button containing "模型设置")
      3. Assert modal appears (selector: [data-testid="model-settings-modal"])
      4. Assert backdrop is visible
      5. Click close button (selector: button with × or "Close")
      6. Assert modal disappears
    Expected Result: Modal opens with backdrop, closes on button click
    Evidence: .sisyphus/evidence/task-5-modal-open-close.png

  Scenario: View preset providers
    Tool: Playwright
    Preconditions: Modal open, backend running with seeded providers
    Steps:
      1. Assert modal shows cards for "Ollama", "OpenAI", "Anthropic", "Google"
      2. Click "Ollama" card
      3. Assert Ollama models expand and show as selectable options
    Expected Result: 4 provider cards visible, clicking one expands model list
    Evidence: .sisyphus/evidence/task-5-preset-providers.png

  Scenario: Add custom provider
    Tool: Playwright
    Preconditions: Modal open
    Steps:
      1. Scroll to "自定义提供商" section
      2. Fill 提供商名称: "My Custom"
      3. Fill API 地址: "http://custom.example.com/v1"
      4. Click "测试连接" button
      5. Assert connection result shown (success or error message)
      6. Click "添加" button
      7. Assert new provider appears in list
    Expected Result: Custom provider added and visible in provider list
    Evidence: .sisyphus/evidence/task-5-add-custom-provider.png

  Scenario: Delete custom provider
    Tool: Playwright
    Preconditions: Custom provider exists in list
    Steps:
      1. Find custom provider card
      2. Click delete button on that card
      3. Assert confirmation or immediate deletion
      4. Assert provider no longer in list
    Expected Result: Provider removed from list
    Evidence: .sisyphus/evidence/task-5-delete-provider.png
  ```

  **Commit**: YES (groups with T6)
  - Message: `feat(frontend): add model settings modal and homepage layout`
  - Files: `src/components/ModelSettingsModal.tsx`

- [x] 6. Frontend: Homepage Layout Integration

  **What to do**:
  - Modify `src/app/page.tsx` to implement 60/40 split layout:
    - Container: `flex` with `gap-6`
    - Left (60%): FileUpload component, wrapped in `w-[60%]` or `flex-[3]`
    - Right (40%): SettingsPanel component, wrapped in `w-[40%]` or `flex-[2]`
  - Add state management:
    - `showModelModal` boolean state
    - `onOpenModelSettings` callback to open modal
  - Import and render ModelSettingsModal with `isOpen` and `onClose` props
  - Modify FileUpload to accept optional `config` prop (doc_language, ocr_model, translate_model) and pass these with the upload request
  - Update upload API call to include config parameters in the FormData or as query params
  - Ensure responsive behavior: on mobile (<768px), stack vertically

  **Must NOT do**:
  - Do not change FileUpload's core upload logic
  - Do not modify HistoryList component
  - Do not change the routing behavior after upload

  **Recommended Agent Profile**:
  - **Category**: `visual-engineering`
    - Reason: Layout integration work requiring flexbox, responsive design, and component composition
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES (but depends on T2, T4, T5)
  - **Parallel Group**: Wave 2 (with T5)
  - **Blocks**: F1-F4
  - **Blocked By**: T2 (config API), T4 (SettingsPanel), T5 (ModelSettingsModal)

  **References**:
  - `src/app/page.tsx` - Current homepage — will be restructured
  - `src/components/FileUpload.tsx` - Upload component to integrate on left side
  - `src/components/HistoryList.tsx` - Keep below the split layout
  - `src/lib/api.ts:53-64` - uploadFile function — may need to add config params

  **Acceptance Criteria**:
  - [ ] Homepage shows 60/40 split on desktop
  - [ ] Left side has FileUpload drag-drop area
  - [ ] Right side has SettingsPanel with 3 dropdowns
  - [ ] "模型设置" button opens modal
  - [ ] On mobile, layout stacks vertically
  - [ ] HistoryList still renders below the split area

  **QA Scenarios**:

  ```
  Scenario: Desktop layout 60/40 split
    Tool: Playwright
    Preconditions: Frontend running, backend running
    Steps:
      1. Navigate to http://localhost:3000 with viewport 1280x720
      2. Assert page has two-column layout (flex container)
      3. Assert left column contains FileUpload (selector: input[type="file"])
      4. Assert right column contains SettingsPanel (selector: [data-testid="settings-panel"])
      5. Measure column widths: left ~60%, right ~40%
    Expected Result: Two-column layout with correct proportions
    Evidence: .sisyphus/evidence/task-6-desktop-layout.png

  Scenario: Mobile responsive stack
    Tool: Playwright
    Preconditions: Frontend running
    Steps:
      1. Navigate to http://localhost:3000 with viewport 375x667 (mobile)
      2. Assert layout stacks vertically (flex-col)
      3. Assert FileUpload appears above SettingsPanel
    Expected Result: Single column vertical stack on mobile
    Evidence: .sisyphus/evidence/task-6-mobile-layout.png

  Scenario: Full flow — settings + upload
    Tool: Playwright
    Preconditions: Frontend and backend running
    Steps:
      1. Navigate to http://localhost:3000
      2. Change 文档语言 to "日文"
      3. Click "模型设置" button
      4. Assert modal opens
      5. Close modal
      6. Verify SettingsPanel dropdowns retain selections
    Expected Result: Settings persist, modal opens/closes correctly
    Evidence: .sisyphus/evidence/task-6-settings-flow.png

  Scenario: HistoryList still visible below
    Tool: Playwright
    Preconditions: Frontend running, some history exists
    Steps:
      1. Navigate to http://localhost:3000
      2. Scroll down
      3. Assert HistoryList component renders below the split layout
    Expected Result: HistoryList visible and functional below upload/settings area
    Evidence: .sisyphus/evidence/task-6-history-below.png
  ```

  **Commit**: YES (groups with T5)
  - Message: `feat(frontend): add model settings modal and homepage layout`
  - Files: `src/app/page.tsx`, `src/components/ModelSettingsModal.tsx`

---

## Final Verification Wave (MANDATORY — after ALL implementation tasks)

> 4 review agents run in PARALLEL. ALL must APPROVE. Present consolidated results to user and get explicit "okay" before completing.

- [ ] F1. **Plan Compliance Audit** — `oracle`
  Read the plan end-to-end. For each "Must Have": verify implementation exists. For each "Must NOT Have": search codebase for forbidden patterns. Check evidence files exist. Compare deliverables against plan.
  Output: `Must Have [N/N] | Must NOT Have [N/N] | Tasks [N/N] | VERDICT: APPROVE/REJECT`

- [ ] F2. **Code Quality Review** — `unspecified-high`
  Run `tsc --noEmit` + linter. Review all changed files for: `as any`/`@ts-ignore`, empty catches, console.log in prod, commented-out code, unused imports. Check AI slop: excessive comments, over-abstraction, generic names.
  Output: `Build [PASS/FAIL] | Lint [PASS/FAIL] | Files [N clean/N issues] | VERDICT`

- [ ] F3. **Real Manual QA** — `unspecified-high` (+ `playwright` skill if UI)
  Start from clean state. Execute EVERY QA scenario from EVERY task. Test cross-task integration. Test edge cases: empty state, invalid input. Save to `.sisyphus/evidence/final-qa/`.
  Output: `Scenarios [N/N pass] | Integration [N/N] | Edge Cases [N tested] | VERDICT`

- [ ] F4. **Scope Fidelity Check** — `deep`
  For each task: read "What to do", read actual diff. Verify 1:1. Check "Must NOT do" compliance. Detect cross-task contamination. Flag unaccounted changes.
  Output: `Tasks [N/N compliant] | Contamination [CLEAN/N issues] | Unaccounted [CLEAN/N files] | VERDICT`

---

## Commit Strategy

- **Wave 1**: `feat(backend): add provider/model management API` — T1, T2
- **Wave 1**: `feat(frontend): add provider config and settings panel` — T3, T4
- **Wave 2**: `feat(frontend): add model settings modal and homepage layout` — T5, T6

---

## Success Criteria

### Verification Commands
```bash
cd xinda-frontend && npx tsc --noEmit  # Expected: No errors
cd xinda-backend && python -c "from routers import providers, config; print('OK')"  # Expected: OK
curl http://localhost:8000/api/providers  # Expected: 200 with provider list
curl http://localhost:8000/api/config     # Expected: 200 with extended config
```

### Final Checklist
- [ ] All "Must Have" present
- [ ] All "Must NOT Have" absent
- [ ] TypeScript compiles without errors
- [ ] Backend imports without errors
- [ ] All QA scenarios pass
