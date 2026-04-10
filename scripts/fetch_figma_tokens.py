#!/usr/bin/env python3
"""
Figma设计令牌提取脚本
从Figma文件中提取设计变量(Variables)和样式(Styles)并生成AI友好的设计令牌文件

使用方法:
  python3 fetch_figma_tokens.py --token YOUR_FIGMA_TOKEN --file FILE_KEY

或者设置环境变量:
  export FIGMA_TOKEN=your_token
  python3 fetch_figma_tokens.py
"""

import json
import os
import sys
import argparse
import urllib.request
import urllib.error
from pathlib import Path

# Figma文件Key
SOURCE_FILE_KEY = "8EPfafesUWZV92e2VqfmRq"
TARGET_FILE_KEY = "bNbp9f3xwWpNvSTMGahf8r"

OUTPUT_DIR = Path(__file__).parent.parent / "design-system" / "tokens"


def figma_request(token: str, endpoint: str) -> dict:
    """发送Figma API请求"""
    url = f"https://api.figma.com/v1/{endpoint}"
    req = urllib.request.Request(url, headers={"X-Figma-Token": token})
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        raise RuntimeError(f"Figma API错误 {e.code}: {body}")


def rgb_to_hex(r: float, g: float, b: float) -> str:
    """将0-1范围的RGB值转换为HEX颜色"""
    return "#{:02X}{:02X}{:02X}".format(
        round(r * 255), round(g * 255), round(b * 255)
    )


def extract_variables(file_key: str, token: str) -> dict:
    """提取Figma Variables（设计变量）"""
    print(f"正在获取 Variables: {file_key}")
    data = figma_request(token, f"files/{file_key}/variables/local")

    variables = data.get("meta", {}).get("variables", {})
    collections = data.get("meta", {}).get("variableCollections", {})

    result = {
        "_source": "figma_variables",
        "_fileKey": file_key,
        "collections": {}
    }

    # 按集合分组变量
    for col_id, col in collections.items():
        col_name = col.get("name", col_id)
        result["collections"][col_name] = {
            "_id": col_id,
            "_description": f"变量集合: {col_name}",
            "modes": col.get("modes", []),
            "variables": {}
        }

    for var_id, var in variables.items():
        col_id = var.get("variableCollectionId")
        col = collections.get(col_id, {})
        col_name = col.get("name", col_id)

        var_name = var.get("name", var_id)
        var_type = var.get("resolvedType", "UNKNOWN")
        values_by_mode = var.get("valuesByMode", {})

        # 取第一个mode的值
        first_mode_id = col.get("defaultModeId") or (list(values_by_mode.keys())[0] if values_by_mode else None)
        raw_value = values_by_mode.get(first_mode_id) if first_mode_id else None

        # 转换值
        value = None
        if var_type == "COLOR" and isinstance(raw_value, dict) and "r" in raw_value:
            r, g, b = raw_value["r"], raw_value["g"], raw_value["b"]
            a = raw_value.get("a", 1.0)
            if a < 1.0:
                value = f"rgba({round(r*255)}, {round(g*255)}, {round(b*255)}, {round(a, 2)})"
            else:
                value = rgb_to_hex(r, g, b)
        elif var_type == "FLOAT":
            value = raw_value
        elif var_type == "STRING":
            value = raw_value
        elif var_type == "BOOLEAN":
            value = raw_value

        token_entry = {
            "$type": var_type.lower(),
            "$value": value,
            "$description": var.get("description", ""),
            "_figmaId": var_id,
        }

        # 添加到对应集合
        if col_name in result["collections"]:
            result["collections"][col_name]["variables"][var_name] = token_entry

    return result


def extract_styles(file_key: str, token: str) -> dict:
    """提取Figma Styles（样式）"""
    print(f"正在获取 Styles: {file_key}")
    data = figma_request(token, f"files/{file_key}/styles")

    styles = data.get("meta", {}).get("styles", [])
    result = {
        "_source": "figma_styles",
        "_fileKey": file_key,
        "styles": {}
    }

    for style in styles:
        style_type = style.get("style_type", "UNKNOWN")
        name = style.get("name", style.get("node_id", ""))
        result["styles"][name] = {
            "_type": style_type,
            "_nodeId": style.get("node_id"),
            "$description": style.get("description", ""),
        }

    return result


def extract_file_info(file_key: str, token: str) -> dict:
    """提取文件基本信息和页面结构"""
    print(f"正在获取文件信息: {file_key}")
    data = figma_request(token, f"files/{file_key}?depth=1")
    doc = data.get("document", {})
    pages = [
        {"name": p.get("name"), "id": p.get("id")}
        for p in doc.get("children", [])
        if p.get("type") == "CANVAS"
    ]
    return {
        "name": data.get("name"),
        "lastModified": data.get("lastModified"),
        "version": data.get("version"),
        "pages": pages,
    }


def save_json(data: dict, path: Path):
    """保存JSON文件"""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"已保存: {path}")


def main():
    parser = argparse.ArgumentParser(description="从Figma提取设计令牌")
    parser.add_argument("--token", help="Figma Personal Access Token")
    parser.add_argument("--file", help="Figma文件Key（默认使用源文件）", default=SOURCE_FILE_KEY)
    args = parser.parse_args()

    token = args.token or os.environ.get("FIGMA_TOKEN")
    if not token:
        print("错误：请通过 --token 或 FIGMA_TOKEN 环境变量提供Figma API Token")
        sys.exit(1)

    file_key = args.file

    try:
        # 获取文件信息
        info = extract_file_info(file_key, token)
        print(f"\n文件名称: {info['name']}")
        print(f"最后修改: {info['lastModified']}")
        print(f"页面列表: {[p['name'] for p in info['pages']]}")
        save_json(info, OUTPUT_DIR / "figma-file-info.json")

        # 获取Variables
        try:
            variables = extract_variables(file_key, token)
            save_json(variables, OUTPUT_DIR / "figma-variables-raw.json")
            print(f"\n共提取 {sum(len(c['variables']) for c in variables['collections'].values())} 个变量")
        except Exception as e:
            print(f"警告：无法获取Variables: {e}")

        # 获取Styles
        try:
            styles = extract_styles(file_key, token)
            save_json(styles, OUTPUT_DIR / "figma-styles-raw.json")
            print(f"\n共提取 {len(styles['styles'])} 个样式")
        except Exception as e:
            print(f"警告：无法获取Styles: {e}")

        print("\n完成！请查看 design-system/tokens/ 目录下的文件。")

    except RuntimeError as e:
        print(f"错误: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
