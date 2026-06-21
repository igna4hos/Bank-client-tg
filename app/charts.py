import io

import matplotlib
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt


def _style(ax: plt.Axes) -> None:
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(axis="y", alpha=0.3, linestyle="--")


def _save(fig: plt.Figure) -> io.BytesIO:
    buf = io.BytesIO()
    plt.tight_layout()
    plt.savefig(buf, format="png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return buf


def make_friction_chart(data: dict) -> io.BytesIO:
    funnel_name = data["funnel_name"]
    benchmark = data["benchmark_duration_sec"]
    stats = data["stats"]

    labels = ["Мин", "Среднее", "Медиана", "Макс"]
    keys = ["min_duration_sec", "avg_duration_sec", "median_duration_sec", "max_duration_sec"]
    day_colors = ["#2196F3", "#90CAF9"]

    x = np.arange(len(labels))
    n = len(stats)
    width = 0.7 / max(n, 1)

    fig, ax = plt.subplots(figsize=(10, 6))
    for i, day in enumerate(stats):
        values = [day[k] for k in keys]
        offset = (i - n / 2 + 0.5) * width
        ax.bar(x + offset, values, width * 0.9, label=day["date"],
               color=day_colors[i % len(day_colors)], edgecolor="white")
        for j, v in enumerate(values):
            ax.text(x[j] + offset, v + 1, f"{v:.0f}", ha="center", va="bottom", fontsize=8)

    ax.axhline(y=benchmark, color="#F44336", linestyle="--", linewidth=2,
               label=f"Benchmark: {benchmark:.0f} сек")
    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=12)
    ax.set_ylabel("Время (сек)", fontsize=11)
    ax.set_title(funnel_name, fontsize=14, fontweight="bold", pad=12)
    ax.legend(fontsize=10)
    _style(ax)
    return _save(fig)


def make_service_usage_chart(data: dict) -> io.BytesIO:
    service_name = data["service_name"]
    median_val = data["median_sessions"]
    entries = data["data"]

    dates = [e["date"] for e in entries]
    counts = [e["session_count"] for e in entries]

    fig, ax = plt.subplots(figsize=(12, 6))
    ax.bar(dates, counts, color="#42A5F5", edgecolor="white", label="Сессии")
    ax.axhline(y=median_val, color="#FF9800", linestyle="--", linewidth=2,
               label=f"Медиана: {median_val:.1f}")
    ax.set_xlabel("Дата", fontsize=11)
    ax.set_ylabel("Количество сессий", fontsize=11)
    ax.set_title(f"Использование: {service_name}", fontsize=14, fontweight="bold", pad=12)
    ax.tick_params(axis="x", rotation=45)
    ax.legend(fontsize=10)
    _style(ax)
    return _save(fig)


def make_industry_chart(data: dict) -> io.BytesIO:
    counts = data["industry_counts"]    # [{industry, count}]
    turnover = data["industry_turnover"]  # [{industry, total_inflow}]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 7))

    # Pie chart — количество бизнесов
    labels_pie = [d["industry"] for d in counts]
    values_pie = [d["count"] for d in counts]
    colors = plt.cm.Set3(np.linspace(0, 1, len(labels_pie)))
    ax1.pie(values_pie, labels=labels_pie, autopct="%1.1f%%", colors=colors,
            startangle=140, textprops={"fontsize": 9})
    ax1.set_title("Бизнесы по отраслям", fontsize=13, fontweight="bold", pad=12)

    # Bar chart — суммарный оборот по отраслям
    industries = [d["industry"] for d in turnover]
    inflows = [d["total_inflow"] / 1_000_000 for d in turnover]  # в млн
    bars = ax2.bar(industries, inflows, color="#5C6BC0", edgecolor="white")
    ax2.set_xlabel("Отрасль", fontsize=11)
    ax2.set_ylabel("Суммарный приток, млн руб.", fontsize=11)
    ax2.set_title("Приток по отраслям (all time)", fontsize=13, fontweight="bold", pad=12)
    ax2.tick_params(axis="x", rotation=40)
    for bar, val in zip(bars, inflows):
        ax2.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.5,
                 f"{val:.1f}", ha="center", va="bottom", fontsize=8)
    _style(ax2)

    return _save(fig)
