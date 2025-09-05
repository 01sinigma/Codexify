# Codexify

Codexify is a tool for developers to collect, analyze, and manage code from various sources within a project. It is built with a clean, API-oriented core ("Engine") that separates business logic from the user interface, allowing for flexible client implementations (GUI, CLI).

## Project Status

**Current Version:** v0.5.x (Final Polish in progress)

This version adds comprehensive testing infrastructure, developer documentation, user guides, and code quality tools, making Codexify a production-ready application with professional development practices.

### Completed Milestones

#### ✅ Branch 1: "Engine Core & State Management" (v0.1)
- **Project Structure:** The full directory and file structure has been created according to the development plan.
- **State Management (`state.py`):** A central `CodexifyState` dataclass has been implemented to act as the single source of truth for the application's state.
- **Event System (`events.py`):** An `EventManager` based on the Observer pattern has been created to enable decoupled communication between components.
- **Core Engine (`engine.py`):** The main `CodexifyEngine` class has been implemented. It orchestrates the application's logic, manages the state, and exposes a clear API for clients.
- **Core Logic Modules (`core/`):** Placeholder modules for `scanner.py` and `builder.py` have been created to define the core functionalities of scanning directories and building output files.
- **Entry Point Simulation (`run_gui.py`):** A simulation script has been created to demonstrate how a client (like a GUI) interacts with the engine's API and subscribes to its events.

#### ✅ Stage 1: Enhanced Engine Core (v0.2)
- **Advanced Scanner (`scanner.py`):** Full implementation with `.codexignore` support, binary file detection, size filtering, and comprehensive error handling.
- **Enhanced Builder (`builder.py`):** Multi-format output support (TXT, Markdown, HTML), metadata inclusion, encoding detection, and professional formatting.
- **Improved Engine (`engine.py`):** Background processing for long operations, real file classification logic, comprehensive error handling, and state management.
- **Functional GUI (`main_window.py`):** Complete interface with format management, file moving between lists, output format selection, and real-time updates.
- **Configuration (`codexignore`):** Comprehensive ignore patterns for common development artifacts.

#### ✅ Stage 2: Enhanced GUI & Analytics (v0.3)
- **Comprehensive Analytics (`analyzer.py`):** Full project analysis including language detection, file categorization, code quality metrics, and structural analysis.
- **Duplicate Detection (`duplicate_finder.py`):** Advanced duplicate finding using hash comparison, content analysis, and similarity matching.
- **Enhanced Engine Integration:** Full integration of analytics and duplicate detection modules with background processing.
- **Improved GUI:** Added analysis and duplicate detection buttons with progress indicators and result displays.
- **Command Line Interface (`cli.py`):** Complete CLI demonstrating API flexibility with commands for all major operations.

#### ✅ Stage 3: Systems & Polish (v0.4)
- **Configuration Management (`config_manager.py`):** Comprehensive settings management with presets, themes, templates, and validation.
- **Achievement System (`achievement_system.py`):** Gamification system with 25+ achievements across 7 categories, progress tracking, and statistics.
- **Hotkey Management (`hotkey_manager.py`):** Flexible keyboard shortcut system with profiles, conflict detection, and Tkinter integration.
- **System Integration:** All systems fully integrated into the engine with unified API and event handling.
- **Enhanced Engine:** Configuration-driven behavior, preset management, and comprehensive system coordination.

#### ✅ Stage 4: Testing & Documentation (v0.5)
- **Comprehensive Test Suite (`tests/`)**: Complete testing infrastructure with pytest, fixtures, and test utilities.
- **Unit Tests**: Thorough testing of all core modules including state management, events, scanner, and configuration systems.
- **Test Runner (`run_tests.py`)**: Professional test runner with multiple testing modes, coverage reporting, and quality checks.
- **Developer Documentation (`docs/DEVELOPER.md`)**: Complete development guide with architecture overview, setup instructions, and contribution guidelines.
- **User Guide (`docs/USER_GUIDE.md`)**: Comprehensive user documentation with tutorials, examples, and troubleshooting.
- **Code Quality Tools**: Integration with flake8, black, isort, and coverage tools for professional code standards.
- **Testing Configuration**: Pytest configuration with custom markers, coverage settings, and reporting options.

## Architecture: Engine + Clients

The core concept is an "Engine + Clients" architecture.

