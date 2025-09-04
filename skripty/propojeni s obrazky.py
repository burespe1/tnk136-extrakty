import os
import re
from collections import defaultdict

md_folder = "./extrakty"
img_folder = "./img"

# Mapování obrázků podle prefixu normy
image_map = defaultdict(list)
for img_file in os.listdir(img_folder):
    if img_file.lower().endswith((".png", ".jpg", ".jpeg", ".emf")):
        prefix = "_".join(img_file.split("_")[:2])
        image_map[prefix].append(img_file)

# Regexy pro různé formáty titulků
regex_obr = re.compile(r"^Obr[.\s]+(\d+)[.\s]*[–—-]?\s*(.*)", re.IGNORECASE)
regex_obrazek = re.compile(r"^\*\*Obrázek\s+(\d+)\s*[–—-]?\s*(.*?)\*\*", re.IGNORECASE)

for filename in os.listdir(md_folder):
    if filename.endswith(".md"):
        filepath = os.path.join(md_folder, filename)
        base_name = os.path.splitext(filename)[0]
        prefix = "_".join(base_name.split("_")[:2])
        images_for_doc = image_map.get(prefix, [])

        new_lines = []
        image_counter = 0

        with open(filepath, "r", encoding="utf-8") as f:
            lines = f.readlines()

        for line in lines:
            stripped = line.strip()
            match_obr = regex_obr.match(stripped)
            match_obrazek = regex_obrazek.match(stripped)

            if (match_obr or match_obrazek) and image_counter < len(images_for_doc):
                image_number = match_obr.group(1) if match_obr else match_obrazek.group(1)
                caption_text = match_obr.group(2).strip() if match_obr else match_obrazek.group(2).strip()
                caption_text_clean = re.sub(r"^[–—-]\s*", "", caption_text)

                image_filename = images_for_doc[image_counter]
                image_path = f"./img/{image_filename}".replace("\\", "/")

                markdown_image = f"![{caption_text_clean}]({image_path})\n"
                formatted_caption = f"**Obr. {image_number}.** {caption_text}\n"

                new_lines.append(markdown_image)
                new_lines.append(formatted_caption)
                image_counter += 1
            else:
                new_lines.append(line)

        with open(filepath, "w", encoding="utf-8") as f:
            f.writelines(new_lines)
        print(f"✅ Upraveno: {filename}")
