import json

with open('plutus.json', encoding='utf-8') as f:
    data = json.load(f)

print("Available validators:")
for v in data['validators']:
    print(f"  - {v['title']}")
