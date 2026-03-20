"""
OpenMAIC Comparative Translation Script v2
Sends Chinese text blocks to local LLMs via LMStudio, splitting large blocks.
Outputs side-by-side comparison markdown files.
"""

import json
import os
import re
import sys
import time
from pathlib import Path
from urllib.request import urlopen, Request
from urllib.error import URLError

LMSTUDIO_URL = "http://192.168.1.210:1234/v1/chat/completions"
MODELS = [
    "google/gemma-3-12b",
]

OUTPUT_DIR = Path(__file__).parent / "translations"
MAX_CHUNK_LINES = 30  # Split blocks larger than this

SYSTEM_PROMPT = """You are a professional translator specializing in software localization.
Translate the following Chinese text to natural, idiomatic English.

Rules:
- This is source code content (system prompts, UI strings, or status messages for an AI education platform)
- Preserve any template variables like ${variable}, {n}, {count}, etc. exactly as-is
- Preserve any markdown formatting (##, **, -, etc.)
- Preserve any code elements (backticks, function names, etc.)
- For system prompts: translate the MEANING and INTENT, not word-for-word
- For UI strings: keep them concise and natural
- Return ONLY the translated text, no explanations or notes"""


def call_model(model_id: str, chinese_text: str, retries: int = 2) -> str:
    """Send text to a specific LMStudio model and return the translation."""
    payload = json.dumps({
        "model": model_id,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": chinese_text},
        ],
        "temperature": 0.3,
        "max_tokens": 4096,
    }).encode("utf-8")

    req = Request(
        LMSTUDIO_URL,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    for attempt in range(retries + 1):
        try:
            with urlopen(req, timeout=600) as resp:
                result = json.loads(resp.read().decode("utf-8"))
                return result["choices"][0]["message"]["content"].strip()
        except URLError as e:
            if attempt < retries:
                print(f"    Retry {attempt + 1}/{retries}...")
                time.sleep(5)
            else:
                return f"[ERROR after {retries + 1} attempts: {e}]"
        except (KeyError, IndexError) as e:
            return f"[ERROR parsing response: {e}]"
    return "[ERROR: unexpected]"


def extract_chinese_blocks(filepath: str) -> list[dict]:
    """Extract blocks of Chinese text, splitting large ones."""
    blocks = []
    chinese_pattern = re.compile(r'[\u4e00-\u9fff]')

    with open(filepath, "r", encoding="utf-8") as f:
        lines = f.readlines()

    current_block = []
    block_start = -1

    for i, line in enumerate(lines):
        if chinese_pattern.search(line):
            if not current_block:
                block_start = i + 1
            current_block.append(line.rstrip())
        else:
            if current_block:
                # Split large blocks
                for sub in _split_block(current_block, block_start):
                    blocks.append(sub)
                current_block = []

    if current_block:
        for sub in _split_block(current_block, block_start):
            blocks.append(sub)

    return blocks


def _split_block(lines: list[str], start_line: int) -> list[dict]:
    """Split a block into sub-blocks of MAX_CHUNK_LINES."""
    if len(lines) <= MAX_CHUNK_LINES:
        return [{
            "start_line": start_line,
            "end_line": start_line + len(lines) - 1,
            "text": "\n".join(lines),
        }]

    chunks = []
    for i in range(0, len(lines), MAX_CHUNK_LINES):
        chunk = lines[i:i + MAX_CHUNK_LINES]
        chunks.append({
            "start_line": start_line + i,
            "end_line": start_line + i + len(chunk) - 1,
            "text": "\n".join(chunk),
        })
    return chunks


def translate_file(filepath: str) -> str:
    """Translate all Chinese blocks in a file using all 3 models."""
    blocks = extract_chinese_blocks(filepath)
    if not blocks:
        return f"No Chinese text found in {filepath}"

    basename = Path(filepath).name
    output = f"# Translations: {basename}\n\n"
    output += f"Source: `{filepath}`\n\n"
    output += f"Found **{len(blocks)}** blocks with Chinese text.\n\n---\n\n"

    for idx, block in enumerate(blocks):
        output += f"## Block {idx + 1} (lines {block['start_line']}-{block['end_line']})\n\n"
        output += f"### Original Chinese\n```\n{block['text']}\n```\n\n"

        for model_id in MODELS:
            short_name = model_id.split("/")[-1] if "/" in model_id else model_id
            print(f"  [{short_name}] Translating block {idx + 1}/{len(blocks)}...")
            start = time.time()
            translation = call_model(model_id, block["text"])
            elapsed = time.time() - start
            output += f"### {short_name} ({elapsed:.1f}s)\n```\n{translation}\n```\n\n"

        output += "---\n\n"

    return output


# Files to translate with the comparative pipeline
FILES_TO_TRANSLATE = [
    r"n:\projects\govware\OpenMAIC\lib\pbl\pbl-system-prompt.ts",
    r"n:\projects\govware\OpenMAIC\lib\pbl\mcp\agent-templates.ts",
    r"n:\projects\govware\OpenMAIC\lib\pbl\generate-pbl.ts",
]


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Test connectivity
    print(f"Testing LMStudio at {LMSTUDIO_URL}...")
    try:
        test_req = Request("http://192.168.1.210:1234/v1/models", method="GET")
        with urlopen(test_req, timeout=5) as resp:
            models = json.loads(resp.read().decode("utf-8"))
            available = [m["id"] for m in models["data"]]
            for m in MODELS:
                status = "✓" if m in available else "✗ NOT FOUND"
                print(f"  {m}: {status}")
    except URLError as e:
        print(f"ERROR: Cannot reach LMStudio: {e}")
        sys.exit(1)

    print()

    for filepath in FILES_TO_TRANSLATE:
        if not os.path.exists(filepath):
            print(f"SKIP: {filepath} (not found)")
            continue

        basename = Path(filepath).stem
        print(f"Translating: {basename}...")
        result = translate_file(filepath)

        out_path = OUTPUT_DIR / f"{basename}.md"
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(result)
        print(f"  -> {out_path}\n")

    print("Done! Review translations in scripts/translations/")


if __name__ == "__main__":
    main()