*   **The Engine (`codexify/engine.py`)**: This is the heart of the application.
    *   **Holds State**: Manages all session information (project path, file lists, etc.) via the `CodexifyState` object.
    *   **Provides API**: Exposes public methods like `load_project()`, `set_active_formats()`, `move_files()`, `collect_code()`, `get_analytics()`, `find_duplicates()`, etc.
    *   **Manages Logic**: Uses "worker" modules (e.g., `scanner.py`, `builder.py`, `analyzer.py`, `duplicate_finder.py`) to perform tasks.
    *   **Signals Changes**: Notifies subscribers (clients) of state changes using the `EventManager`.
    *   **Background Processing**: Handles long-running operations in separate threads to keep the UI responsive.
    *   **System Coordination**: Manages configuration, achievements, and hotkeys through integrated systems.

*   **The Clients (`codexify/clients/`)**: These are the shells that interact with the engine.
    *   **GUI (`gui/`)**: A graphical interface that displays the engine's state and calls its API. It does not hold its own state.
    *   **CLI (`cli.py`)**: A command-line interface that uses the same engine to perform tasks in a console environment.

*   **The Systems (`codexify/systems/`)**: These provide auxiliary functionality to the engine.
    *   **Configuration Manager**: Handles settings, presets, themes, and templates.
    *   **Achievement System**: Tracks user progress and awards achievements.
    *   **Hotkey Manager**: Manages keyboard shortcuts and profiles.

*   **The Testing (`tests/`)**: This provides comprehensive testing infrastructure.
    *   **Test Suite**: Complete testing of all modules and systems.
    *   **Fixtures**: Reusable test data and setup utilities.
    *   **Quality Tools**: Integration with professional testing and code quality tools.

This design ensures that business logic is centralized and reusable, making the application easy to maintain, test, and extend.

## Current Features

### 🔍 **Smart File Scanning**
- Recursive directory scanning with `.codexignore` support
- Automatic binary file detection and filtering
- Configurable file size limits and depth restrictions
- Comprehensive error handling and reporting

### 📁 **Intelligent File Classification**
- Automatic categorization based on file extensions
- Dynamic reclassification when formats change
- Support for custom file formats
- Real-time file list updates

### 🎯 **Format Management**
- Pre-configured common development file formats
- Custom format addition
- Real-time filtering and classification
- Visual format selection interface

### 📝 **Multi-Format Output**
- **Plain Text**: Simple, readable format with metadata
- **Markdown**: Structured documentation with code blocks
- **HTML**: Professional web-ready output with styling
- Metadata inclusion (file size, modification date, encoding)

### 🖱️ **Interactive GUI**
- Drag-and-drop style file management
- Real-time status updates
- Format selection checkboxes
- File movement between include/other lists
- Output format selection
- Project analysis and duplicate detection buttons
- Progress indicators and result displays

### ⚡ **Performance Features**
- Background processing for long operations
- Non-blocking UI during file operations
- Efficient file handling and memory management
- Progress reporting and status updates

### 📊 **Advanced Analytics**
- **Language Detection**: Automatic identification of 30+ programming languages
- **File Categorization**: Smart classification into code, markup, styling, config, etc.
- **Code Quality Metrics**: Comment ratios, empty line analysis, code density
- **Structural Analysis**: Directory depth, file distribution, complexity metrics
- **Size Distribution**: Categorization by file size ranges

### 🔍 **Duplicate Detection**
- **Exact Duplicates**: Hash-based file comparison
- **Code Block Analysis**: Duplicate code segment detection
- **Similarity Matching**: Fuzzy content similarity using difflib
- **Configurable Methods**: Choose detection algorithms
- **Comprehensive Reporting**: Detailed duplicate group analysis

### 💻 **Command Line Interface**
- **Full API Access**: All engine functionality available via CLI
- **Batch Operations**: Chain commands for automation
- **Rich Output**: Formatted analysis and duplicate results
- **Error Handling**: Comprehensive error reporting and recovery

### ⚙️ **Configuration Management**
- **Centralized Settings**: All application settings in one place
- **Preset System**: Save and load configuration presets
- **Theme Management**: Customizable UI themes and colors
- **Template System**: Output format templates for different use cases
- **Validation**: Automatic configuration validation and error checking
- **Import/Export**: Share configurations between installations

