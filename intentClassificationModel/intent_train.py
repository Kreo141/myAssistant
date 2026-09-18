import json
import pickle
from pathlib import Path

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression

project_dir = Path(__file__).resolve().parent
with (project_dir / "intent.json").open(encoding="utf-8") as f:
    data = json.load(f)

sentences = []
labels = []

for intent in data["intents"]:
    for example in intent["examples"]:
        sentences.append(example)
        labels.append(intent["name"])

vectorizer = TfidfVectorizer()
X = vectorizer.fit_transform(sentences)

model = LogisticRegression()
model.fit(X, labels)

models_dir = project_dir / "models"
models_dir.mkdir(exist_ok=True)

with (models_dir / "intent_model.pkl").open("wb") as f:
    pickle.dump(model, f)

with (models_dir / "vectorizer.pkl").open("wb") as f:
    pickle.dump(vectorizer, f)

print("Model trained!")