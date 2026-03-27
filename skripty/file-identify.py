import os
import re
import pandas as pd

CSV_PATH = r"c:\work\tnk136-extrakty\list-of-stds.txt"
ROOT_FOLDER = r"c:\_SP\tnk\projekty\01 extrakty\hotove\silmos"
OUTPUT_CSV = r"full_match_report.csv"

# === 1) Load CSV ===
df = pd.read_csv(CSV_PATH, sep="\t", encoding="utf-8-sig")

# Extract code from Norma (with or without part)
def extract_code(text):
    s = str(text)

    # Case 1: number with part (e.g. 14819-1 or 14819-01)
    m = re.search(r"(\d{4,5})-(\d+)", s)
    if m:
        base = m.group(1)
        suffix = str(int(m.group(2)))  # normalize 01 → 1
        return f"{base}-{suffix}"

    # Case 2: number without part (e.g. 14823)
    m = re.search(r"\b(\d{4,5})\b", s)
    if m:
        return m.group(1)

    return None

df["code"] = df["Norma"].apply(extract_code)
df = df[df["code"].notna()].copy()

# === 2) Scan folder structure ===
pattern = re.compile(r"(?i)extrakt[_ ](\d{4,5})(?:-(\d+))?")

files = []

for root, dirs, filelist in os.walk(ROOT_FOLDER):
    for f in filelist:
        try:
            m = pattern.search(f)
            if m:
                base = m.group(1)
                suffix = m.group(2)

                if suffix:
                    suffix = str(int(suffix))  # normalize 01 → 1
                    code = f"{base}-{suffix}"
                else:
                    code = base

                full_path = os.path.join(root, f)
                files.append((full_path, code))
        except Exception:
            pass

files_df = pd.DataFrame(files, columns=["file_path", "code"])

# === 3) FULL OUTER JOIN ===
merged = pd.merge(
    files_df,
    df,
    on="code",
    how="outer",
    indicator=True
)

merged.to_csv(OUTPUT_CSV, index=False, encoding="utf-8-sig")

print("Done. Output saved to:", OUTPUT_CSV)