import os

from google import genai


def main():
    api_version = os.getenv("GEMINI_API_VERSION", "v1beta")
    client = genai.Client(http_options={"api_version": api_version})

    print(f"API version: {api_version}")
    print("Listing available models...")

    for model in client.models.list():
        name = getattr(model, "name", "")
        supported = getattr(model, "supported_generation_methods", [])
        print(f"- {name} | methods={supported}")


if __name__ == "__main__":
    main()

