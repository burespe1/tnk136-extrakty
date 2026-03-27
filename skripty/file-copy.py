import os
import re
import shutil
import pandas as pd

CSV_PATH = r"c:\work\tnk136-extrakty\list-of-stds.txt"
ROOT_FOLDER = r"c:\_SP\tnk\projekty\01 extrakty\hotove\silmos"
OUTPUT_CSV = r"full_match_report.csv"

# === 1) Load CSV ===
df = pd.read_csv(CSV_PATH, sep="\t", encoding="utf-8-sig")

def extract_code(text):
    s = str(text)

    # Case 1: number with part (14819-1 or 14819-01)
    m = re.search(r"(\d{4,5})-(\d+)", s)
    if m:
        base = m.group(1)
        suffix = str(int(m.group(2)))  # normalize 01 → 1
        return f"{base}-{suffix}"

    # Case 2: number without part (14823)
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
                    suffix = str(int(suffix))
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
print("Audit saved to:", OUTPUT_CSV)

# === 4) COPY MATCHED FILES ===
copy_count = 0

for idx, row in merged.iterrows():
    if row["_merge"] != "both":
        continue  # only matched files

    file_path = row["file_path"]
    code = row["code"]
    wg = row["WG"]

    if pd.isna(file_path) or pd.isna(wg):
        continue

    # Extract year from path
    m = re.search(r"(20[0-3][0-9])", file_path)
    year = m.group(1) if m else "0000"

    # Extension
    ext = os.path.splitext(file_path)[1]

    # Destination folder
    dest_folder = os.path.join("WG", str(wg))
    os.makedirs(dest_folder, exist_ok=True)

    # Destination filename
    dest_name = f"extract_{code}_({year}){ext}"
    dest_path = os.path.join(dest_folder, dest_name)

    # Copy
    shutil.copy2(file_path, dest_path)
    copy_count += 1

print(f"Copied {copy_count} matched files.")