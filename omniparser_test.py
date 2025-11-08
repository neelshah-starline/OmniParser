#!/usr/bin/env C:\Users\%USERNAME%\AppData\Local\Programs\Python\Python312\python.exe

import os
import io
import time
import json
import base64
import logging
from pathlib import Path
from typing import List, Optional, Union

import numpy as np
import torch
import pyautogui
from PIL import Image

from util.utils import check_ocr_box, get_yolo_model, get_caption_model_processor, get_som_labeled_img

# Set OMP_NUM_THREADS to 1
os.environ["OMP_NUM_THREADS"] = "1"

# Initialize models
yolo_model = get_yolo_model(motdel_path='weights/icon_detect/model.pt')
caption_model_processor = get_caption_model_processor(model_name="florence2", model_name_or_path="weights/icon_caption_florence")

# Setup logging
logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')

# Default directory relative to script
default_dir = Path(__file__).parent / "imgs"

# Function to take a screenshot and save it
def take_screenshot(filename):
    screenshot = pyautogui.screenshot()
    screenshot.save(os.path.join(default_dir, filename))

# Function to parse the screenshot and save the parsed content
# Updated function to parse the screenshot and save the parsed content
def parse_screenshot(filename):
    image_path = os.path.join(default_dir, filename)
    image = Image.open(image_path)
    box_overlay_ratio = image.size[0] / 3200
    draw_bbox_config = {
        'text_scale': 0.8 * box_overlay_ratio,
        'text_thickness': max(int(2 * box_overlay_ratio), 1),
        'text_padding': max(int(3 * box_overlay_ratio), 1),
        'thickness': max(int(3 * box_overlay_ratio), 1),
    }
    ocr_bbox_rslt, is_goal_filtered = check_ocr_box(image_path, display_img=False, output_bb_format='xyxy', goal_filtering=None, easyocr_args={'paragraph': False, 'text_threshold':0.9}, use_paddleocr=False)
    text, ocr_bbox = ocr_bbox_rslt
    dino_labled_img, label_coordinates, parsed_content_list = get_som_labeled_img(image_path, yolo_model, BOX_TRESHOLD=0.05, output_coord_in_ratio=True, ocr_bbox=ocr_bbox, draw_bbox_config=draw_bbox_config, caption_model_processor=caption_model_processor, ocr_text=text, iou_threshold=0.1)
    image = Image.open(io.BytesIO(base64.b64decode(dino_labled_img)))

    # Remove the file extension from the filename
    filename_without_ext = os.path.splitext(filename)[0]

    # Save the parsed image output
    parsed_image_path = os.path.join(default_dir, f"{filename_without_ext}_parsed.png")
    image.save(parsed_image_path)

    print('finish processing')

    # Format parsed content list correctly for JSON
    parsed_content_dict = {f'{i}': v for i, v in enumerate(parsed_content_list)}

    # Save parsed content as JSON
    parsed_content_path = os.path.join(default_dir, f"{filename_without_ext}_parsed.json")
    with open(parsed_content_path, "w") as f:
        json.dump(parsed_content_dict, f)

    return image, parsed_content_dict, label_coordinates

# Function to click on a specific tag using the provided JSON file path
def click_on_tag(tag_id, json_file_path):
    print(tag_id, json_file_path)
    with open(json_file_path, "r") as f:
        parsed_content = json.load(f)

    for key, value in parsed_content.items():
        if key == str(tag_id):

            x = int(value['bbox'][0] * pyautogui.size().width)
            y = int(value['bbox'][1] * pyautogui.size().height)
            x_center = int((value['bbox'][0] + value['bbox'][2]) / 2 * pyautogui.size().width)
            y_center = int((value['bbox'][1] + value['bbox'][3]) / 2 * pyautogui.size().height)
            pyautogui.moveTo(x_center, y_center,1)
            pyautogui.click()
            print("mouse moved")

def list_directory(directory: Path) -> None:
    """List files in a directory."""
    files = list(directory.iterdir())
    if not files:
        print("📂 Directory is empty.")
    else:
        print("📁 Files in directory:")
        for f in files:
            print(f"- {f.name}")

def get_filenames_input() -> Union[List[str], str]:
    """Prompt for screenshot filenames or commands."""
    raw = input("Enter screenshot filenames (comma-separated), type 'list_dir' to view files, or 'n' to exit: ").strip()
    if raw.lower() == 'n':
        return []
    if raw.lower() == 'list_dir':
        return 'list_dir'
    return [f.strip() for f in raw.split(',') if f.strip()]


def process_file(filename: str, screenshot_dir: Path) -> None:
    """Process a single screenshot file."""
    time.sleep(1)  # Wait for the screenshot to be saved
    image, parsed_content_dict, label_coordinates = parse_screenshot(filename)
    filename_stem = Path(filename).stem
    json_file_path = screenshot_dir / f"{filename_stem}_parsed.json"
    logging.info(f"Processed {filename}, JSON saved at {json_file_path}")

# Main loop
def main_loop():
    while True:
        try:
            user_dir = input(f"Provide File Directory [default: {default_dir}]: ").strip()
            screenshot_dir = Path(user_dir) if user_dir else default_dir
            if not screenshot_dir.exists() or not screenshot_dir.is_dir():
                logging.error(f"❌ Directory '{screenshot_dir}' does not exist."); continue

            while True:
                filenames = get_filenames_input()
                if not filenames: logging.info("👋 Exiting program."); return
                if filenames == 'list_dir' : list_directory(screenshot_dir); continue
                for fname in filenames:
                    try: process_file(fname, screenshot_dir)
                    except Exception as e: logging.error(f"Failed to process '{fname}': {e}")
                break  # ask if they want to run again

            if input("Run again? (y/n): ").strip().lower() != 'y': break

        except KeyboardInterrupt:
            logging.warning("Interrupted by user."); break
        except Exception as e:
            logging.exception("Unexpected error.")
            if input("Try again? (y/n): ").strip().lower() != 'y': break


if __name__ == "__main__":
    main_loop()
