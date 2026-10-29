# -*- coding: utf-8 -*-
import pandas as pd

f = r"data/weibo/weibo_search_20261029_235834.xlsx"
df_contents = pd.read_excel(f, sheet_name="Contents")
df_comments = pd.read_excel(f, sheet_name="Comments")

print("=== 1. 基本统计 ===")
print("正文总条数:", len(df_contents), "去重后独立条数:", df_contents["note_id"].nunique())
print("评论总条数:", len(df_comments), "去重后独立条数:", df_comments["comment_id"].nunique())

df_contents["dt"] = pd.to_datetime(df_contents["create_date_time"], errors="coerce")
if hasattr(df_contents["dt"].dt, "tz") and df_contents["dt"].dt.tz is not None:
    df_contents["dt"] = df_contents["dt"].dt.tz_localize(None)

df_contents["month"] = df_contents["dt"].dt.to_period("M")
print("\n=== 2. 正文月份分布 ===")
print(df_contents["month"].value_counts().sort_index())

print("\n=== 3. 互动指标 TOP 5 (点赞数最热门微博) ===")
top_liked = (
    df_contents.sort_values(by="liked_count", ascending=False)
    .drop_duplicates(subset=["note_id"])
    .head(5)
)
for _, r in top_liked.iterrows():
    print(f"[{r['create_date_time']}] 点赞:{r['liked_count']} 评论:{r['comments_count']} 转发:{r['shared_count']}")
    print(f"  内容摘要: {str(r['content'])[:80]}...\n")

print("=== 4. 2026年10月每日发帖走势 ===")
oct_df = df_contents[df_contents["month"] == "2026-10"].drop_duplicates(subset=["note_id"])
daily = oct_df["dt"].dt.date.value_counts().sort_index()
print(daily)

print("\n=== 5. 评论情感与高频词特征 ===")
df_comments["dt"] = pd.to_datetime(df_comments["create_date_time"], errors="coerce")
if hasattr(df_comments["dt"].dt, "tz") and df_comments["dt"].dt.tz is not None:
    df_comments["dt"] = df_comments["dt"].dt.tz_localize(None)
oct_comments = df_comments[df_comments["note_id"].isin(oct_df["note_id"])]
print("10月正文关联的评论总数:", len(oct_comments), "去重后评论数:", oct_comments["comment_id"].nunique())
top_comments = oct_comments.sort_values(by="comment_like_count", ascending=False).drop_duplicates(subset=["comment_id"]).head(10)
print("\n=== 6. 10月份互动量最高的热门评论 TOP 10 ===")
for _, r in top_comments.iterrows():
    print(f"点赞:{r['comment_like_count']} | 时间:{r['create_date_time']} | 评论: {r['content']}")

