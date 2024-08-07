import io
import os
import logging
from typing import Tuple, List, Optional

import pyautogui
from PIL import Image, ImageDraw
from google.cloud import vision

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class ScreenAnalyzer:
    def __init__(self, credentials_path: str = 'credentials.json'):
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = credentials_path
        self.vision_client = vision.ImageAnnotatorClient()

    def capture_screenshot(self, filename: str = 'screenshot.png') -> str:
        screenshot = pyautogui.screenshot()
        screenshot.save(filename)
        return filename

    def detect_text(self, image_path: str) -> List[vision.TextAnnotation]:
        with io.open(image_path, 'rb') as image_file:
            content = image_file.read()
        image = vision.Image(content=content)
        response = self.vision_client.text_detection(image=image)
        return response.text_annotations

    def find_element(self, text_to_find: str, screenshot_path: str = 'screenshot.png') -> Optional[Tuple[int, int]]:
        self.capture_screenshot(screenshot_path)
        texts = self.detect_text(screenshot_path)

        if not texts:
            logger.warning("No text found in the image.")
            return None

        target_text = next((text for text in texts[1:] if text.description.lower() == text_to_find.lower()), None)

        if target_text:
            vertices = target_text.bounding_poly.vertices
            center_x = (vertices[0].x + vertices[2].x) // 2
            center_y = (vertices[0].y + vertices[2].y) // 2
            return (center_x, center_y)
        else:
            logger.warning(f"Text '{text_to_find}' not found in the image.")
            return None

    def click_element(self, text_to_find: str, screenshot_path: str = 'screenshot.png') -> bool:
        element_position = self.find_element(text_to_find, screenshot_path)
        if element_position:
            pyautogui.click(element_position[0], element_position[1])
            logger.info(f"Clicked at position: {element_position}")
            return True
        return False

    def find_input_field(self, label_text: str, screenshot_path: str = 'screenshot.png', offset_y: int = 30) -> \
            Optional[Tuple[int, int]]:
        element_position = self.find_element(label_text, screenshot_path)
        if element_position:
            return (element_position[0], element_position[1] + offset_y)
        return None

    def input_text(self, label_text: str, text: str, screenshot_path: str = 'screenshot.png',
                   offset_y: int = 30) -> bool:
        input_position = self.find_input_field(label_text, screenshot_path, offset_y)
        if input_position:
            pyautogui.click(input_position[0], input_position[1])
            pyautogui.write(text)
            logger.info(f"Entered text '{text}' at position {input_position}")
            return True
        logger.warning(f"Failed to find input field with label '{label_text}'")
        return False

    def debug_screenshot(self, text_to_find: str, screenshot_path: str = 'screenshot.png'):
        element_position = self.find_element(text_to_find, screenshot_path)
        if element_position:
            debug_image = Image.open(screenshot_path)
            draw = ImageDraw.Draw(debug_image)
            draw.rectangle([
                (element_position[0] - 5, element_position[1] - 5),
                (element_position[0] + 5, element_position[1] + 5)
            ], outline="red", width=2)
            debug_filename = f'debug_{text_to_find.lower()}_screenshot.png'
            debug_image.save(debug_filename)
            logger.info(f"Saved debug screenshot: {debug_filename}")


class WindowManager:
    @staticmethod
    def find_window(title: str):
        windows = pyautogui.getWindowsWithTitle(title)
        if windows:
            logger.info(f"Found window with title '{title}'")
        else:
            logger.warning(f"No window found with title '{title}'")
        return windows

    @staticmethod
    def resize_window(window, width: int, height: int):
        window.resize(width, height)
        logger.info(f"Resized window to {width}x{height}")

    @staticmethod
    def move_window(window, x: int, y: int):
        window.move(x, y)
        logger.info(f"Moved window to position ({x}, {y})")

    @staticmethod
    def maximize_window(window):
        window.maximize()
        logger.info("Maximized window")

    @staticmethod
    def center_window(window):
        screen_width, screen_height = pyautogui.size()
        window_width, window_height = window.size
        new_x = (screen_width - window_width) // 2
        new_y = (screen_height - window_height) // 2
        WindowManager.move_window(window, new_x, new_y)
        logger.info("Centered window on screen")


# Usage example
if __name__ == "__main__":
    analyzer = ScreenAnalyzer()

    # Example: Find and click a button
    if analyzer.click_element("Submit"):
        logger.info("Successfully clicked the Submit button")
    else:
        logger.warning("Failed to click the Submit button")

    # Example: Input text into a field
    if analyzer.input_text("Username", "user_name"):
        logger.info("Successfully entered username")
    else:
        logger.warning("Failed to enter username")

    # Example: Resize and center a window
    windows = WindowManager.find_window("Example Application")
    if windows:
        window = windows[0]
        WindowManager.resize_window(window, 800, 600)
        WindowManager.center_window(window)
        logger.info("Window resized and centered")
    else:
        logger.warning("Failed to find and manipulate window")
