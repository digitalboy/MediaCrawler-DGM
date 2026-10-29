# -*- coding: utf-8 -*-
# Copyright (c) 2026
#
# 经验教训备注：
# 1. 爬虫生成的 create_date_time 带有 +08:00 时区信息，使用 pandas 比较前必须先统一剥离或转换时区，
#    防止抛出 "TypeError: Cannot compare tz-naive and tz-aware datetime-like objects"。
# 2. 爬取时使用双关键词搜索会有重叠记录，清洗时同时输出：
#    - 去重版本 (按 note_id / comment_id 去重，避免情绪统计权重失真)
#    - 保留冗余版本 (仅剔除 9 月及更早，保留全部抓取记录，供用户自定义管道使用)
# 3. 0 评论的微博必须予以完整保留，Comments 表基于有效 note_id 做外键对齐。

from pathlib import Path
import pandas as pd


def clean_october_dataset(input_file: str):
    p = Path(input_file)
    if not p.exists():
        print(f"File not found: {input_file}")
        return

    print(f"Reading dataset: {input_file} ...")
    df_contents = pd.read_excel(p, sheet_name="Contents")
    df_comments = pd.read_excel(p, sheet_name="Comments")

    print(f"Original: {len(df_contents)} contents, {len(df_comments)} comments")

    # 1. 统一转换并剥离时区
    dt_contents = pd.to_datetime(df_contents["create_date_time"], errors="coerce")
    if hasattr(dt_contents.dt, "tz") and dt_contents.dt.tz is not None:
        dt_contents = dt_contents.dt.tz_localize(None)

    dt_comments = pd.to_datetime(df_comments["create_date_time"], errors="coerce")
    if hasattr(dt_comments.dt, "tz") and dt_comments.dt.tz is not None:
        dt_comments = dt_comments.dt.tz_localize(None)

    # 2. 仅保留 2026 年 10 月 (2026-10-01 00:00:00 ~ 2026-10-31 23:59:59)
    mask_oct_contents = (dt_contents >= "2026-10-01") & (dt_contents < "2026-11-01")
    oct_contents = df_contents[mask_oct_contents].copy()

    valid_note_ids = set(oct_contents["note_id"].astype(str))

    # Comments 属于 10 月主贴且评论时间也在 10 月
    mask_oct_comments = (
        df_comments["note_id"].astype(str).isin(valid_note_ids)
        & (dt_comments >= "2026-10-01")
        & (dt_comments < "2026-11-01")
    )
    oct_comments = df_comments[mask_oct_comments].copy()

    # 输出版本 A：保留冗余的 10 月版本 (仅剔除 9 月及更早)
    out_all = p.parent / "weibo_202610_all.xlsx"
    with pd.ExcelWriter(out_all, engine="openpyxl") as writer:
        oct_contents.to_excel(writer, sheet_name="Contents", index=False)
        oct_comments.to_excel(writer, sheet_name="Comments", index=False)
    print(f"Saved (All 10-Month Records): {out_all}")
    print(f"  Contents: {len(oct_contents)}, Comments: {len(oct_comments)}")

    # 输出版本 B：去重纯净版 (按 note_id 和 comment_id 排重，最适合情感分析)
    out_dedup = p.parent / "weibo_202610_dedup.xlsx"
    dedup_contents = oct_contents.drop_duplicates(subset=["note_id"])
    dedup_comments = oct_comments.drop_duplicates(subset=["comment_id"])
    with pd.ExcelWriter(out_dedup, engine="openpyxl") as writer:
        dedup_contents.to_excel(writer, sheet_name="Contents", index=False)
        dedup_comments.to_excel(writer, sheet_name="Comments", index=False)
    print(f"Saved (Deduplicated 10-Month Records): {out_dedup}")
    print(f"  Contents: {len(dedup_contents)}, Comments: {len(dedup_comments)}")


if __name__ == "__main__":
    clean_october_dataset(r"data/weibo/weibo_search_20261029_235834.xlsx")

