import os

from .config import INPUT_FOLDER, OUTPUT_FILE, configure_binaries
from .io_utils import pdf_to_images, save_output
from .ocr import extract_data
from .postprocess import finalize_record, merge_page_records
from .preprocessing import preprocess_image


def process_document(image_path, page_number=None):
    processed = preprocess_image(image_path)
    return extract_data(processed, page_number=page_number)


def run_pipeline(input_folder=INPUT_FOLDER, output_file=OUTPUT_FILE):
    configure_binaries()
    results = []

    for file in sorted(os.listdir(input_folder)):
        path = os.path.join(input_folder, file)
        print(f"[INFO] Processing {file}")

        if file.lower().endswith(".pdf"):
            image_paths = pdf_to_images(path)
            page_records = []

            for page_number, img_path in enumerate(image_paths, start=1):
                try:
                    data = process_document(img_path, page_number=page_number)
                    finalized = finalize_record(data, source_file=file, source_page=page_number)
                    page_records.append(finalized)
                finally:
                    if os.path.exists(img_path):
                        os.remove(img_path)

            if page_records:
                results.append(merge_page_records(page_records))

        elif file.lower().endswith((".jpg", ".jpeg", ".png")):
            data = process_document(path)
            finalized = finalize_record(data, source_file=file)
            results.append(finalized)

    save_output(results, output_file=output_file)
    print(results)

    return results