### 🏆 **Achievement System**
- **25+ Achievements**: Across 7 categories (Projects, Files, Analysis, Duplicates, Collection, Efficiency, Exploration)
- **Progress Tracking**: Automatic tracking of user actions and milestones
- **Point System**: Earn points for completing tasks and unlocking achievements
- **Statistics**: Comprehensive user statistics and progress metrics
- **Gamification**: Encourages exploration and mastery of the application

### ⌨️ **Hotkey Management**
- **Default Shortcuts**: Pre-configured shortcuts for common actions
- **Custom Bindings**: Create and modify keyboard shortcuts
- **Profile System**: Save and load different hotkey configurations
- **Conflict Detection**: Automatic detection of conflicting key combinations
- **Category Organization**: Organized by function (File, Analysis, Navigation, View, etc.)
- **Tkinter Integration**: Seamless integration with the GUI

### 🧪 **Testing Infrastructure**
- **Comprehensive Test Suite**: Unit tests for all core modules and systems
- **Professional Test Runner**: Advanced test runner with multiple modes and reporting
- **Code Coverage**: Detailed coverage reporting with HTML and XML output
- **Quality Tools**: Integration with flake8, black, isort for code quality
- **Test Fixtures**: Reusable test data and setup utilities
- **Custom Markers**: Organized testing with custom pytest markers

### 📚 **Documentation**
- **Developer Guide**: Complete development documentation with architecture overview
- **User Guide**: Comprehensive user documentation with tutorials and examples
- **API Documentation**: Detailed API reference for all public methods
- **Testing Guide**: Complete testing documentation and best practices
- **Contribution Guidelines**: Clear guidelines for contributors and maintainers

### 🚀 **Performance Systems**
- **Performance Profiling**: Comprehensive execution time and memory usage tracking
- **Memory Optimization**: Advanced memory monitoring, leak detection, and GC optimization
- **Intelligent Caching**: Multi-level caching for files, analysis results, and persistent data
- **Parallel Processing**: Thread and process-based parallel execution for I/O and CPU operations
- **Performance Benchmarking**: Automated benchmarking with optimization recommendations
- **Unified Performance Management**: Centralized control and monitoring of all performance systems

### 🎨 **Modern UI/UX System**
- **Enhanced Widgets**: Modern file lists with search, filtering, and context menus
- **Advanced Format Selector**: Categorized file format selection with search capabilities
- **Smart Search**: Real-time file search with autocomplete and result navigation
- **Progress Tracking**: Animated progress indicators with detailed status information
- **Status Management**: Enhanced status bar with icons, progress, and file counts
- **Responsive Layout**: Adaptive interface with proper spacing and modern styling
- **Theme System**: Consistent color scheme and typography across all components

## Next Steps

**Этап 5: Performance & Optimization (v0.6) - ЗАВЕРШЕН! ✅**

### 🚀 Performance Profiling
- **PerformanceProfiler** - система профилирования производительности
- **Execution Time Measurement** - измерение времени выполнения операций
- **Memory Usage Tracking** - отслеживание использования памяти
- **Bottleneck Identification** - выявление узких мест
- **Performance Metrics** - метрики производительности

### 💾 Memory Optimization
- **MemoryMonitor** - мониторинг использования памяти
- **MemoryOptimizer** - оптимизация памяти и сборка мусора
- **WeakReferenceManager** - управление слабыми ссылками
- **Memory Leak Detection** - обнаружение утечек памяти
- **Garbage Collection Optimization** - оптимизация сборки мусора

### 🗄️ Caching Strategies
- **FileContentCache** - кэширование содержимого файлов
- **AnalysisResultCache** - кэширование результатов анализа
- **PersistentCache** - персистентное кэширование
- **Cache Policies** - политики кэширования
- **Intelligent Invalidation** - интеллектуальная инвалидация

### ⚡ Parallel Processing
- **ParallelProcessor** - система параллельной обработки
- **FileProcessor** - параллельная обработка файлов
- **AnalysisProcessor** - параллельный анализ
- **Task Queue Management** - управление очередью задач
- **Worker Pool Management** - управление пулом воркеров

### 📊 Benchmarking
- **BenchmarkRunner** - система бенчмаркинга
- **CodexifyBenchmarks** - предустановленные бенчмарки
- **Performance Comparison** - сравнение производительности
- **Optimization Recommendations** - рекомендации по оптимизации
- **Results Export** - экспорт результатов

