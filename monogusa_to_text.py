import re
import io
import numpy as np
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm

st.set_page_config(
    page_title="名前・正解数抽出",
    layout="centered"
)

st.title("名前・正解数抽出アプリ")

test_name = st.text_input(
    "テスト名を入力してください",
    value="name_score"
)

uploaded_file = st.file_uploader(
    "txt または csv ファイルをドラッグ＆ドロップしてください",
    type=["txt", "csv"]
)

pasted_text = st.text_area(
    "または、ここにデータを直接コピペしてください",
    height=300
)


def read_file(uploaded_file):
    raw = uploaded_file.read()

    for enc in ["utf-8-sig", "utf-8", "cp932", "shift_jis"]:
        try:
            return raw.decode(enc)
        except Exception:
            pass

    return raw.decode("utf-8", errors="ignore")


def mask_name(name):
    name = re.sub(r"\s+", " ", name.strip())
    parts = name.split(" ")

    if len(parts) >= 2:
        return parts[0][0] + "****" + parts[1][-1]

    if len(name) >= 2:
        return name[0] + "****" + name[-1]

    return name


def split_student_blocks(lines):
    blocks = []
    current = []

    for line in lines:
        line = line.strip()

        if not line:
            continue

        if re.fullmatch(r"\d{6,10}", line):
            if current:
                blocks.append(current)
            current = [line]
        else:
            current.append(line)

    if current:
        blocks.append(current)

    return blocks


def extract_name_score(text):
    lines = text.splitlines()
    blocks = split_student_blocks(lines)

    results = []

    for block in blocks:
        name = None
        score = None
        unanswered = False

        for line in block:
            if "未回答" in line:
                unanswered = True

        for line in block:
            if (
                re.search(r"[一-龥ぁ-んァ-ン]", line)
                and line not in ["完了", "未回答", "回答中"]
            ):
                name = line
                break

        for line in block:
            m = re.search(r"(\d+)\s*/\s*(\d+)\s*点?", line)
            if m:
                score = int(m.group(1))
                break

        if unanswered:
            score = 0

        if name is not None:
            if score is None:
                score = 0

            results.append({
                "名前": mask_name(name),
                "点数": score,
                "未回答": unanswered
            })

    return results


def get_japanese_font():
    preferred_fonts = [
        "Noto Sans CJK JP",
        "Noto Sans JP",
        "IPAexGothic",
        "IPAGothic",
        "Hiragino Sans",
        "Yu Gothic",
        "Meiryo"
    ]

    available_fonts = {
        f.name: f.fname for f in fm.fontManager.ttflist
    }

    for font_name in preferred_fonts:
        if font_name in available_fonts:
            return font_name

    return None


def make_graph(df, test_name):
    font_name = get_japanese_font()

    if font_name:
        plt.rcParams["font.family"] = font_name

    plt.rcParams["axes.unicode_minus"] = False

    answered_df = df[df["未回答"] == False]

    mean = answered_df["点数"].mean()
    sd = answered_df["点数"].std(ddof=0)

    names = df["名前"].tolist() + ["平均"]
    scores = df["点数"].tolist() + [mean]

    x = np.arange(len(names))

    fig, ax = plt.subplots(figsize=(max(10, len(names) * 0.45), 6))

    bars = ax.bar(x, scores)

    for i, bar in enumerate(bars):
        height = bar.get_height()
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            height + 0.2,
            f"{height:.1f}" if i == len(bars) - 1 else f"{int(height)}",
            ha="center",
            va="bottom",
            fontsize=9
        )

    mean_index = len(names) - 1

    ax.errorbar(
        mean_index,
        mean,
        yerr=sd,
        fmt="none",
        ecolor="black",
        capsize=6,
        linewidth=1.5
    )

    ax.axhline(mean, color="black", linewidth=1.2, label=f"平均 {mean:.2f}")
    ax.axhline(mean - sd, color="red", linewidth=1.0, label=f"平均−SD {mean - sd:.2f}")
    ax.axhline(mean + sd, color="yellow", linewidth=1.0, label=f"平均＋SD {mean + sd:.2f}")

    ax.text(
        0.02,
        0.95,
        f"平均 = {mean:.2f}\nSD = {sd:.2f}",
        transform=ax.transAxes,
        fontsize=12,
        va="top",
        bbox=dict(boxstyle="round", facecolor="white", alpha=0.8)
    )

    ax.set_title(test_name)
    ax.set_ylabel("点数")
    ax.set_xticks(x)
    ax.set_xticklabels(names, rotation=90)
    ax.legend()
    ax.grid(axis="y", linestyle="--", alpha=0.3)

    ymax = max(scores + [mean + sd]) + 3
    ax.set_ylim(0, ymax)

    fig.tight_layout()

    buffer = io.BytesIO()
    fig.savefig(buffer, format="png", dpi=200)
    plt.close(fig)
    buffer.seek(0)

    return buffer, mean, sd


text = ""

if uploaded_file is not None:
    text = read_file(uploaded_file)
elif pasted_text.strip():
    text = pasted_text


if text:
    results = extract_name_score(text)

    if results:
        df = pd.DataFrame(results)

        st.subheader("抽出結果")

        st.dataframe(
            df[["名前", "点数"]],
            use_container_width=True,
            hide_index=True
        )

        graph_buffer, mean, sd = make_graph(df, test_name)

        st.write(f"平均：{mean:.2f}")
        st.write(f"標準偏差：{sd:.2f}")

        st.image(graph_buffer)

        output_text = "名前,点数\n"

        for _, row in df.iterrows():
            output_text += f"{row['名前']},{row['点数']}\n"

        output_text += f"平均,{mean:.2f}\n"
        output_text += f"標準偏差,{sd:.2f}\n"

        st.download_button(
            label="TXTをダウンロード",
            data=output_text.encode("utf-8-sig"),
            file_name=f"{test_name}.txt",
            mime="text/plain"
        )

        st.download_button(
            label="PNGグラフをダウンロード",
            data=graph_buffer,
            file_name=f"{test_name}_グラフ.png",
            mime="image/png"
        )

    else:
        st.warning("抽出に失敗しました。")
