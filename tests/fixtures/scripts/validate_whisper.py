import os
import requests
import sys
import json
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

sys.path.insert(0, str(Path(__file__).parent.parent / "prompts"))
from whisper_test_prompt import whisper_test_prompt

OLLAMA_HOST = os.environ["OLLAMA_HOST"]

def normalize_whisper_transcript(whisper_transcript_path):
  whisper_json = json.loads(
    Path(whisper_transcript_path).read_text(encoding="utf-8")
  )
  return whisper_json["text"]

def generate_prompt(whisper_transcript_path, golden_transcript_path):
   whisper_transcript = normalize_whisper_transcript(whisper_transcript_path)
   golden_transcript = Path(golden_transcript_path).read_text(encoding="utf-8")
   return f"{whisper_test_prompt()} GOLDEN TRANSCRIPT: {golden_transcript} GENERATED TRANSCRIPT: {whisper_transcript}"

def receive_judgement(prompt):
    resp = requests.post(
        f"{OLLAMA_HOST}/api/generate",
        json={
            "model": "llama3.2:1b", 
            "prompt": prompt, 
            "stream": False
        },
    )
    return resp.json()

def validate_via_llm(whisper_transcript_path, golden_transcript_path):
   prompt = generate_prompt(whisper_transcript_path, golden_transcript_path)
   return receive_judgement(prompt)

if __name__ == "__main__":
    if len(sys.argv) < 2:
       print("Incorrect arguments! Please try again with: validate_whisper.py <whisper transcript path> <golden transcript path>")
    result = validate_via_llm(sys.argv[1], sys.argv[2])
    print(json.dumps(result, indent=2, ensure_ascii=False))