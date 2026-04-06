import os
import re
import csv

import pandas as pd
from pdf2image import convert_from_path

from .config import POPLER_PATH


def pdf_to_images(pdf_path):
    images = convert_from_path(
        pdf_path,
        dpi=300,
        poppler_path=POPLER_PATH,
    )

    image_paths = []
    base_name = os.path.splitext(os.path.basename(pdf_path))[0]
    safe_base_name = re.sub(r"[^A-Za-z0-9_-]", "_", base_name)

    for i, img in enumerate(images):
        temp_path = f"temp_{safe_base_name}_page_{i}.jpg"
        img.save(temp_path, "JPEG")
        image_paths.append(temp_path)

    return image_paths


def save_to_excel(data_list, output_file="output.xlsx"):
    df = pd.DataFrame(data_list)
    df.to_excel(output_file, index=False)
    print(f"[INFO] Saved to {output_file}")


def save_to_csv(data_list, output_file="output.csv"):
    df = pd.DataFrame(data_list)
    df.to_csv(output_file, index=False, quoting=csv.QUOTE_MINIMAL)
    print(f"[INFO] Saved to {output_file}")


def save_output(data_list, output_file="output.xlsx"):
    if output_file.lower().endswith(".csv"):
        save_to_csv(data_list, output_file=output_file)
        return

    save_to_excel(data_list, output_file=output_file)
