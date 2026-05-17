import pickle

with open("ml_models/risk_model.pkl", "rb") as f:
    model = pickle.load(f)

with open("ml_models/risk_vectorizer.pkl", "rb") as f:
    vectorizer = pickle.load(f)

text = ["Company has unstable cash flow and rising debt"]

X = vectorizer.transform(text)

print(X.shape)

prediction = model.predict(X)

print(prediction)