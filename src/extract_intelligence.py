import openai
import json
import os
from dotenv import load_dotenv

load_dotenv()

client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def extract_intelligence(transcript_text: str) -> dict:
    """
    Takes the full readable transcript text.
    Returns a structured dict with all extracted intelligence.
    """

    prompt = f"""You are an expert meeting analyst. Read the following meeting transcript carefully and extract structured information.

Return a JSON object with EXACTLY these keys. Do not add any extra text before or after the JSON.

{{
  "summary": "A 2-3 sentence overview of what the meeting was about and what was accomplished",
  
  "action_items": [
    {{
      "task": "Description of the task to be done",
      "assignee": "Name of the person responsible",
      "deadline": "YYYY-MM-DD format, estimate if not explicitly stated",
      "priority": "high, medium, or low"
    }}
  ],
  
  "decisions": [
    {{
      "decision": "What was decided",
      "rationale": "Why this decision was made"
    }}
  ],
  
  "risks": [
    "Risk or blocker mentioned in the meeting"
  ],
  
  "follow_up_needed": true or false,
  
  "follow_up_reason": "Reason a follow-up meeting is needed, or null if not needed",
  
  "parking_lot": [
    "Topic that was raised but deferred for a later meeting"
  ]
}}

Rules:
- If a field has no content, return an empty list [] or null
- For deadlines, use today's date as reference if relative terms like "next week" are used
- Only include what is actually mentioned in the transcript
- Do not invent information

TRANSCRIPT:
{transcript_text}"""

    print("Sending transcript to GPT-4o-mini for analysis...")

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": "You are an expert meeting analyst. Always respond with valid JSON only."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        response_format={"type": "json_object"},
        temperature=0.1
    )

    result = json.loads(response.choices[0].message.content)
    print("Extraction complete.")
    return result


def add_metadata(extracted: dict, transcript_data: dict, participants: list) -> dict:
    """
    Adds meeting metadata to the extracted intelligence.
    """
    from datetime import datetime

    extracted["meeting_id"] = transcript_data.get("transcript_id", "unknown")
    extracted["date"] = datetime.now().isoformat()
    extracted["participants"] = participants

    return extracted


if __name__ == "__main__":
    from transcribe import format_transcript_for_llm
    import json

    with open("data/transcript.json") as f:
        transcript_data = json.load(f)

    readable = format_transcript_for_llm(transcript_data)

    result = extract_intelligence(readable)

    result = add_metadata(
        result,
        transcript_data,
        participants=["alice@company.com", "ajukply@gmail.com"]
    )

    with open("data/extracted.json", "w") as f:
        json.dump(result, f, indent=2)

    print("\n--- Extracted Intelligence ---")
    print(json.dumps(result, indent=2))