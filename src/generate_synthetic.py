import openai
import json
import os
from dotenv import load_dotenv

load_dotenv()

client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

MEETING_TYPES = [
    "sprint planning",
    "design review",
    "executive strategy check-in",
    "bug triage",
    "product roadmap discussion",
    "budget review"
]

PARTICIPANTS = ["Alice (PM)", "Bob (Engineer)", "Carol (Designer)", "Dave (Manager)"]


def generate_one_transcript(meeting_type: str) -> dict:
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "user",
                "content": f"""Generate a realistic {meeting_type} meeting transcript 
between these participants: {', '.join(PARTICIPANTS)}.

The meeting should be 10-15 exchanges long and must contain:
- At least 3 clear action items with specific owners and deadlines
- At least 2 decisions that were made with clear reasoning
- At least 1 risk or blocker mentioned
- At least 1 topic that gets deferred to a later meeting
- Natural conversation, disagreements, and follow-up questions

Format each line as:
Name: dialogue

Start directly with the conversation. No introduction text."""
            }
        ],
        temperature=0.8
    )

    return {
        "type": meeting_type,
        "transcript": response.choices[0].message.content
    }


def generate_all_transcripts(total: int = 30):
    transcripts = []
    per_type = total // len(MEETING_TYPES)

    for meeting_type in MEETING_TYPES:
        print(f"Generating {per_type} {meeting_type} transcripts...")
        for i in range(per_type):
            try:
                t = generate_one_transcript(meeting_type)
                transcripts.append(t)
                print(f"  {i+1}/{per_type} done")
            except Exception as e:
                print(f"  Error: {e}")

    os.makedirs("data/synthetic", exist_ok=True)
    with open("data/synthetic/transcripts.json", "w") as f:
        json.dump(transcripts, f, indent=2)

    print(f"\nSaved {len(transcripts)} transcripts to data/synthetic/transcripts.json")
    return transcripts


if __name__ == "__main__":
    generate_all_transcripts(30)