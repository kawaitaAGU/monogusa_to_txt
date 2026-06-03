import re
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="名前・正解数抽出",
    layout="centered"
)

st.title("名前・正解数抽出アプリ")

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

    for enc in [
        "utf-8-sig",
        "utf-8",
        "cp932",
        "shift_jis"
    ]:
        try:
            return raw.decode(enc)
        except Exception:
            pass

    return raw.decode(
        "utf-8",
        errors="ignore"
    )


def mask_name(name):
    name = re.sub(
        r"\s+",
        " ",
        name.strip()
    )

    parts = name.split(" ")

    if len(parts) >= 2:
        return (
            parts[0][0]
            + "****"
            + parts[1][-1]
        )

    if len(name) >= 2:
        return (
            name[0]
            + "****"
            + name[-1]
        )

    return name


def split_student_blocks(lines):

    blocks = []
    current = []

    for line in lines:

        line = line.strip()

        if not line:
            continue

        if re.fullmatch(
            r"\d{6,10}",
            line
        ):

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

        for line in block:

            if (
                re.search(
                    r"[一-龥ぁ-んァ-ン]",
                    line
                )
                and line not in [
                    "完了",
                    "未回答",
                    "回答中"
                ]
            ):
                name = line
                break

        for line in block:

            m = re.search(
                r"(\d+)\s*/\s*(\d+)\s*点?",
                line
            )

            if m:
                score = int(
                    m.group(1)
                )
                break

        if any(
            "未回答" in x
            for x in block
        ):
            score = 0

        if name is not None:

            if score is None:
                score = 0

            results.append(
                [
                    mask_name(name),
                    score
                ]
            )

    return results


# ------------------------
# 入力取得
# ------------------------

text = ""

if uploaded_file is not None:
    text = read_file(uploaded_file)

elif pasted_text.strip():
    text = pasted_text


# ------------------------
# 実行
# ------------------------

if text:

    results = extract_name_score(text)

    if results:

        st.subheader("抽出結果")

        df = pd.DataFrame(
            results,
            columns=[
                "名前",
                "正解数"
            ]
        )

        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True
        )

        st.success(
            "抽出完了しました。下のボタンからダウンロードできます。"
        )

        output_text = "名前,点数\n"

        for name, score in results:
            output_text += (
                f"{name},{score}\n"
            )

        st.download_button(
            label="TXTをダウンロード",
            data=output_text.encode(
                "utf-8-sig"
            ),
            file_name="name_score.txt",
            mime="text/plain"
        )

    else:
        st.warning(
            "抽出に失敗しました。"
        )
