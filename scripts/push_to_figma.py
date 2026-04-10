#!/usr/bin/env python3
"""
将设计令牌写入Figma Variables

使用Figma Variables API将design-system/tokens/目录下的规范
同步回目标Figma文件中。

使用方法:
  python3 push_to_figma.py --token YOUR_FIGMA_TOKEN
"""

import json
import os
import sys
import argparse
import urllib.request
import urllib.error
from pathlib import Path

TARGET_FILE_KEY = "bNbp9f3xwWpNvSTMGahf8r"
TOKENS_DIR = Path(__file__).parent.parent / "design-system" / "tokens"


def figma_post(token: str, endpoint: str, payload: dict) -> dict:
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        f"https://api.figma.com/v1/{endpoint}",
        data=body,
        headers={
            "X-Figma-Token": token,
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        body_resp = e.read().decode()
        raise RuntimeError(f"Figma API错误 {e.code}: {body_resp}")


def load_color_tokens() -> dict:
    path = TOKENS_DIR / "colors.json"
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def hex_to_rgb(hex_color: str) -> dict:
    hex_color = hex_color.lstrip("#")
    r = int(hex_color[0:2], 16) / 255
    g = int(hex_color[2:4], 16) / 255
    b = int(hex_color[4:6], 16) / 255
    return {"r": r, "g": g, "b": b, "a": 1.0}


def build_variables_payload(tokens: dict) -> dict:
    """
    将设计令牌转换为Figma Variables API格式
    Figma Variables POST /v1/files/:file_key/variables
    """
    variable_collections = []
    variables = []

    # 颜色集合
    collection_id = "color-system"
    variable_collections.append({
        "action": "CREATE",
        "id": collection_id,
        "name": "Color System",
        "initialModeId": "mode-light",
    })

    colors = tokens.get("colors", {})
    for group_name, group in colors.items():
        if isinstance(group, dict) and "$type" not in group:
            for scale_key, scale_val in group.items():
                if isinstance(scale_val, dict) and "$value" in scale_val:
                    var_name = f"{group_name}/{scale_key}"
                    hex_val = scale_val["$value"]
                    variables.append({
                        "action": "CREATE",
                        "id": f"color-{group_name}-{scale_key}",
                        "name": var_name,
                        "variableCollectionId": collection_id,
                        "resolvedType": "COLOR",
                        "description": scale_val.get("$description", ""),
                        "valuesByMode": {
                            "mode-light": hex_to_rgb(hex_val)
                        }
                    })

    return {
        "variableCollections": variable_collections,
        "variables": variables,
        "variableModes": [
            {
                "action": "CREATE",
                "id": "mode-light",
                "name": "Light",
                "variableCollectionId": collection_id,
            }
        ],
    }


def main():
    parser = argparse.ArgumentParser(description="将设计令牌推送到Figma")
    parser.add_argument("--token", help="Figma Personal Access Token")
    parser.add_argument("--file", default=TARGET_FILE_KEY, help="目标Figma文件Key")
    args = parser.parse_args()

    token = args.token or os.environ.get("FIGMA_TOKEN")
    if not token:
        print("错误：请通过 --token 或 FIGMA_TOKEN 环境变量提供Figma API Token")
        sys.exit(1)

    print("正在加载颜色令牌...")
    color_tokens = load_color_tokens()

    print("正在构建Figma Variables payload...")
    payload = build_variables_payload(color_tokens)
    print(f"  变量集合: {len(payload['variableCollections'])} 个")
    print(f"  变量: {len(payload['variables'])} 个")

    print(f"\n正在写入Figma文件: {args.file}")
    try:
        result = figma_post(token, f"files/{args.file}/variables", payload)
        print("成功！Figma Variables已更新。")
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except RuntimeError as e:
        print(f"错误: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
