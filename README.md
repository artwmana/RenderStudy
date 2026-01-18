# RenderStudy

Конвертация Markdown в DOCX с оформлением по стандарту БГУИР «СТП 01–2024 Дипломные проекты (работы). Общие требования» для пояснительной записки.

## Возможности
- Шаблон страницы: А4, поля 30/15/20/20 мм, односторонняя печать.
- Шрифт Times New Roman 14 pt, интерлиньяж 18 pt, абзацный отступ 1.25 см.
- Заголовки с авто-нумерацией, выравниванием и отступами.
- Списки, кодовые блоки, горизонтальные линии.
- Формулы с нумерацией по разделам `(m.n)`; встроенная и блочная запись.
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
```

## Пример

В каталоге `examples/` лежит `sample_report.md`, демонстрирующий заголовки, списки, формулы, код, рисунок и таблицу. Запустите:

```bash
RenderStudy examples/sample_report.md -o examples/sample_report.docx
```

## Тесты

```bash
pip install .[test]
pytest
```
