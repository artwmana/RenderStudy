# RenderStudy

Конвертация Markdown в DOCX с оформлением по стандарту БГУИР «СТП 01–2024 Дипломные проекты (работы). Общие требования» для пояснительной записки.

## Возможности
- Шаблон страницы: А4, поля 30/15/20/20 мм, односторонняя печать.
- Шрифт Times New Roman 14 pt, интерлиньяж 18 pt, абзацный отступ 1.25 см.
- Заголовки с авто-нумерацией, выравниванием и отступами.
- Списки, кодовые блоки, горизонтальные линии.
- Формулы с нумерацией по разделам `(m.n)`; встроенная и блочная запись с использованием встроенных объектов формул MS Word.
- Рисунки с подписями `Рисунок m.n – ...`, таблицы `Таблица m.n – ...`.
- Базовый разбор Markdown через `markdown-it-py` + `texmath`.

## Установка

```bash
pip install .
```

## Использование CLI

Создать файл report.md
```bash
RenderStudy report.md
RenderStudy report.md -o report.docx
RenderStudy report.md --verbose
# или YAML
RenderStudy data.yaml -o data.docx
# или переоформление существующего DOCX
RenderStudy draft.docx -o draft_formatted.docx
```

Для входного `.docx` используется режим:
- первая страница входного файла отбрасывается,
- текст после первой страницы извлекается в Markdown,
- итоговый `.docx` собирается как `титульник из examples/титульник.docx + отрендеренный Markdown`.

## Telegram бот

Бот принимает:
- `.md`
- `.docx`
- обычный текст в сообщении

И отправляет обратно готовый `.docx` с форматированием.

Запуск:
```bash
export TELEGRAM_BOT_TOKEN="ваш_токен"
RenderStudyBot
```

Или:
```bash
RenderStudyBot --token "ваш_токен"
```

Для режима бота с входом `текст` и `.md` нужен титульник:
```bash
export RENDERSTUDY_TITLE_TEMPLATE="/абсолютный/путь/к/титульник.docx"
```
Если переменная не задана, бот пытается использовать `examples/титульник.docx`.

Хранилище всех работ бота:
```bash
export RENDERSTUDY_BOT_STORAGE="/абсолютный/путь/к/папке"
```
Если переменная не задана, используется `./renderstudy_bot_storage` в текущей директории запуска.
Внутри автоматически создаются папки:
- `docx/`
- `md/`
- `text/`

## HTTP API

Для работы API необходимо задать ключ авторизации в переменной окружения `RENDERSTUDY_API_KEY`:

Запуск:
```bash
export RENDERSTUDY_API_KEY="ваш_секретный_ключ"
RenderStudyAPI --host 0.0.0.0 --port 8000
```

### Endpoint

- `POST /format`
- Обязательный заголовок: `X-API-Key: ваш_секретный_ключ`
- `Content-Type: multipart/form-data`
- Ответ: `Content-Type: multipart/form-data` (поле `file` с `.docx`)

### Request contract (multipart/form-data)

Передайте **либо** файл, **либо** текст:

- `file` (optional): файл с расширением `.md | .txt | .docx`
- `text` (optional): обычный текст для форматирования
- `filename` (optional): имя для результата при использовании `text`

Ограничение: одновременно `file` и `text` передавать нельзя.

Валидация:
- для неподдерживаемых типов возвращается `415 Unsupported Media Type`;
- проверяется сигнатура файла;
- для `.docx` дополнительно выполняется базовая проверка ZIP-bomb
  (число entry, суммарный распакованный размер, коэффициент сжатия).

### Response contract (multipart/form-data)

Один part:
- `name="file"`
- `filename="<input>_formatted.docx"`
- `Content-Type: application/vnd.openxmlformats-officedocument.wordprocessingml.document`

### Примеры

Файл:
```bash
curl -X POST "http://localhost:8000/format" \
  -H "X-API-Key: ваш_секретный_ключ" \
  -F "file=@examples/sample_report.md" \
  --output response.multipart
```

Текст:
```bash
curl -X POST "http://localhost:8000/format" \
  -H "X-API-Key: ваш_секретный_ключ" \
  -F "text=# ВВЕДЕНИЕ\n\nТекст..." \
  -F "filename=my_text" \
  --output response.multipart
```

## Пример

В каталоге `examples/` лежит `sample_report.md`, демонстрирующий заголовки, списки, формулы, код, рисунок и таблицу. Запустите:

```bash
RenderStudy examples/sample_report.md -o examples/sample_report.docx
```

Также есть пример `examples/sample_report.yaml` с жесткой структурой полей. Поддерживаемые ключи:

```yaml
title: "1 Введение"          # заголовок (можно с номером)
subtitle: "1.1 Цель"        # подзаголовок (опционально)
context: "Текст абзаца"     # основной абзац
ordered_list:               # нумерованный список
  - Первый
  - Второй
bullet_list:                # маркированный список
  - Маркер A
  - Маркер B
image:                      # картинка с подписью
  path: images/sample.png
  caption: "Схема процесса"
formula: "S = \\pi r^2"     # формула (LaTeX как текст)
```

## Тесты

```bash
pip install .[test]
pytest
```
