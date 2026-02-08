import os
import io
import time
import requests
from huggingface_hub import InferenceClient
from dotenv import load_dotenv

# ==========================================
# 1. ENVIRONMENT CONFIGURATION
# ==========================================
# Load environment variables from the .env file once
load_dotenv()

# Retrieve sensitive keys safely using os.getenv
# If the key is missing, it returns None instead of crashing the app
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
HF_TOKEN = os.getenv("HF_TOKEN")

# ==========================================
# 2. CLIENT INITIALIZATION
# ==========================================
def get_hf_client():
    """
    Initializes and returns the Hugging Face Inference Client.
    
    Returns:
        InferenceClient: The authenticated client object for image generation.
    """
    return InferenceClient(
        api_key=HF_TOKEN
    )

# ==========================================
# 3. TELEGRAM POLLING FUNCTION
# ==========================================
def get_prompt_from_tele(last_update_id):
    """
    Polls the Telegram API for new messages (Long Polling).

    Args:
        last_update_id (int): The ID of the last processed message + 1. 
                              This acts as an offset to prevent reading old messages.

    Returns:
        dict: A JSON dictionary containing the API response. 
              Returns an empty dict {} if the request fails.
    """
    
    # Construct the URL for the 'getUpdates' endpoint
    # timeout=30 keeps the connection open for 30s to wait for new messages (Long Polling)
    url_get_updates = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUpdates?timeout=30&offset={last_update_id}"

    try:
        # Send a GET request to Telegram
        response = requests.get(url_get_updates, timeout=35)
        
        # Parse and return the JSON response directly
        return response.json()

    except Exception as e:
        # SAFE ERROR HANDLING
        # We convert the error to string but DO NOT print it directly.
        error_str = str(e).lower()

        # --- DETECT ERROR TYPE SAFELY ---

        # CASE 1: Connection / DNS / Max Retries (The source of your previous leak)
        if "connection" in error_str or "max retries" in error_str or "failed to resolve" in error_str:
            print("❌ NETWORK ERROR: Failed to fetch updates from Telegram. Check internet/DNS.")

        # CASE 2: Read Timeout (Normal for Long Polling)
        elif "read timed out" in error_str:
            # This is actually normal in long polling if no message arrives in 30s.
            # We can print a soft log or nothing at all.
            print("⏳ Polling cycle refreshed (No new messages).")

        # CASE 3: SSL Errors
        elif "ssl" in error_str:
            print("🔒 SSL ERROR: Certificate verification failed.")

        # CASE 4: Unknown Error
        else:
            print("❌ POLLING ERROR: An unknown error occurred while fetching updates.")
            print("   (Error details hidden for security)")
        
        # Return an empty dictionary to ensure the main loop doesn't crash
        return {}

# ==========================================
# 4. IMAGE GENERATION FUNCTION
# ==========================================
def generate_img(prompt: str):
    """
    Generates an image based on the text prompt using the Fal AI model.
    Returns the image as a Byte Array (in-memory) for Telegram transmission.
    """
    
    # 1. INPUT VALIDATION
    # Ensure the prompt is valid before calling the expensive API
    if prompt is None or prompt.strip() == "":
        print("❌ Error: Received an empty prompt.")
        # We raise a ValueError so the Main Flow knows this step failed
        raise ValueError("Prompt cannot be empty or None.")

    print(f"🎨 Generating Image for: '{prompt}'")

    try:
        client = get_hf_client()

        # 2. CALL GENERATION API
        # Sending request to Black Forest Labs FLUX.1 model
        image = client.text_to_image(
            prompt,
            model="stabilityai/stable-diffusion-xl-base-1.0",
        )

        # 3. OUTPUT VALIDATION
        # Safety check: Ensure the API actually returned an object
        if not image:
            raise ValueError("API returned an empty result (No Image).")

        # 4. IMAGE PROCESSING (IN-MEMORY)
        # Create a virtual file in RAM (BytesIO) to avoid saving to hard drive
        img_bytes_arr = io.BytesIO()
        
        # Save the PIL image into the buffer as PNG format
        image.save(img_bytes_arr, format="PNG")
        
        # Reset the cursor to the beginning of the file so it can be read later
        img_bytes_arr.seek(0)
        
        print("✅ Image generated and converted to bytes successfully.")
        return img_bytes_arr

    except Exception as e:
        # 5. SAFE ERROR HANDLING
        # We convert the error to a string but DO NOT print it directly
        # because it might contain the HF_TOKEN in the headers.
        error_str = str(e).lower()

        # --- DETECT ERROR TYPE SAFELY ---

        # CASE 1: Authentication Error (Wrong Token)
        if "401" in error_str or "unauthorized" in error_str or "token" in error_str:
            print("🔒 AUTH ERROR: Hugging Face Token is invalid or missing.")

        # CASE 2: Rate Limit / Quota Exceeded (Free tier limits)
        elif "429" in error_str or "quota" in error_str:
            print("⏳ QUOTA ERROR: Hugging Face API rate limit reached. Please wait.")

        # CASE 3: Model Loading (Common in HF Inference API)
        elif "503" in error_str or "loading" in error_str:
            print("🏗️ MODEL BUSY: The model is currently loading on Hugging Face servers. Try again in 30s.")

        # CASE 4: Network/Connection Errors
        elif "connection" in error_str or "max retries" in error_str:
             print("❌ NETWORK ERROR: Failed to connect to Hugging Face API.")

        # CASE 5: API Key Quota / Credit Depleted
        elif "credit balance" in error_str or "depleted" in error_str or "429" in error_str:
            warning_msg = "💳 QUOTA EXCEEDED: Your Hugging Face credit balance is depleted. Purchase credits or upgrade to Pro."
            print(warning_msg)
            return warning_msg

        # CASE 6: Unknown Error
        else:
            print("🔥 GENERATION FAILED: An unknown error occurred during image generation.")
            print("   (Error details hidden for security)")

        return None

