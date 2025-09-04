import os
import re

md_folder = "./extrakty"
img_folder = "img"
pattern = re.compile(r"^Obr[.\s]+(\d+)[.\s]*(.*)", re.IGNORECASE)

def clean_caption(caption):
    # Odstraní pomlčky, dvojtečky, tečky a mezery na začátku titulku
    return re.sub(r"^[\s\-–:.\u2013]+", "", caption)

for filename in os.listdir(md_folder):
    if filename.endswith(".md"):
        filepath = os.path.join(md_folder, filename)
        new_lines = []

        with open(filepath, "r", encoding="utf-8") as f:
            lines = f.readlines()

        for line in lines:
            match = pattern.match(line.strip())
            if match:
                image_number = match.group(1)
                raw_caption = match.group(2).strip()
                caption = clean_caption(raw_caption)
                base_name = os.path.splitext(filename)[0]
                image_filename = f"{base_name}_image{image_number}.png"
                image_path = os.path.join(img_folder, image_filename).replace("\\", "/")
                markdown_image = f"![{caption}]({image_path})\n"
                new_lines.append(markdown_image)
            else:
                new_lines.append(line)

        with open(filepath, "w", encoding="utf-8") as f:
            f.writelines(new_lines)
        print(f"✅ Upraveno: {filename}")
