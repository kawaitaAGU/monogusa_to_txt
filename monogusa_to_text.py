import re
import html
from pathlib import Path
import streamlit as st

st.set_page_config(page_title="名前・正解数抽出", layout="centered")

st.title("名前・正解数抽出アプリ")

uploaded_file = st.file_uploader(
    "txt または csv ファイルをドラッグ＆ドロップしてください",
    type=["txt", "csv"]
)

pasted_text = st.text_area(
    "または、ここにデータを直接コピペしてください",
    height=250
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

        if any("未回答" in x for x in block):
            score = 0

        if name is not None:
            if score is None:
                score = 0

            results.append([
                mask_name(name),
                score
            ])

    return results


def make_html_table(results):
    rows = ""

    for name, score in results:
        rows += f"""
        <tr>
            <td style="border:1px solid #ccc;padding:6px;">
                {html.escape(str(name))}
            </td>
            <td style="border:1px solid #ccc;padding:6px;text-align:right;">
                {html.escape(str(score))}
            </td>
        </tr>
        """

    return f"""
    <table style="border-collapse: collapse; width:100%;">
        <thead>
            <tr>
                <th style="border:1px solid #ccc;padding:6px;">名前</th>
                <th style="border:1px solid #ccc;padding:6px;">正解数</th>
            </tr>
        </thead>
        <tbody>
            {rows}
        </tbody>
    </table>
    """


def save_to_desktop(results):
    desktop = Path.home() / "Desktop"
    path = desktop / "name_score.txt"

    with open(path, "w", encoding="utf-8-sig") as f:
        f.write("名前,点数\n")
        for name, score in results:
            f.write(f"{name},{score}\n")

    return path


text = ""

if uploaded_file is not None:
    text = read_file(uploaded_file)

elif pasted_text.strip():
    text = pasted_text


if text:
    results = extract_name_score(text)

    if results:
        st.subheader("抽出結果")

        st.markdown(
            make_html_table(results),
            unsafe_allow_html=True
        )

        saved = save_to_desktop(results)

        st.success(f"Desktop保存完了: {saved}")

        output_text = "名前,点数\n"
        for name, score in results:
            output_text += f"{name},{score}\n"

        st.download_button(
            label="TXTをダウンロード",
            data=output_text.encode("utf-8-sig"),
            file_name="name_score.txt",
            mime="text/plain"
        )

    else:
        st.warning("抽出失敗")