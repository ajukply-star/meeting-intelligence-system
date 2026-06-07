import json, sys
sys.path.insert(0, 'src')
from extract_intelligence import extract_intelligence

with open("data/synthetic/transcripts.json") as f:
    data = json.load(f)

for item in data[:3]:
    result = extract_intelligence(item["transcript"])
    print(f"\nMeeting Type : {item['type']}")
    print(f"Action Items : {len(result['action_items'])}")
    print(f"Decisions    : {len(result['decisions'])}")
    print(f"Risks        : {len(result['risks'])}")
    print(f"Follow Up    : {result['follow_up_needed']}")
    print(f"Parking Lot  : {len(result['parking_lot'])}")
    print("---")
