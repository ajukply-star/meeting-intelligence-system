from gtts import gTTS
import os

os.makedirs("data", exist_ok=True)

meeting_text = """
Alice: Good morning everyone. Let us start the sprint planning meeting.
Bob: Sure. I think we need to finish the login feature by next Friday.
Alice: Agreed. Bob can you take ownership of that task?
Bob: Yes I will handle it by Friday.
Alice: Carol can you review the design mockups by Wednesday?
Carol: Sure I will get that done by Wednesday.
Bob: One risk I see is the API dependency from the backend team.
Alice: Good point. Let us flag that as a blocker.
Carol: Should we schedule a follow up meeting to review progress?
Alice: Yes let us meet again next Monday.
Bob: Also the database migration discussion should move to next meeting.
Alice: Agreed, parking that for later. Thanks everyone.
"""

tts = gTTS(text=meeting_text, lang='en', slow=False)
tts.save("data/test_meeting.mp3")
print("Audio file created at data/test_meeting.mp3")
