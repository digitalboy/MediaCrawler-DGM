# -*- coding: utf-8 -*-
# Copyright (c) 2026
#
# 经验教训备注：
# 1. 爬虫生成的 create_date_time 带有时区 (+08:00)，使用 pandas 比较时若传入 tz-naive 的时间字符串会抛出
#    "TypeError: Cannot compare tz-naive and tz-aware datetime-like objects"。因此必须统一转为带时区或统一去除时区对比。
# 2. 爬虫导出的 Excel 包含 Contents 和 Comments 两个 Sheet，过滤指定月份/时间区间时，不仅要过滤 Contents 中的时间，
#    还必须基于 note_id 联动过滤 Comments，避免出现孤立评论或跨月脏数据。

import sys
from pathlib import Path
import pandas as pd


def filter_weibo_excel(
    file_path: str,
    year_month: str = "2026-10",
    output_path: str = None,
):
    path = Path(file_path)
    if not path.exists():
        print(f"Error: File not found: {file_path}")
        return

    if output_path is None:
        output_path = path.parent / f"{path.stem}_{year_month.replace('-', '')}_filtered{path.suffix}"

    print(f"Loading {file_path} ...")
    df_contents = pd.read_excel(file_path, sheet_name="Contents")
    df_comments = pd.read_excel(file_path, sheet_name="Comments")

    # 1. 统一转换时间并剥离时区进行比较，避免 tz-naive 与 tz-aware 比较报错
    dt_contents = pd.to_datetime(df_contents["create_date_time"], errors="coerce")
    if hasattr(dt_contents.dt, "tz") and dt_contents.dt.tz is not None:
        dt_contents = dt_contents.dt.tz_localize(None)

    # 构造起止时间
    start_dt = pd.to_datetime(f"{year_month}-01 00:00:00")
    # 计算下月初
    parts = year_month.split("-")
    y, m = int(parts[0]), int(parts[1])
    if m == 12:
        end_dt = pd.to_datetime(f"{y+1}-01-01 00:00:00")
    else:
        end_dt = pd.to_datetime(f"{y}-{m+1:02d}-01 00:00:00")

    mask_contents = (dt_contents >= start_dt) & (dt_contents < end_dt)
    filtered_contents = df_contents[mask_contents]

    valid_note_ids = set(filtered_contents["note_id"].astype(str))

    # 2. 联动过滤 Comments（属于有效 note_id 且评论时间也在指定月份内）
    dt_comments = pd.to_datetime(df_comments["create_date_time"], errors="coerce")
    if hasattr(dt_comments.dt, "tz") and dt_comments.dt.tz is not None:
        dt_comments = dt_comments.dt.tz_localize(None)

    mask_comments = (
        df_comments["note_id"].astype(str).isin(valid_note_ids)
        & (dt_comments >= start_dt)
        & (dt_comments < end_dt)
    )
    filtered_comments = df_comments[mask_comments]

    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
        filtered_contents.to_excel(writer, sheet_name="Contents", index=False)
        filtered_comments.to_excel(writer, sheet_name="Comments", index=False)

    print(f"Filtered Excel created successfully -> {output_path}")
    print(f"  Contents: {len(df_contents)} -> {len(filtered_contents)} (Filtered {year_month})")
    print(f"  Comments: {len(df_comments)} -> {len(filtered_comments)} (Filtered {year_month})")


if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else r"data/weibo/weibo_search_20261029_192800.xlsx"
    filter_weibo_excel(target)