### 🎯 Performance Management
- **PerformanceManager** - единый интерфейс управления производительностью
- **Unified Configuration** - единая конфигурация всех систем
- **Performance Reports** - отчеты о производительности
- **Auto-optimization** - автоматическая оптимизация
- **Performance Scoring** - оценка производительности

### 🧪 Performance Testing
- **run_performance_tests.py** - скрипт для тестирования производительности
- **Comprehensive Testing** - тестирование всех систем производительности
- **Benchmark Execution** - выполнение бенчмарков
- **Results Export** - экспорт результатов тестирования

---

## Следующий этап: Final Polish & Release (v1.0)

**Этап 6: Final Polish & Release (v1.0)** будет включать:
1. **UI/UX Improvements** - финальные улучшения интерфейса ✅ **ЗАВЕРШЕНО!**
2. **Performance Tuning** - тонкая настройка производительности ✅ **ЗАВЕРШЕНО!**
3. **Bug Fixes** - исправление найденных ошибок ✅ **ЗАВЕРШЕНО!**
4. **Documentation Updates** - обновление документации
5. **Release Preparation** - подготовка к релизу
6. **Final Testing** - финальное тестирование

### Recent Additions (v0.5.x)
- Path Presets: save/apply/delete presets of absolute file paths for quick Include/Other population (GUI: Command Palette → Path Preset actions).
- Collect Output Headers: collected files now include full absolute path as a header before each file’s content (TXT/MD/HTML); a separate "Other files" section lists non-included files by full path without code.
- Portable Build: PyInstaller onefile builds for GUI and CLI with a portable runtime hook that keeps logs/presets/templates next to the executable.
- Inline Preview: preview panel shows full path and snippet of selected file; wrap/nowrap to be added.
- Advanced Filters: type + Min/Max KB, hide hidden files, saved filters per list.
- Workspaces: save/load/delete full UI state (formats, layout, lists, project path).
- Tags & Notes: add tags and notes to files via context menu.
- Pattern Selection: select by same extension or glob/substring pattern from context menu.
- Bundle Export/Import: export format/path presets, saved filters, layout and active formats; import and apply in one шаг.
- Watch Mode: optional auto-refresh of project state with configurable interval (UI → Command Palette).
- Context-aware Command Palette: показывает релевантные действия для списков файлов (выбор по расширению/паттерну, пресеты, workspaces, bundle, watch).
- Logs Viewer: кнопка в левом нижнем углу открывает окно логов (поиск/подсветка, копирование, обновление).
- Instant Formats Reclassify: при изменении форматов файлы сразу переклассифицируются между Include/Other без задержки.

