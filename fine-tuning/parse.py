import json, os

from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

analyzer = SentimentIntensityAnalyzer()

def sentiment(text):
    compound = analyzer.polarity_scores(text)['compound']
    if compound > 0.05:
        return 'Positive'
    elif compound < -0.05:
        return 'Negative'
    return 'Neutral'

with open('train.json', 'r') as f:
    data = json.load(f)

moods = {
    'Positive': 0,
    'Negative': 0,
    'Neutral': 0
}
print("PARSING")
lines = []
for key in data.keys():
    for line in data[key]["content"]:
        mood = sentiment(line['message'])
        moods[mood] += 1
        lines.append(f"{line['agent']} <{mood}>: {line['message']}")
    lines.append("*"*20)

print("WRITING")
with open(f'conversation-sentiment.txt', 'w') as f:
    f.write("\n".join(lines))

print(moods)
