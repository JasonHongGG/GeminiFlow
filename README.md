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

## Image output directory

When using an `*-image` model, generated images are saved under `output/image/` by default.

You can override the output directory with an environment variable:

- `GEMINI_FLOW_IMAGE_DIR`: absolute path or relative path (relative to current working directory)

Example (Windows PowerShell):

```powershell
$env:GEMINI_FLOW_IMAGE_DIR = "output/image"
python cli.py chat -m gemini-3-pro-image -c user_cookies "Generate an image of a cute shiba inu."
```

## Cookie file format

The cookies directory should contain one or more `*.json` files exported from Chrome/extensions.
Each file must be a JSON list of objects including at least: `domain`, `name`, `value`.

## Notes
- If you see `SNlM0e token not found`, your cookies are likely expired or you were redirected to a login/consent page.
 