### New in v0.5.x (continued)
- Hotkeys Management: вкладка в Settings для просмотра/редактирования хоткеев, профили, экспорт/импорт.
- AI Worker: фоновые вызовы с прогрессом/отменой, кэш и rate‑limit в памяти.
- Analysis Filters: просмотр горячих файлов с фильтрами (min score, min size, Top N).
- Full Code Map: многоуровневая Mermaid‑карта (модули/классы/функции, импорты, локальные вызовы), легенда, настройки включения слоёв, навигация к файлам, HTML‑просмотр.
- Map UX: в HTML‑просмотре добавлены Zoom In/Out, Fit, Reset, панорамирование мышью, масштаб колесом, экспорт PNG (учитывает bbox и отступы), клики по узлам с подсказкой пути и кнопками Copy/Open.
- Map Fallback (JS/TS): если нет Python‑символов, строится карта файлов/папок со связями по `import`/`require` для *.js/*.ts/*.jsx/*.tsx.
- Safer IDs: идентификаторы узлов Mermaid санитизируются (A‑Z/0‑9/_), чтобы избежать ошибок парсера.
- Duplicates Settings: методы поиска, пороги и skip binary; AI‑план рефакторинга по группам.
- Volatile Mode: конфиг/пресеты/воркспейсы/хоткеи хранятся in‑memory; экспорт/импорт — по желанию пользователя.
- Tests: smoke‑тест анализа и карты, LLM‑моки, тесты индекса символов и импорт‑графа.

### Map: Advanced features (v0.5.x)
- Bookmarks: сохранение и применение ракурсов (камера/viewBox) прямо в HTML‑просмотрщике.
- Depth/Top‑N: ограничения по глубине от выделенного узла и по топ‑степени (центральности) для больших графов.
- Hover highlight: подсветка соседей при наведении, остальное приглушается.
- Collapse/expand уровней: быстрые чекбоксы слоёв (Dirs/Modules/Files/Classes/Functions, Imports/Calls).
- Minimap: мини‑обзор с прямоугольником текущего viewport; Fit to selection.
- Progressive loading: пошаговая отрисовка узлов/рёбер чанками (Chunk, Start/Stop) с прогресс‑баром; автостарт на больших графах.
- Context menu: Copy Path, Open (в системе), Fit to selection.
- Layout presets: Orientation (LR/TD/BT/RL), Node/Rank spacing с кнопкой Apply Layout.

### AI (к карте)
- AI Code Map: генерация обзорной карты по метаданным (пути, расширения, импорт‑пары) через LLM (OpenAI/Gemini).
- AI Explain Node: краткое описание роли выбранного узла, рисков и идей рефакторинга.
- AI Cluster Map: кластеризация подсистем — subgraph’ы и классы с цветами; открытие в HTML‑просмотрщике.

### LLM & AI (OpenAI/Gemini)
- LLM Settings (вкладка): выбор провайдера (`openai`/`gemini`/`custom`), модель, температура, max tokens, safe mode.
- Ключи API: поле `API Key (kept in-memory)` с кнопкой Paste (вставить из буфера), чекбоксом Show key (показать символы), кнопками `Save API` (сохранить в конфиг по запросу) и `Test API` (быстрый вызов `ping`).
- Переключение моделей: пресеты популярных моделей + динамическое обнаружение доступных моделей через публичные API при наличии ключа.
- Переменные окружения: если поле ключа пустое — читаем `OPENAI_API_KEY` (OpenAI) или `GEMINI_API_KEY` (Gemini).
- Логи LLM: успехи/ошибки, провайдер, модель, длина запроса — доступны в Logs Viewer.
- Gemini Thinking: поддержка опционального бюджета размышлений через `llm.gemini_thinking_budget` (0 — отключить).

#### AI Code Map: режимы и валидация
- **AI Map input (Settings → LLM)**:
  - **minimal**: отправляются только безопасные метаданные (относительные пути, гистограмма расширений, пары импортов для Python). Исходный код не отправляется.
  - **extended**: дополнительно передаётся лёгкая карта символов из анализа (modules/classes/functions) с усечением до безопасных лимитов.
- **Chunking/лимиты**: большие промпты автоматически укорачиваются (усечение списков), чтобы укладываться в контекст модели.
- **Валидация Mermaid**: ответ от LLM автоматически нормализуется (снятие markdown‑ограждений, нормализация стрелок, баланс `subgraph/end`). При невалидном синтаксисе выполняется одна попытка автопочинки/повторной генерации.
- **Логирование**: в логи пишется режим, размеры промпта/ответа, результат валидации и факт повторной попытки.

### UI Logging
- Добавлены логи на каждую ключевую кнопку/операцию GUI: выбор проекта, анализ, поиск дублей, открытие/сохранение настроек LLM, тест API, генерация карт и др. Все доступны через кнопку `Logs` внизу окна.

---

## How‑To: Настройка LLM

### OpenAI
1. Получите ключ на странице биллинга OpenAI и задайте переменную окружения:
   - Windows PowerShell: `setx OPENAI_API_KEY "sk-..."`
2. В GUI откройте `AI Settings` → вкладка `LLM`:
   - Provider: `openai`
   - Модель: выберите из списка (например, `gpt-4o-mini`) или введите вручную
   - При необходимости вставьте ключ через `Paste` и нажмите `Save API`
   - `Test API` для проверки

### Gemini
1. Получите ключ в Google AI Studio и задайте переменную окружения:
   - Windows PowerShell: `setx GEMINI_API_KEY "..."`
2. В GUI → `AI Settings` → `LLM`:
   - Provider: `gemini`
   - Модель: `gemini-1.5-flash`, `gemini-1.5-pro`, `gemini-2.5-flash` и др. (список обновляется динамически)
   - Вставьте ключ (или используйте переменную окружения), `Save API` и `Test API`
3. Опционально: установить `llm.gemini_thinking_budget=0` (отключить размышление) — значение хранится в памяти сессии.

### Custom HTTP
- Укажите `llm.custom_url` и модель, ключ будет добавлен как `Authorization: Bearer <key>`; тело запроса включает `prompt`, `system`, `temperature`, `max_tokens`.

---

## Mermaid‑карта: использование
1. Сгенерируйте карту: `Generate Full Code Map (Mermaid)`.
2. В модальном окне нажмите `Open HTML` для интерактивного просмотра.
3. Управление: Zoom In/Out, Fit, Reset; колесо — масштаб, зажатая ЛКМ — панорамирование.
4. Layers: чекбоксы Imports/Calls и слоёв (Dirs/Modules/Files/Classes/Functions).
5. Search: подсветка совпадений и приглушение прочих узлов.
6. Bookmarks: в панели инструментов — имя, Save View/Apply.
7. Depth/Top‑N: задайте значения и нажмите Apply Filter; Clear — сброс.
8. Progressive: при больших графах загрузка стартует автоматически; вручную — Chunk/Start/Stop.
9. `Export PNG/SVG/JSON` сохраняет соответствующие форматы.
10. Клик по узлу открывает подсказку пути и кнопки `Copy/Open`.
11. Контекст‑меню по узлу: Copy Path, Open, Fit selection.

---

## Changelog (2025‑08‑25)
- Исправлено: ошибки f‑string в HTML‑вьюере (полная конкатенация строки без фигурных скобок).
- Добавлено: подробные логи UI; логи LLM (успех/ошибки).
- Улучшено: HTML‑карта — пан/зум, экспорт PNG, подсказки, безопасные ID.
- Добавлено: fallback для JS/TS импортов и карта файлов.
- Улучшено: LLM Settings — Paste/Show key, Save API, Test API; динамические модели; поддержка env‑переменных.
- Новое: Bookmarks, Depth/Top‑N фильтры, Hover highlight, Collapse/expand уровней.
- Новое: Minimap и Fit to selection, Progressive loading с прогресс‑баром и Chunk‑контролем.
- Новое: AI Code Map, AI Explain Node, AI Cluster Map (Mermaid).

### Portable Build (Windows)
```powershell
pip install pyinstaller
# runtime hook at hooks/hook_portable.py already created
pyinstaller --noconfirm --clean --windowed --onefile run_gui.py \
  --name Codexify \
  --runtime-hook hooks/hook_portable.py \
  --hidden-import tkinterdnd2 \
  --collect-data tkinterdnd2 \
  --add-data templates:templates \
  --add-data presets:presets

pyinstaller --noconfirm --clean --onefile run_cli.py \
  --name Codexify-CLI \
  --runtime-hook hooks/hook_portable.py \
  --hidden-import tkinterdnd2 \
  --collect-data tkinterdnd2 \
  --add-data templates:templates \
  --add-data presets:presets
```

## Usage

### Running the GUI
```bash
cd codexify_project
python -m run_gui
```

### Running the CLI
```bash
cd codexify_project
python -m run_cli --help
```

### Running Tests
```bash
cd codexify_project

# Run all tests
python run_tests.py

# Run only unit tests
python run_tests.py --unit-only

# Run with coverage
python run_tests.py --coverage

# Run specific test file
python run_tests.py --test tests/test_state.py

# Run linting only
python run_tests.py --lint-only
```

### Basic CLI Workflow
```bash
# Scan a project
python -m run_cli scan /path/to/project

# Analyze the project
python -m run_cli analyze

# Find duplicates
python -m run_cli duplicates

# Set file formats and collect code
python -m run_cli formats .py .js .html
python -m run_cli collect output.txt --format md --metadata
```

### Basic GUI Workflow
1. **Load Project**: Click "Load Project" and select a directory
2. **Analyze**: Click "Analyze Project" for comprehensive insights
3. **Find Duplicates**: Click "Find Duplicates" to identify code duplication
4. **Select Formats**: Check/uncheck file formats you want to include
5. **Review Files**: Files are automatically classified into "Include" and "Other" lists
6. **Customize**: Move files between lists as needed
7. **Collect Code**: Choose output format and save location, then click "Collect Code"

### Configuration Management
```python
# Get configuration setting
max_file_size = engine.get_setting("scanning.max_file_size")

# Set configuration setting
engine.set_setting("ui.window_width", 1200)

# Create and load presets
engine.create_preset("web_dev", "Web development settings")
engine.load_preset("web_dev")

# Export/import configuration
engine.export_configuration("my_config.json")
engine.import_configuration("my_config.json")
```

### Achievement System
```python
# Get all achievements
achievements = engine.get_achievements()

# Get unlocked achievements
unlocked = engine.get_unlocked_achievements()

# Get progress summary
progress = engine.get_achievement_progress()

# Reset progress (for testing)
engine.reset_achievements()
```

### Hotkey Management
```python
# Get all hotkeys
hotkeys = engine.get_hotkeys()

# Get hotkeys by category
file_hotkeys = engine.get_hotkeys_by_category("file")

# Enable/disable hotkeys
engine.set_hotkey_enabled("open_project", False)

# Update hotkey binding
engine.update_hotkey("save_collection", "S", ["Ctrl", "Shift"])

# Check for conflicts
conflicts = engine.get_hotkey_conflicts()
```

### Testing and Development
```bash
# Install test dependencies
python run_tests.py --install-deps

# Run all quality checks
python run_tests.py

# Run specific test categories
python run_tests.py --unit-only
python run_tests.py --integration-only
python run_tests.py --lint-only

# Generate coverage report
python run_tests.py --coverage

# Run tests in parallel
python run_tests.py --parallel
```

### Supported File Formats
- **Code**: `.py`, `.js`, `.ts`, `.jsx`, `.tsx`, `.java`, `.cpp`, `.c`, `.cs`, `.php`, `.rb`, `.go`, `.rs`, `.swift`, `.kt`, `.scala`, `.sh`, `.bat`, `.ps1`
- **Markup**: `.html`, `.xml`, `.md`, `.rst`
- **Styling**: `.css`, `.scss`, `.less`
- **Config**: `.json`, `.yaml`, `.yml`, `.toml`, `.ini`
- **Documentation**: `.md`, `.txt`, `.rst`
- **Custom**: Add any file extension via the interface

### Output Formats
- **TXT**: Simple text with file separators and metadata
- **MD**: Markdown with code blocks and structured information
- **HTML**: Web-ready output with CSS styling and metadata

### Analysis Capabilities
- **30+ Programming Languages** with syntax-aware analysis
- **Code Quality Metrics** including comment ratios and complexity
- **File Structure Analysis** with depth and distribution statistics
- **Size Distribution** categorization for optimization insights
- **Language Statistics** with file counts and line counts per language

### Duplicate Detection Methods
- **Hash-based**: Exact file content matching
- **Block Analysis**: Duplicate code segment identification
- **Similarity Matching**: Fuzzy content comparison (80%+ similarity)
- **Configurable Thresholds**: Adjust sensitivity for different use cases

### Configuration Categories
- **App**: General application settings, themes, language
- **Scanning**: File scanning parameters, size limits, depth
- **Analysis**: Analysis settings, quality metrics, duplicate detection
- **Output**: Output format settings, metadata, formatting
- **UI**: Interface settings, window properties, display options
- **Performance**: Threading, caching, and optimization settings

### Achievement Categories
- **Projects**: Loading and managing different projects
- **Files**: Processing files and working with formats
- **Analysis**: Running project analysis and insights
- **Duplicates**: Finding and resolving duplicate code
- **Collection**: Creating code collections and exports
- **Efficiency**: Performance and optimization achievements
- **Exploration**: Discovering advanced features and capabilities

### Hotkey Categories
- **File**: Open, save, export operations
- **Analysis**: Run analysis, find duplicates, quick scan
- **Navigation**: File navigation and selection
- **View**: Interface controls and display options
- **Application**: Preferences, help, about dialogs
- **Development**: Debug mode, console, refresh
- **Custom**: User-defined hotkey combinations

### Testing Features
- **Unit Tests**: Comprehensive testing of all modules and functions
- **Integration Tests**: End-to-end testing of complete workflows
- **Test Fixtures**: Reusable test data and setup utilities
- **Coverage Reporting**: Detailed code coverage analysis
- **Quality Tools**: Integration with professional testing tools
- **Custom Markers**: Organized testing with pytest markers
- **Parallel Execution**: Support for parallel test execution
- **Multiple Formats**: HTML, XML, and terminal reporting

### Documentation Features
- **Developer Guide**: Complete development documentation
- **User Guide**: Comprehensive user tutorials and examples
- **API Reference**: Detailed documentation of all public APIs
- **Architecture Overview**: Clear explanation of system design
- **Contribution Guidelines**: Clear guidelines for contributors
- **Testing Documentation**: Complete testing guide and best practices
- **Troubleshooting**: Common issues and solutions
- **Examples**: Practical examples and use cases
