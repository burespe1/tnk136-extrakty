import os
import shutil

# Cesta k rootu, kde se skript spouští
root_dir = os.getcwd()

# Projde všechny složky v rootu
for norm_folder in os.listdir(root_dir):
    norm_path = os.path.join(root_dir, norm_folder)
    
    # Ověří, že jde o složku a že název vypadá jako číslo normy
    if os.path.isdir(norm_path) and norm_folder.startswith("21219-"):
        media_path = os.path.join(norm_path, "word", "media")
        
        # Pokud existuje složka s obrázky
        if os.path.exists(media_path):
            for filename in os.listdir(media_path):
                source_file = os.path.join(media_path, filename)
                
                # Vytvoří nový název: číslo_normy_název_souboru
                new_filename = f"{norm_folder}_{filename}"
                destination_file = os.path.join(root_dir, new_filename)
                
                # Zkopíruje soubor do rootu
                shutil.copy2(source_file, destination_file)
                print(f"Zkopírováno: {source_file} → {destination_file}")
