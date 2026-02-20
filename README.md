# 🎨 Real-Time AI Image Bot: Telegram Integration

![Python](https://img.shields.io/badge/Python-3.9%2B-blue?logo=python&logoColor=white)
![HuggingFace](https://img.shields.io/badge/AI-Stable%20Diffusion%20XL-FFD21E?logo=huggingface&logoColor=black)
![Telegram](https://img.shields.io/badge/Telegram-Long%20Polling-26A5E4?logo=telegram&logoColor=white)
![Status](https://img.shields.io/badge/Status-Active-success)

## 📌 Overview
**Real-Time AI Image Bot** is an interactive chatbot that brings **Stable Diffusion XL** directly to your Telegram interface.

Unlike scheduled pipelines, this bot runs on a **Long Polling** architecture using raw **HTTP Requests**, allowing it to respond **automatically** to user messages without needing a webhook or external libraries like `python-telegram-bot`. It manually hits the Telegram `getUpdates` endpoint, processes text prompts via **Hugging Face's Inference API**, and replies with high-quality generated images in **seconds**.

## ✨ Key Features

### 🤖 On-Demand AI Generation
* **Instant Inference:** Integrates `huggingface_hub.InferenceClient` to generate images using the `stabilityai/stable-diffusion-xl-base-1.0` model.
* **Smart Feedback:** Handles API limits and failures gracefully. If the quota is exceeded or a server error occurs (returning `None`), the bot replies with a notification message instead of failing silently.
* **In-Memory Processing:** Utilizes `io.BytesIO` to handle image data in RAM, ensuring zero disk footprint and faster delivery.

### 🛡️ Resilience & Security
* **Manual Long Polling:** Implements a custom `get_prompt_from_tele` function that directly queries the Telegram API, giving full control over the polling loop.
* **Safe Error Handling:** Categorizes errors (Network, SSL, Timeout, Auth) and logs them cleanly without leaking sensitive API tokens in the console.
* **Graceful Recovery:** Automatically handles timeouts and network fluctuations with retry logic and sleep intervals.

### 📨 Interactive Delivery
* **Direct Reply:** Sends the generated image back to the specific user/chat ID that requested it.
* **Captioning:** Automatically attaches the user's original prompt as the image caption for context.

## 🛠️ Tech Stack
* **Core:** Python 3.9+
* **AI Provider:** Hugging Face Inference API
* **Communication:** Telegram Bot API (Raw HTTP Requests via `requests`)
* **Image Processing:** Pillow (PIL) & IO
* **Config:** Python-Dotenv

## 🚀 The Workflow
1.  **Poll:** The bot continuously checks Telegram for new messages by hitting the `getUpdates` endpoint manually.
2.  **Extract:** It parses the JSON response to get the `chat_id`, `sender_name`, and `text prompt`.
3.  **Generate:** The prompt is sent to Hugging Face.
    * *If Success:* Returns Image Bytes (RAM).
    * *If Quota Full:* Returns a warning string (Text).
    * *If Critical Error:* Returns `None` (System Failure).
4.  **Send:**
    * *If Image Bytes:* Uploads via `sendPhoto` endpoint with caption.
    * *If String (Quota):* Sends the warning text via `sendMessage` endpoint.
    * *If None (Error):* Sends a generic "Server Error" notification via `sendMessage` endpoint.
5.  **Loop:** The bot sleeps for 1 second and repeats the cycle.

## ⚙️ Configuration (Environment Variables)
Create a `.env` file in the root directory:
```ini
TELEGRAM_TOKEN=your_telegram_bot_token
HF_TOKEN=your_huggingface_read_token
```

## 📦 Local Installation

1. **Clone the Repository**
```bash
git clone https://github.com/viochris/telegram-ai-bot.git
cd telegram-ai-bot
```

2. **Install Dependencies**
```bash
pip install -r requirements.txt
# Requires: requests, huggingface_hub, python-dotenv, pillow
```

3. **Run the Bot**
```bash
python img_maker_tele.py
```

### 🖥️ Expected Output
You will see the bot polling and processing requests in real-time:
```text
🤖 Bot is starting... Monitoring incoming messages...
💤 No new messages... Waiting...
📦 Update Received: 1 new message(s).
📩 RECEIVED MESSAGE from [Silvio]: 'A futuristic city made of crystal, 8k resolution'
🎨 Generating Image for: 'A futuristic city made of crystal, 8k resolution'
✅ Image generated and converted to bytes successfully.
🚀 Sending image to Silvio with Telegram Chat ID: 123456789...
✅ Success: Image delivered to Telegram!
```

## 🚀 Deployment
This script is designed to be **Always On**. It is best deployed on:
* **Docker Container** (using the provided Dockerfile).
* **VPS** (Virtual Private Server) like DigitalOcean or AWS EC2.
* **Hugging Face Spaces** (as a Docker Space).
* **Railway** (PaaS) for seamless GitHub integration and continuous deployment.

---

**Author:** [Silvio Christian, Joe](https://www.linkedin.com/in/silvio-christian-joe)
*"Turning text into art, one message at a time."*
