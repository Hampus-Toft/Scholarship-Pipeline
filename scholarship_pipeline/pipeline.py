import os

from .config import INPUT_FOLDER, OUTPUT_FILE, configure_binaries
from .io_utils import pdf_to_images, save_to_excel
from .ocr import extract_data
from .postprocess import finalize_record
from .preprocessing import preprocess_image


def process_document(image_path):
    processed = preprocess_image(image_path)
    return extract_data(processed)


def run_pipeline(input_folder=INPUT_FOLDER, output_file=OUTPUT_FILE):
    configure_binaries()
    results = []

    for file in sorted(os.listdir(input_folder)):
        path = os.path.join(input_folder, file)
        print(f"[INFO] Processing {file}")

        if file.lower().endswith(".pdf"):
            image_paths = pdf_to_images(path)

            for page_number, img_path in enumerate(image_paths, start=1):
                try:
                    data = process_document(img_path)
                    finalized = finalize_record(data, source_file=file, source_page=page_number)
                    results.append(finalized)
                finally:
                    if os.path.exists(img_path):
                        os.remove(img_path)

        elif file.lower().endswith((".jpg", ".jpeg", ".png")):
            data = process_document(path)
            finalized = finalize_record(data, source_file=file)
            results.append(finalized)

    save_to_excel(results, output_file=output_file)
    print(results)

    return results
