#!/usr/bin/env python3
"""
Standalone LM Studio Agent for OmniParser
Controls Windows desktop using local Qwen model via LM Studio
"""

import os
import sys
import time
import json
import base64
import requests
import pyautogui
from PIL import Image
import io
import argparse
from typing import Dict, Any, Optional

# Import OmniParser functionality directly
from util.utils import get_yolo_model, get_caption_model_processor, get_som_labeled_img
from omniparser_test import parse_screenshot

# Configuration
LM_STUDIO_URL = "http://127.0.0.1:1234/v1/chat/completions"
MODEL_NAME = "qwen/qwen3-vl-8b"

class LMStudioAgent:
    def __init__(self, lm_studio_url: str = LM_STUDIO_URL,
                 model_name: str = MODEL_NAME):
        self.lm_studio_url = lm_studio_url
        self.model_name = model_name
        self.conversation_history = []

        # Initialize OmniParser models directly
        print("🔧 Initializing OmniParser models...")
        self.yolo_model = get_yolo_model(model_path='weights/icon_detect/model.pt')
        self.caption_model_processor = get_caption_model_processor(
            model_name="florence2",
            model_name_or_path="weights/icon_caption_florence"
        )
        print("✅ OmniParser models loaded!")

        # Configure pyautogui
        pyautogui.FAILSAFE = True
        pyautogui.PAUSE = 0.5

        print("🤖 LM Studio Agent initialized!")
        print(f"🧠 LM Studio: {lm_studio_url}")
        print(f"📝 Model: {model_name}")

    def take_screenshot(self, step_num: int = 0) -> str:
        """Take screenshot of all monitors, save to file, and return as base64"""
        # Capture all monitors
        screenshot = pyautogui.screenshot(allScreens=True)
        print(f"📺 Captured all monitors: {screenshot.size}")

        # Save screenshot to file
        timestamp = int(time.time())
        filename = f"screenshots/screenshot_{timestamp}_step_{step_num}.png"
        screenshot.save(filename)
        print(f"💾 Screenshot saved: {filename}")

        # Convert to base64
        buffer = io.BytesIO()
        screenshot.save(buffer, format='PNG')
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
        return image_base64

    def analyze_screen(self, image_base64: str, step_num: int = 0) -> Dict[str, Any]:
        """Analyze screenshot with OmniParser directly"""
        try:
            # Convert base64 to PIL Image
            image_bytes = base64.b64decode(image_base64)
            image = Image.open(io.BytesIO(image_bytes))

            # Use the same logic as omniparser_test.py
            BOX_TRESHOLD = 0.05
            box_overlay_ratio = image.size[0] / 3200
            draw_bbox_config = {
                'text_scale': 0.8 * box_overlay_ratio,
                'text_thickness': max(int(2 * box_overlay_ratio), 1),
                'text_padding': max(int(3 * box_overlay_ratio), 1),
                'thickness': max(int(3 * box_overlay_ratio), 1),
            }

            # Check OCR box (same as parse_screenshot)
            from util.utils import check_ocr_box
            ocr_bbox_rslt, is_goal_filtered = check_ocr_box(
                image,  # Pass PIL Image directly
                display_img=False,
                output_bb_format='xyxy',
                goal_filtering=None,
                easyocr_args={'paragraph': False, 'text_threshold': 0.9},
                use_paddleocr=False
            )
            text, ocr_bbox = ocr_bbox_rslt

            # Get SOM labeled image and parsed content
            dino_labled_img, label_coordinates, parsed_content_list = get_som_labeled_img(
                image,  # Pass PIL Image directly
                self.yolo_model,
                BOX_TRESHOLD=BOX_TRESHOLD,
                output_coord_in_ratio=True,
                ocr_bbox=ocr_bbox,
                draw_bbox_config=draw_bbox_config,
                caption_model_processor=self.caption_model_processor,
                ocr_text=text,
                iou_threshold=0.1
            )

            # Save parsed SOM image for debugging
            timestamp = int(time.time())
            if dino_labled_img:
                som_image_bytes = base64.b64decode(dino_labled_img)
                som_image = Image.open(io.BytesIO(som_image_bytes))
                som_filename = f"screenshots/som_parsed_{timestamp}_step_{step_num}.png"
                som_image.save(som_filename)
                print(f"💾 SOM image saved: {som_filename}")

            # Save parsed content as JSON for debugging
            json_filename = f"screenshots/parsed_content_{timestamp}_step_{step_num}.json"
            with open(json_filename, 'w') as f:
                json.dump({"parsed_content_list": parsed_content_list}, f, indent=2)
            print(f"💾 Parsed content saved: {json_filename}")

            # Format the response to match what the agent expects
            return {
                "som_image_base64": dino_labled_img,
                "parsed_content_list": parsed_content_list,
                "width": image.size[0],
                "height": image.size[1]
            }

        except Exception as e:
            print(f"❌ OmniParser error: {e}")
            import traceback
            traceback.print_exc()
            return None

    def get_ai_decision(self, screen_info: str, task: str) -> Dict[str, Any]:
        """Get decision from LM Studio"""
        system_prompt = f"""You are an AI assistant controlling a Windows computer.

TASK: {task}

You can perform these actions:
- left_click: Click on element by Box ID
- right_click: Right-click on element by Box ID
- double_click: Double-click on element by Box ID
- type: Type text (provide "value" field)
- scroll_up: Scroll up
- scroll_down: Scroll down
- wait: Wait 1 second
- None: Task completed

SCREEN ELEMENTS:
{screen_info}

IMPORTANT: You MUST respond with ONLY valid JSON. No explanations, no markdown, just JSON.

Required JSON format:
{{
    "reasoning": "Brief explanation of what you see and your plan",
    "action": "action_type",
    "box_id": number (only for click actions),
    "value": "text to type" (only for type action)
}}

Examples:
{{"reasoning": "I see Chrome browser icon, clicking it to open", "action": "left_click", "box_id": 5}}
{{"reasoning": "Task completed after clicking the file", "action": "None"}}
{{"reasoning": "Need to type search query", "action": "type", "value": "hello world"}}
"""

        messages = [
            {"role": "system", "content": system_prompt},
            *self.conversation_history[-4:]  # Keep last 4 messages for context
        ]

        try:
            response = requests.post(
                self.lm_studio_url,
                json={
                    "model": self.model_name,
                    "messages": messages,
                    "max_tokens": 500,
                    "temperature": 0.1
                },
                timeout=60
            )
            response.raise_for_status()
            result = response.json()

            content = result["choices"][0]["message"]["content"]
            print(f"🧠 AI Response: {content}")

            # Extract JSON from response
            try:
                # Try to parse as direct JSON
                decision = json.loads(content.strip())
            except json.JSONDecodeError as e:
                print(f"⚠️ Direct JSON parsing failed: {e}")
                try:
                    # Try to extract JSON from markdown code blocks
                    import re
                    json_match = re.search(r'```json\s*(.*?)\s*```', content, re.DOTALL)
                    if json_match:
                        decision = json.loads(json_match.group(1).strip())
                    else:
                        # Fallback: look for JSON-like content
                        json_match = re.search(r'\{.*\}', content, re.DOTALL)
                        if json_match:
                            decision = json.loads(json_match.group(0))
                        else:
                            # Last resort: try to clean and parse
                            cleaned_content = content.strip()
                            if cleaned_content.startswith('{') and cleaned_content.endswith('}'):
                                decision = json.loads(cleaned_content)
                            else:
                                print(f"❌ Content doesn't look like JSON: {cleaned_content[:200]}...")
                                raise ValueError(f"No valid JSON found in response. Content: {content}")
                except json.JSONDecodeError as e2:
                    print(f"❌ JSON parsing failed: {e2}")
                    print(f"❌ Raw content: {repr(content)}")
                    raise ValueError(f"Could not parse JSON from AI response: {e2}")

            # Add to conversation history
            self.conversation_history.append({"role": "assistant", "content": content})

            return decision

        except Exception as e:
            print(f"❌ LM Studio error: {e}")
            return None

    def execute_action(self, action: str, box_id: Optional[int] = None,
                      value: Optional[str] = None, screen_data: Dict = None) -> bool:
        """Execute the AI's chosen action"""
        try:
            if action == "left_click" and box_id is not None:
                if screen_data and "parsed_content_list" in screen_data:
                    elements = screen_data["parsed_content_list"]
                    if 0 <= box_id < len(elements):
                        bbox = elements[box_id]["bbox"]
                        # Convert normalized coordinates to screen coordinates
                        screen_width, screen_height = pyautogui.size()
                        center_x = int((bbox[0] + bbox[2]) / 2 * screen_width)
                        center_y = int((bbox[1] + bbox[3]) / 2 * screen_height)

                        pyautogui.moveTo(center_x, center_y)
                        pyautogui.click()
                        print(f"🖱️ Left-clicked element {box_id} at ({center_x}, {center_y})")
                        return True

            elif action == "right_click" and box_id is not None:
                if screen_data and "parsed_content_list" in screen_data:
                    elements = screen_data["parsed_content_list"]
                    if 0 <= box_id < len(elements):
                        bbox = elements[box_id]["bbox"]
                        screen_width, screen_height = pyautogui.size()
                        center_x = int((bbox[0] + bbox[2]) / 2 * screen_width)
                        center_y = int((bbox[1] + bbox[3]) / 2 * screen_height)

                        pyautogui.moveTo(center_x, center_y)
                        pyautogui.rightClick()
                        print(f"🖱️ Right-clicked element {box_id} at ({center_x}, {center_y})")
                        return True

            elif action == "double_click" and box_id is not None:
                if screen_data and "parsed_content_list" in screen_data:
                    elements = screen_data["parsed_content_list"]
                    if 0 <= box_id < len(elements):
                        bbox = elements[box_id]["bbox"]
                        screen_width, screen_height = pyautogui.size()
                        center_x = int((bbox[0] + bbox[2]) / 2 * screen_width)
                        center_y = int((bbox[1] + bbox[3]) / 2 * screen_height)

                        pyautogui.moveTo(center_x, center_y)
                        pyautogui.doubleClick()
                        print(f"🖱️ Double-clicked element {box_id} at ({center_x}, {center_y})")
                        return True

            elif action == "type" and value:
                pyautogui.write(value)
                print(f"⌨️ Typed: '{value}'")
                return True

            elif action == "scroll_up":
                pyautogui.scroll(100)
                print("📜 Scrolled up")
                return True

            elif action == "scroll_down":
                pyautogui.scroll(-100)
                print("📜 Scrolled down")
                return True

            elif action == "wait":
                time.sleep(1)
                print("⏳ Waited 1 second")
                return True

            elif action in ["none", "None"]:
                print("✅ Task completed!")
                return True

            print(f"⚠️ Unknown or invalid action: {action}")
            return False

        except Exception as e:
            print(f"❌ Action execution error: {e}")
            return False

    def run_task(self, task: str, max_steps: int = 20) -> bool:
        """Run the complete task"""
        print(f"🎯 Starting task: {task}")
        print("=" * 50)

        self.conversation_history = [
            {"role": "user", "content": f"I need you to: {task}"}
        ]

        for step in range(max_steps):
            print(f"\n🔄 Step {step + 1}/{max_steps}")
            print("-" * 30)

            # Take screenshot
            print("📸 Taking screenshot...")
            screenshot_b64 = self.take_screenshot(step + 1)

            # Analyze screen
            print("🔍 Analyzing screen with OmniParser...")
            screen_data = self.analyze_screen(screenshot_b64, step + 1)

            if not screen_data:
                print("❌ Failed to analyze screen")
                return False

            # Format screen info for AI
            elements = screen_data.get("parsed_content_list", [])
            screen_info = "\n".join([
                f"Box {i}: {elem.get('content', 'Unknown')} ({elem.get('type', 'unknown')})"
                for i, elem in enumerate(elements)
            ])

            # Get AI decision
            print("🧠 Getting AI decision...")
            decision = self.get_ai_decision(screen_info, task)

            if not decision:
                print("❌ Failed to get AI decision")
                return False

            print(f"📋 Decision: {decision}")

            # Execute action
            action = decision.get("action", "").lower()
            box_id = decision.get("box_id")
            value = decision.get("value")

            if not self.execute_action(action, box_id, value, screen_data):
                print("❌ Failed to execute action")
                return False

            # Check if task is complete
            if action in ["none", "None"]:
                return True

            # For single-action tasks, check if the task description suggests completion
            task_lower = task.lower()
            reasoning = decision.get("reasoning", "").lower()

            # If the AI mentions task completion or just performed the requested action
            if ("complete" in reasoning or "done" in reasoning or
                "successfully" in reasoning or "finished" in reasoning):
                print("🎯 AI indicates task completion based on reasoning")
                return True

            # If it's a simple click task and we just clicked something
            if action == "left_click" and ("click" in task_lower or "open" in task_lower):
                print("🎯 Single-click task completed")
                return True

            # Wait a bit for UI to update
            time.sleep(2)

        print(f"⏰ Reached maximum steps ({max_steps})")
        return False


