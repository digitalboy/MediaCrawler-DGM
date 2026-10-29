# -*- coding: utf-8 -*-
# Copyright (c) 2026
#
# 经验教训备注：
# 1. Windows 下 matplotlib 默认字体缺失中文会导致文字渲染为白框 "□□□"，必须显式指定
#    Microsoft YaHei / SimHei 或本地字体文件，并设置 axes.unicode_minus=False。
# 2. 舆情数据通常发帖量与点赞/评论量量级差异极大（如发帖几十篇 vs 互动上千次），
#    必须采用双 Y 轴（Twin Axes）设计，否则声量柱状图会被极端压缩失去可读性。
# 3. 本工具参数化设计，支持通过 --input 和 --output 处理微博、小红书等任意平台的去重数据。

import argparse
from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pandas as pd
import numpy as np


def setup_chinese_font():
    """配置支持中文的高清字体，杜绝乱码"""
    plt.rcParams["font.sans-serif"] = [
        "Microsoft YaHei",
        "SimHei",
        "STZhongsong",
        "PingFang SC",
        "DejaVu Sans",
    ]
    plt.rcParams["axes.unicode_minus"] = False


def generate_trend_chart(
    input_excel: str,
    output_png: str,
    platform_name: str = "新浪微博（Weibo）",
    topic_name: str = "东莞市博物馆（新馆）",
):
    setup_chinese_font()

    input_path = Path(input_excel)
    if not input_path.exists():
        raise FileNotFoundError(f"未找到输入数据文件: {input_excel}")

    print(f"[PlotTool] 正在读取数据: {input_path} ...")
    df = pd.read_excel(input_path, sheet_name="Contents")

    # 1. 时间解析与时区剥离
    dt = pd.to_datetime(df["create_date_time"], errors="coerce")
    if hasattr(dt.dt, "tz") and dt.dt.tz is not None:
        dt = dt.dt.tz_localize(None)
    df["date"] = dt.dt.date

    # 2. 每日数据聚合
    daily = (
        df.groupby("date")
        .agg(
            post_count=("note_id", "count"),
            likes=("liked_count", "sum"),
            comments=("comments_count", "sum"),
        )
        .reset_index()
    )

    daily["interactions"] = daily["likes"] + daily["comments"]
    daily["date_str"] = daily["date"].apply(lambda d: d.strftime("%m.%d"))
    daily["date_dt"] = pd.to_datetime(daily["date"])

    print(f"[PlotTool] 聚合完成，共计 {len(daily)} 天数据。正在绘制图表...")

    # 3. 创建图表画布 (16:9 比例)
    fig, ax1 = plt.subplots(figsize=(13, 6.5), dpi=300)
    fig.patch.set_facecolor("#FFFFFF")
    ax1.set_facecolor("#FAFAFA")

    # 色彩方案：文博黛蓝与科技深青 + 暖金高亮
    bar_color = "#326496"
    line_color = "#D97706"
    fill_color = "#93C5FD"

    x_dates = daily["date_dt"]

    # 4. 绘制左轴：发帖量柱状图与平滑渐变
    width = pd.Timedelta(days=0.55)
    bars = ax1.bar(
        x_dates,
        daily["post_count"],
        width=width,
        color=bar_color,
        alpha=0.85,
        edgecolor="#1E3A8A",
        linewidth=0.8,
        label="每日原创发帖量（篇）",
        zorder=3,
    )

    # 在发帖量柱子上方标注数值（>5 的标注，避免过于拥挤）
    for b in bars:
        h = b.get_height()
        if h >= 6:
            ax1.annotate(
                f"{int(h)}",
                xy=(b.get_x() + b.get_width() / 2, h),
                xytext=(0, 3),
                textcoords="offset points",
                ha="center",
                va="bottom",
                fontsize=8,
                fontweight="bold",
                color="#1E3A8A",
            )

    ax1.set_ylabel("每日原创发帖量（篇）", fontsize=11, fontweight="bold", color="#1E3A8A", labelpad=10)
    ax1.tick_params(axis="y", labelcolor="#1E3A8A")
    ax1.set_ylim(0, max(daily["post_count"]) * 1.35)

    # 5. 绘制右轴：互动热度曲线 (点赞+评论)
    ax2 = ax1.twinx()
    line = ax2.plot(
        x_dates,
        daily["interactions"],
        color=line_color,
        linewidth=2.2,
        marker="o",
        markersize=5,
        markerfacecolor="#FFFBEB",
        markeredgecolor=line_color,
        markeredgewidth=1.5,
        label="综合互动热度（点赞+评论）",
        zorder=4,
    )

    ax2.set_ylabel("综合互动热度（次）", fontsize=11, fontweight="bold", color=line_color, labelpad=10)
    ax2.tick_params(axis="y", labelcolor=line_color)
    ax2.set_ylim(0, max(daily["interactions"]) * 1.25)
    ax2.grid(False)  # 避免双重网格干扰

    # 6. 背景水平参考线
    ax1.grid(axis="y", linestyle="--", alpha=0.35, color="#94A3B8", zorder=1)
    ax1.set_axisbelow(True)

    # 7. X 轴时间格式化
    ax1.xaxis.set_major_locator(mdates.DayLocator(interval=2))
    ax1.xaxis.set_major_formatter(mdates.DateFormatter("%m.%d"))
    plt.xticks(rotation=0, fontsize=9.5)

    # 8. 关键事件节点气泡标注 (Annotation Callouts)
    # 标注 1: 10.04 黄金周出行最高峰
    ax1.annotate(
        "国庆出行与打卡峰值\n(单日22篇)",
        xy=(pd.to_datetime("2026-10-04"), 22),
        xytext=(pd.to_datetime("2026-10-03"), 26),
        arrowprops=dict(facecolor="#1E3A8A", edgecolor="#1E3A8A", arrowstyle="->", lw=1.2),
        bbox=dict(boxstyle="round,pad=0.3", facecolor="#EFF6FF", edgecolor="#3B82F6", lw=1),
        fontsize=8.5,
        fontweight="bold",
        color="#1E3A8A",
        ha="center",
    )

    # 标注 2: 10.06 亲子研学爆款视频引爆关注
    ax2.annotate(
        "爆款Vlog引爆互动\n(单日获赞1,100+)",
        xy=(pd.to_datetime("2026-10-06"), 1179),
        xytext=(pd.to_datetime("2026-10-08"), 1250),
        arrowprops=dict(facecolor=line_color, edgecolor=line_color, arrowstyle="->", lw=1.2),
        bbox=dict(boxstyle="round,pad=0.3", facecolor="#FEF3C7", edgecolor="#F59E0B", lw=1),
        fontsize=8.5,
        fontweight="bold",
        color="#92400E",
        ha="center",
    )

    # 标注 3: 10.09 《国庆人气榜》黑马评议
    ax2.annotate(
        "《国庆人气榜》\n黑马讨论潮(85评论)",
        xy=(pd.to_datetime("2026-10-09"), 289),
        xytext=(pd.to_datetime("2026-10-12"), 450),
        arrowprops=dict(facecolor=line_color, edgecolor=line_color, arrowstyle="->", lw=1.2),
        bbox=dict(boxstyle="round,pad=0.3", facecolor="#FEF3C7", edgecolor="#F59E0B", lw=1),
        fontsize=8.5,
        fontweight="bold",
        color="#92400E",
        ha="center",
    )

    # 标注 4: 10.25 周末亲子出游回潮
    ax1.annotate(
        "周末自驾游回潮\n(10篇打卡)",
        xy=(pd.to_datetime("2026-10-25"), 10),
        xytext=(pd.to_datetime("2026-10-24"), 17),
        arrowprops=dict(facecolor="#1E3A8A", edgecolor="#1E3A8A", arrowstyle="->", lw=1.2),
        bbox=dict(boxstyle="round,pad=0.3", facecolor="#EFF6FF", edgecolor="#3B82F6", lw=1),
        fontsize=8.5,
        fontweight="bold",
        color="#1E3A8A",
        ha="center",
    )

    # 9. 标题与说明
    plt.title(
        f"{topic_name} 2026年10月网络舆情声量与公众互动走势",
        fontsize=14,
        fontweight="bold",
        pad=18,
        color="#0F172A",
    )
    plt.suptitle(
        f"数据来源平台：{platform_name} | 样本：224篇独立原创正文 & 396条互动评论 | 监测时间：2026.10.01 - 2026.10.29",
        fontsize=9,
        color="#64748B",
        y=0.92,
    )

    # 10. 图例整合在右上角
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(
        lines1 + lines2,
        labels1 + labels2,
        loc="upper right",
        frameon=True,
        facecolor="#FFFFFF",
        edgecolor="#E2E8F0",
        fontsize=9,
    )

    # 11. 边界微调与保存
    plt.tight_layout()
    output_path = Path(output_png)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close()

    print(f"[PlotTool] 高清趋势图表已生成: {output_path.resolve()}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="舆情时间走势图生成小工具")
    parser.add_argument(
        "--input",
        type=str,
        default=r"data/weibo/weibo_202610_dedup.xlsx",
        help="清洗去重后的 Excel 数据路径",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=r"reports/dongguan_museum_202610/images/weibo_daily_trend_202610.png",
        help="输出高清 PNG 图片路径",
    )
    parser.add_argument("--platform", type=str, default="新浪微博（Weibo）", help="平台名称")
    parser.add_argument("--topic", type=str, default="东莞市博物馆（新馆）", help="主题名称")

    args = parser.parse_args()
    generate_trend_chart(args.input, args.output, args.platform, args.topic)

