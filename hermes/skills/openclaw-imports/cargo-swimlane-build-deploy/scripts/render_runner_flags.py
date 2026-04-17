#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from typing import Any


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="从 pipeline list-images 输出中生成 deploy 的 --runner-image 参数。"
    )
    parser.add_argument(
        "--input",
        default="-",
        help="输入 JSON 文件路径，默认从 stdin 读取。",
    )
    parser.add_argument(
        "--service-name",
        action="append",
        default=[],
        help="按 service_name 模糊过滤，可重复传入（通常是 com.xxx.bbb.cc，形态接近 appkey）。",
    )
    parser.add_argument(
        "--appkey",
        action="append",
        default=[],
        help="按 appkey 模糊过滤，可重复传入。",
    )
    parser.add_argument(
        "--runner-uuid",
        action="append",
        default=[],
        help="按 runner_uuid 精确过滤，可重复传入。",
    )
    parser.add_argument(
        "--image-uuid",
        default="",
        help="给所有匹配 runner 指定统一目标镜像。",
    )
    parser.add_argument(
        "--output",
        choices=["flags", "pairs"],
        default="flags",
        help="输出格式：flags/pairs，默认 flags。",
    )
    return parser.parse_args()


def _load_json(path: str) -> Any:
    try:
        if path == "-":
            raw = sys.stdin.read()
        else:
            with open(path, "r", encoding="utf-8") as fh:
                raw = fh.read()
    except OSError as exc:
        raise ValueError(f"读取输入失败: {exc}") from exc

    if not raw.strip():
        raise ValueError("输入为空，请提供 list-images 的 JSON 输出")

    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(f"输入不是合法 JSON: {exc}") from exc


def _extract_runners(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, dict):
        runners = payload.get("runners")
        if isinstance(runners, list):
            return [item for item in runners if isinstance(item, dict)]
        data = payload.get("data")
        if isinstance(data, dict) and isinstance(data.get("runners"), list):
            return [item for item in data["runners"] if isinstance(item, dict)]
    raise ValueError("未找到 runners 列表，请确认输入是 list-images 命令输出")


def _match_any(text: str, keywords: list[str]) -> bool:
    if not keywords:
        return True
    lowered = text.lower()
    for keyword in keywords:
        token = str(keyword or "").strip().lower()
        if token and token in lowered:
            return True
    return False


def _filter_runners(
    runners: list[dict[str, Any]],
    *,
    service_keywords: list[str],
    appkey_keywords: list[str],
    runner_uuids: list[str],
) -> list[dict[str, Any]]:
    runner_uuid_set = {item.strip() for item in runner_uuids if item.strip()}
    results: list[dict[str, Any]] = []
    for runner in runners:
        runner_uuid = str(runner.get("runner_uuid") or "").strip()
        service_name = str(runner.get("service_name") or "").strip()
        appkey = str(runner.get("appkey") or "").strip()
        if runner_uuid_set and runner_uuid not in runner_uuid_set:
            continue
        if not _match_any(service_name, service_keywords):
            continue
        if not _match_any(appkey, appkey_keywords):
            continue
        results.append(runner)
    return results


def _build_mapping(
    runners: list[dict[str, Any]],
    *,
    image_uuid: str,
) -> list[tuple[str, str]]:
    forced_image_uuid = image_uuid.strip()
    mappings: list[tuple[str, str]] = []
    for runner in runners:
        runner_uuid = str(runner.get("runner_uuid") or "").strip()
        if not runner_uuid:
            continue
        selected_image_uuid = forced_image_uuid or str(
            runner.get("current_image_uuid") or ""
        ).strip()
        if not selected_image_uuid:
            raise ValueError(
                f"runner 缺少可用镜像：runner_uuid={runner_uuid}，请显式传 --image-uuid"
            )
        mappings.append((runner_uuid, selected_image_uuid))
    if not mappings:
        raise ValueError("未生成任何 runner/image 映射")
    return mappings


def _print_flags(mappings: list[tuple[str, str]]) -> None:
    chunks = [f"--runner-image {runner}={image}" for runner, image in mappings]
    print(" ".join(chunks))


def _print_pairs(mappings: list[tuple[str, str]]) -> None:
    for runner, image in mappings:
        print(f"{runner}={image}")


def main() -> int:
    args = parse_args()
    try:
        payload = _load_json(args.input)
        runners = _extract_runners(payload)

        selected_runners = _filter_runners(
            runners,
            service_keywords=args.service_name,
            appkey_keywords=args.appkey,
            runner_uuids=args.runner_uuid,
        )
        if not selected_runners:
            raise ValueError(
                "未匹配到 runner，请调整过滤条件（service-name/appkey/runner-uuid）。"
                "注意 service-name 通常是 com.xxx...，不是 banma_service_aibox_server 这类展示名。"
            )

        mappings = _build_mapping(
            selected_runners,
            image_uuid=args.image_uuid,
        )

        if args.output == "pairs":
            _print_pairs(mappings)
        else:
            _print_flags(mappings)
        return 0
    except ValueError as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
