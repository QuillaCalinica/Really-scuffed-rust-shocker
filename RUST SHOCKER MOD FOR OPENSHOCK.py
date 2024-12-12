import pyautogui
import pytesseract
import numpy as np
import cv2
import time
import tkinter as tk
import requests
import json
from threading import Thread

# Set the tesseract path if needed
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# Global variables for the shocker control API
api_token = "PUT YOUR API TOKEN HERE"
hub_token = "PUT YOUR HUB TOKEN HERE"
shocker_id = "SHOCKER ID HERE"  # Updated shocker ID
url = "https://api.openshock.app/2/shockers/control"  # OpenShock API URL

# Define the region for the screenshot (updated region)
screen_width, screen_height = pyautogui.size()

# 5 more pixels to the right and 10 pixels wider (as per the previous adjustments)
region_width = 50 + 5  # 5 pixels wider
region_height = 30  # As adjusted earlier (20 pixels smaller)
region_x = screen_width - region_width - 150 - 25 - 20 - 50 + 5 + 15 + 15  # 15 pixels to the right
region_y = screen_height - region_height - 150 + 25 + 5 + 5

region = (region_x, region_y, region_width, region_height)

# Create a tkinter window to display the extracted number
def create_window():
    root = tk.Tk()
    root.title("Extracted Number")
    root.geometry("150x50+{}+{}".format(screen_width - 160, 10))  # Top-right corner
    root.attributes("-topmost", True)  # Always on top
    root.configure(bg='black')  # Background color
    label = tk.Label(root, text="", font=("Helvetica", 24), fg="white", bg="black")
    label.pack(fill=tk.BOTH, expand=True)

    return root, label

# Function to send the shock command
def send_shock():
    payload = {
        "shocks": [
            {
                "id": shocker_id,
                "type": "Shock",  # "Shock" type
                "intensity": 10,  # Intensity set to 10%
                "duration": 1000,  # Duration set to 1 second (1000 milliseconds)
                "exclusive": True  # Exclusive shock flag
            }
        ],
        "customName": "Test Shock Command"  # Optional custom name for the command
    }

    headers = {
        "Open-Shock-Token": api_token,
        "Hub-Token": hub_token,
        "Content-Type": "application/json"
    }

    response = requests.post(url, headers=headers, data=json.dumps(payload))

    print("Request URL:", url)
    print("Response Status Code:", response.status_code)
    print("Response Text:", response.text)

    if response.status_code == 200:
        print("Shock sent successfully!")
        print(response.json())  # Print the response if the shock was successfully sent
    else:
        print(f"Error {response.status_code}: {response.text}")

# Function to update the text in the window and track the number
def update_window(label):
    previous_number = None  # Variable to store the last number

    while True:
        screenshot = pyautogui.screenshot(region=region)
        screenshot = np.array(screenshot)
        screenshot = cv2.cvtColor(screenshot, cv2.COLOR_RGB2BGR)

        # Convert to grayscale for better OCR
        gray = cv2.cvtColor(screenshot, cv2.COLOR_BGR2GRAY)

        # Apply adaptive thresholding (or simple thresholding)
        _, thresholded = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)
        # Alternatively, use cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)

        # Apply noise removal (morphological operation)
        kernel = np.ones((2, 2), np.uint8)
        cleaned = cv2.morphologyEx(thresholded, cv2.MORPH_CLOSE, kernel)

        # Tesseract config for digits only
        custom_config = r'--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789'
        extracted_text = pytesseract.image_to_string(cleaned, config=custom_config).strip()

        if extracted_text.isdigit():
            current_number = int(extracted_text)

            # Display the extracted number in the tkinter window
            label.config(text=str(current_number))

            # Check if the number has decreased and trigger the shock
            if previous_number is not None and current_number < previous_number:
                # Change color to yellow when the shock is sent
                label.config(fg="yellow")
                send_shock()  # Trigger the shock if the number decreased

                # Reset the color back to white after a brief pause
                time.sleep(1)
                label.config(fg="white")

            previous_number = current_number  # Update the previous number

        time.sleep(0.1)  # Update every 0.1 seconds (lower delay)

# Create the tkinter window and label
root, label = create_window()

# Start the update function in a separate thread to update the window in real-time
thread = Thread(target=update_window, args=(label,))
thread.daemon = True  # Allow the thread to exit when the main program exits
thread.start()

# Start the tkinter main loop to display the window
root.mainloop()
