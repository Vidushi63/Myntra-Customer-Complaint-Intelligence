import os
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI

# Load .env from the same directory as this file
env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(env_path)

api_key = os.getenv("NVIDIA_API_KEY")

if not api_key:
    raise ValueError(
        "NVIDIA_API_KEY was not found. Check your .env file."
    )

client = OpenAI(
    base_url="https://integrate.api.nvidia.com/v1",
    api_key=os.getenv("NVIDIA_API_KEY")
)

def ask_ai(prompt: str, system_prompt: str = "You are a helpful assistant.") -> str:
    """
    Sends a query to NVIDIA API and returns the text response.
    """
    try:
        response = client.chat.completions.create(
           model="nvidia/nemotron-3.5-bolt-e4b",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            temperature=0.4,
            max_tokens=1024
        )
        return response.choices[0].message.content
    except Exception as e:
        print("Error type:", type(e).__name__)
        print("Full error:", repr(e))

        if hasattr(e, "response") and e.response is not None:
            print("Response details:", e.response.text)

        return "API request failed. Check the error above."