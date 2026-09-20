import json
import pickle
from pathlib import Path

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression

project_dir = Path(__file__).resolve().parent
for file in ["intent.json", "genai_task_intent.json"]:
    with (project_dir / file).open(encoding="utf-8") as f:
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

    with (models_dir / f"intent_model_{file.split('.')[0]}.pkl").open("wb") as f:
        pickle.dump(model, f)

    with (models_dir / f"vectorizer_{file.split('.')[0]}.pkl").open("wb") as f:
        pickle.dump(vectorizer, f)

    print("Model trained!")