# ==========================================
# 5. TELEGRAM SEND FUNCTION
# ==========================================
def to_telegram(sender_name, chat_id, caption, img):
    """
    Sends the generated image and caption to the specified Telegram Chat.
    """

    if not TELEGRAM_TOKEN:
        print("❌ Error: Telegram credentials are missing.")
        return
    
    # 1. CONSTRUCT API URL
    url_send_photo = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"

    # 2. PREPARE FILE PAYLOAD
    # We must send the file as a tuple: (filename, file_data, mime_type)
    # This tells requests how to format the binary data properly.
    files = {
        "photo": ("generated_image.png", img, "image/png")
    }

    # 3. PREPARE DATA PAYLOAD
    # Note: Telegram API keys are case-sensitive. Use 'chat_id', not 'CHAT_ID'.
    data = {
        "chat_id": chat_id, 
        "caption": caption
    }

    print(f"🚀 Sending image to {sender_name} with Telegram Chat ID: {chat_id}...")

    try:
        # 4. Send the POST Request
        response = requests.post(url_send_photo, files=files, data=data, timeout=60)

        # 5. Validate Response
        if response.status_code == 200:
            print("✅ Success: Image delivered to Telegram!")
        else:
            # If the API returns an error (e.g., 400 Bad Request, 401 Unauthorized)
            print(f"❌ Telegram Refused: Status Code {response.status_code}")
            print(f"📄 Error Details: {response.text}")

    except Exception as e:
        # SAFETY CHECK: Do NOT print 'e' directly because it might contain the URL with the Token.
        error_str = str(e).lower()

        # --- SAFE ERROR HANDLING ---
        
        # CASE 1: Connection / DNS Issues
        if "connection" in error_str or "failed to resolve" in error_str or "max retries" in error_str:
            print(f"❌ NETWORK ERROR: Failed to send image to {sender_name}. Check internet/DNS.")
        
        # CASE 2: Timeout
        elif "timeout" in error_str:
            print(f"⏳ TIMEOUT ERROR: Sending image to {sender_name} timed out.")
        
        # CASE 3: SSL / Certificate Errors
        elif "ssl" in error_str or "certificate" in error_str:
             print("🔒 SSL ERROR: Connection failed due to SSL verification issues.")

        # CASE 4: Unknown Error
        else:
            print(f"❌ SENDING FAILED: An unknown error occurred while sending to {sender_name}.")
            print("   (Error details hidden for security)")

