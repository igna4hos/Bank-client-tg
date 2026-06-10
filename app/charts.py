import io

import matplotlib
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt


def _apply_style(ax: plt.Axes) -> None:
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(axis="y", alpha=0.3, linestyle="--")


def make_friction_chart(data: dict) -> io.BytesIO:
    """Столбчатый график min/avg/median/max с горизонтальной линией benchmark."""
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
        ax.bar(
            x + offset, values, width * 0.9,
            label=day["date"],
            color=day_colors[i % len(day_colors)],
            edgecolor="white",
        )
        for j, v in enumerate(values):
            ax.text(
                x[j] + offset, v + 1, f"{v:.0f}",
                ha="center", va="bottom", fontsize=8, color="#333333",
            )

    ax.axhline(
        y=benchmark, color="#F44336", linestyle="--", linewidth=2,
        label=f"Benchmark: {benchmark:.0f} сек",
    )

    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=12)
    ax.set_ylabel("Время (сек)", fontsize=11)
    ax.set_title(funnel_name, fontsize=14, fontweight="bold", pad=12)
    ax.legend(fontsize=10)
    _apply_style(ax)

    buf = io.BytesIO()
    plt.tight_layout()
    plt.savefig(buf, format="png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return buf


def make_service_usage_chart(data: dict) -> io.BytesIO:
    """Столбчатый график сессий по дням с пунктирной линией медианы."""
    service_name = data["service_name"]
    median_val = data["median_sessions"]
    entries = data["data"]

    dates = [e["date"] for e in entries]
    counts = [e["session_count"] for e in entries]

    fig, ax = plt.subplots(figsize=(12, 6))

    ax.bar(dates, counts, color="#42A5F5", edgecolor="white", label="Сессии")
    ax.axhline(
        y=median_val, color="#FF9800", linestyle="--", linewidth=2,
        label=f"Медиана: {median_val:.1f}",
    )

    ax.set_xlabel("Дата", fontsize=11)
    ax.set_ylabel("Количество сессий", fontsize=11)
    ax.set_title(f"Использование: {service_name}", fontsize=14, fontweight="bold", pad=12)
    ax.tick_params(axis="x", rotation=45)
    ax.legend(fontsize=10)
    _apply_style(ax)

    buf = io.BytesIO()
    plt.tight_layout()
    plt.savefig(buf, format="png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return buf
