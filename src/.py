import assemblyai as aai
import json
import os
from dotenv import load_dotenv

load_dotenv()

aai.settings.api_key = os.getenv("ASSEMBLYAI_API_KEY")


def transcribe_audio(audio_path: str) -> dict:
    """
    Takes a path to an audio file.
    Returns a dict with speaker-labeled utterances.
    """
    print(f"Starting transcription for: {audio_path}")

    config = aai.TranscriptionConfig(
        speaker_labels=True,
        punctuate=True,
        format_text=True
    )

    transcriber = aai.Transcriber()
    transcript = transcriber.transcribe(audio_path, config=config)

    if transcript.status == aai.TranscriptStatus.error:
        raise Exception(f"Transcription failed: {transcript.error}")

    print(f"Transcription complete. {len(transcript.utterances)} utterances found.")

    result = {
        "transcript_id": transcript.id,
        "full_text": transcript.text,
        "utterances": []
    }

    for utterance in transcript.utterances:
        result["utterances"].append({
            "speaker": f"Speaker_{utterance.speaker}",
            "text": utterance.text,
            "start_ms": utterance.start,
            "end_ms": utterance.end
        })

    return result


def save_transcript(transcript_data: dict, output_path: str):
    with open(output_path, "w") as f:
        json.dump(transcript_data, f, indent=2)
    print(f"Transcript saved to: {output_path}")


def format_transcript_for_llm(transcript_data: dict) -> str:
    """
    Converts the JSON transcript into readable text for the LLM.
    Example: Speaker_A: Hello everyone...
    """
    lines = []
    for utterance in transcript_data["utterances"]:
        lines.append(f"{utterance['speaker']}: {utterance['text']}")
    return "\n".join(lines)


if __name__ == "__main__":
    transcript = transcribe_audio("data/test_meeting.mp3")
    save_transcript(transcript, "data/transcript.json")

    readable = format_transcript_for_llm(transcript)
    print("\n--- First 500 characters of readable transcript ---")
    print(readable[:500])