# ==========================================
# 5B. TELEGRAM SEND TEXT FUNCTION
# ==========================================
def send_information(sender_name, chat_id, information):
    """
    Sends a text message (information or warning) to a specific Telegram user.
    """
    
    # 1. Credential Check
    if not TELEGRAM_TOKEN:
        print("❌ Error: Telegram credentials are missing.")
        return

    # 2. Construct URL
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"

    # 3. Prepare Data
    data = {
        "chat_id": chat_id,
        "text": information,
        "parse_mode": "Markdown"
    }

    # 4. Log Action
    print(f"🚀 SENDING INFO TO {sender_name} (ID: {chat_id})...")

    try:
        # 5. Send POST request to Telegram API
        response = requests.post(url, json=data)
        
        # 6. Check HTTP Status Code (200 = OK)
        if response.status_code == 200:
            print("Status: ✅ Message delivered!")
        else:
            # Log the specific error from Telegram for debugging
            print(f"Status: ❌ Telegram Refused (Code: {response.status_code})")
            print(f"Details: {response.text}")
            
    except Exception as e:
        # 7. Safe Error Handling
        # Parse the error string to determine the cause
        error_str = str(e).lower()

        if "connection" in error_str or "dns" in error_str:
            print("Status: ❌ Network Error (Connection/DNS).")
        elif "timeout" in error_str:
            print("Status: ⏳ Timeout Error (No Response).")
        elif "ssl" in error_str:
            print("Status: 🔒 SSL Error (Certificate Failed).")
        else:
            print("Status: ❌ Send Failed (Unknown Error).")
    
# ==========================================
# 6. MAIN BOT LOOP (BACKGROUND PROCESS)
# ==========================================
def main():
    print("🤖 Bot is starting... Monitoring incoming messages...")
    
    # Initialize the offset to 0 to receive new messages
    last_update_id = 0

    while True:
        try:
            # Poll Telegram servers for new updates
            # 'last_update_id + 1' ensures we confirm previous messages and only get new ones
            data = get_prompt_from_tele(last_update_id + 1)
            
            # Print raw data only if there's actual content (prevents console spam)
            if "result" in data and len(data["result"]) > 0:
                print(f"\n📦 Update Received: {len(data['result'])} new message(s).")
            
            # Check if the 'result' key exists and contains messages
            if "result" in data and len(data["result"]) > 0:
                for message in data["result"]:
                    # Update the offset ID to acknowledge this message
                    last_update_id = message["update_id"]

                    # Ensure the update contains a valid text message
                    if "message" in message and "text" in message["message"]:
                        prompt = message["message"]["text"]
                        sender_name = message["message"].get("from", {}).get("first_name", "Unknown")
                        chat_id = message["message"].get("chat", {}).get("id", "Unknown")

                        # Log the received message details
                        print(f"📩 RECEIVED MESSAGE from [{sender_name}]: '{prompt}'")

                        # Generate image based on the user's prompt
                        result = generate_img(prompt)
                        
                        # If image generation was successful, send it back to Telegram
                        if result is None:
                            print("⚠️ Image generation failed (returned None).")
                            send_information(sender_name, chat_id, "❌ Sorry, failed to generate image due to server error.")
                        elif isinstance(result, str):
                            send_information(sender_name, chat_id, result)
                        else:
                            to_telegram(sender_name, chat_id, prompt, result)
                            print("✅ Image sent successfully.")           

            else:
                # No new messages found in this poll cycle
                print("💤 No new messages... Waiting...", end='\r')

            # Short delay to prevent hitting API rate limits
            time.sleep(1)

        except Exception as e:
            # 1. Convert error to string and lowercase for easy matching
            # We keep this in memory only, NEVER print it.
            error_str = str(e).lower()

            # --- IF-ELIF LOGIC TO DETECT ERROR TYPE ---

            # CASE 1: Connection / Internet / DNS Errors
            # (This was the cause of your previous token leak)
            if "connection" in error_str or "failed to resolve" in error_str or "max retries" in error_str:
                print("\n❌ NETWORK ERROR: Failed to connect to Telegram. Check your internet or DNS.")
            
            # CASE 2: Timeout Errors (Telegram is lagging)
            elif "timeout" in error_str:
                print("\n⏳ TIMEOUT ERROR: Telegram is not responding. Retrying...")

            # CASE 3: JSON Decoding Errors (Server might be down or returned HTML instead of JSON)
            elif "json" in error_str or "decode" in error_str:
                print("\n⚠️ API ERROR: Invalid response from Telegram (Server might be down).")

            # CASE 4: Unknown / Other Errors
            # We do NOT print 'e' here to protect your Token.
            else:
                print("\n❌ CRITICAL ERROR: An unknown internal error occurred.")
                print("   (Error details hidden for security)")

            # Pause before restarting to avoid CPU spam
            print("🔄 Restarting polling in 5 seconds...")
            time.sleep(5)

# ==========================================
# 7. EXECUTION
# ==========================================
if __name__ == "__main__":
    main()