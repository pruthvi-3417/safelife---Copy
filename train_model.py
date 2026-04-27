import numpy as np
from sklearn.neighbors import KNeighborsClassifier
import pickle

print("🔧 Generating dataset...")

X = np.random.rand(1000, 9)
y = np.random.choice(["Low", "Medium", "High"], 1000)

print("🔍 Training KNN model...")

model = KNeighborsClassifier(n_neighbors=19)
model.fit(X, y)

with open("knn_model.pkl", "wb") as f:
    pickle.dump(model, f)

print("💾 Model saved successfully!")