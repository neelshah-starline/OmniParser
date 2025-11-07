#!/usr/bin/env python3

import os
import json
from pathlib import Path

from util.utils import get_yolo_model, get_caption_model_processor
from omniparser_test import parse_screenshot

# Initialize models
print("Loading models...")
yolo_model = get_yolo_model(model_path='weights/icon_detect/model.pt')
caption_model_processor = get_caption_model_processor(model_name="florence2", model_name_or_path="weights/icon_caption_florence")

# Test with google_page.png
filename = "google_page.png"
print(f"Processing {filename}...")

try:
    image, parsed_content_dict, label_coordinates = parse_screenshot(filename)
    print("✅ Processing completed successfully!")

    # Check if files were created
    default_dir = Path(__file__).parent / "imgs"
    json_file = default_dir / "google_page_parsed.json"
    png_file = default_dir / "google_page_parsed.png"

    if json_file.exists():
        print(f"✅ JSON file created: {json_file}")
        with open(json_file, 'r') as f:
            data = json.load(f)
            print(f"   Contains {len(data)} parsed elements")
    else:
        print(f"❌ JSON file not found: {json_file}")

    if png_file.exists():
        print(f"✅ PNG file created: {png_file}")
    else:
        print(f"❌ PNG file not found: {png_file}")

except Exception as e:
    print(f"❌ Error processing {filename}: {e}")
    import traceback
    traceback.print_exc()
