# gemini_flow (standalone project)

This is a small standalone project that reproduces the **Gemini web (cookie-based)** flow used by gpt4free/g4f.

It is intentionally **not packaged** (no editable install required). You run it directly.

## Install

```bash
cd projects/gemini_flow
python -m pip install -r requirements.txt
```

## Run

```bash
cd projects/gemini_flow
python cli.py chat -c ../../user_cookies "用繁中回覆一句：測試成功"
```

Choose model:

```bash
python cli.py chat -m gemini-3-pro -c user_cookies "用繁中回覆一句：測試成功"
python cli.py chat -m gemini-3-pro-image -c user_cookies "生成一張可愛柴犬插畫（無文字），只輸出圖片"
python cli.py chat -m gemini-3-flash -c user_cookies "用繁中回覆一句：測試成功"
```

Debug mode (prints token/response previews):

```bash
python cli.py chat --debug -c user_cookies "hello"
```

## Structure

- `cli.py`: entrypoint
- `gemini_flow/`: code (cookie loading, protocol parsing, provider/client)

## Cookie file format

The cookies directory should contain one or more `*.json` files exported from Chrome/extensions.
Each file must be a JSON list of objects including at least: `domain`, `name`, `value`.

## Notes

- This is **not** the official Gemini API. It depends on website internals and can break.
- If you see `SNlM0e token not found`, your cookies are likely expired or you were redirected to a login/consent page.
 