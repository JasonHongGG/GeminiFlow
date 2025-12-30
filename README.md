# gemini_flow

## Install

```bash
cd projects/gemini_flow
python -m pip install -r requirements.txt
```

## Run

```bash
python cli.py chat -c user_cookies "用繁中回覆一句：測試成功"
```

Choose model:

```bash
python cli.py chat -m gemini-3-pro -c user_cookies "用繁中回覆一句：測試成功"
python cli.py chat -m gemini-3-flash -c user_cookies "用繁中回覆一句：測試成功"
```

Debug mode (prints token/response previews):

```bash
python cli.py chat --debug -c user_cookies "hello"
```

## Cookie file format

The cookies directory should contain one or more `*.json` files exported from Chrome/extensions.
Each file must be a JSON list of objects including at least: `domain`, `name`, `value`.

## Notes
- If you see `SNlM0e token not found`, your cookies are likely expired or you were redirected to a login/consent page.
 