def main():
    parser = argparse.ArgumentParser(description="LM Studio Agent for OmniParser")
    parser.add_argument("task", help="Task description for the AI agent")
    parser.add_argument("--lm-studio-url", default=LM_STUDIO_URL,
                       help="LM Studio server URL")
    parser.add_argument("--model", default=MODEL_NAME,
                       help="Model name")
    parser.add_argument("--max-steps", type=int, default=20,
                       help="Maximum number of steps")

    args = parser.parse_args()

    # Check if LM Studio server is running
    print("🔍 Checking LM Studio server availability...")

    try:
        response = requests.get("http://127.0.0.1:1234/v1/models", timeout=5)
        if response.status_code == 200:
            models = response.json().get("data", [])
            model_names = [m["id"] for m in models]
            if MODEL_NAME in model_names:
                print(f"✅ LM Studio server is running with model '{MODEL_NAME}'")
            else:
                print(f"⚠️ LM Studio server running but model '{MODEL_NAME}' not found")
                print(f"   Available models: {model_names}")
                return
        else:
            print("❌ LM Studio server responded but not ready")
            return
    except:
        print("❌ LM Studio server not accessible at http://127.0.0.1:1234")
        print("   Make sure LM Studio is running with the server enabled")
        return

    # Create and run agent
    agent = LMStudioAgent(
        lm_studio_url=args.lm_studio_url,
        model_name=args.model
    )

    success = agent.run_task(args.task, args.max_steps)

    if success:
        print("\n🎉 Task completed successfully!")
    else:
        print("\n❌ Task failed or timed out")


if __name__ == "__main__":
    main()
