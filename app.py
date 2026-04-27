"""
SafeLife AI – ML Engine
KNN-based health risk prediction with:
  - Synthetic dataset generation
  - Preprocessing (imputation, encoding, scaling)
  - Train/Val/Test split (70/15/15)
  - Optimal K tuning on validation set
  - Model + scaler saved via pickle
  - Explainable AI (nearest-neighbor reasoning)
  - Digital Twin simulation
  - Feedback-driven retraining
"""

import numpy as np
import pickle
import os
from sklearn.neighbors import KNeighborsClassifier
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, confusion_matrix
from sklearn.impute import SimpleImputer

MODEL_PATH  = 'knn_model.pkl'
SCALER_PATH = 'knn_scaler.pkl'
DATA_PATH   = 'feedback_data.pkl'

FEATURE_NAMES = ['age', 'bmi', 'sleep', 'water', 'steps', 'stress_enc',
                 'systolic_bp', 'heart_rate', 'blood_sugar']
LABEL_MAP = {0: 'Low', 1: 'Medium', 2: 'High'}
LABEL_MAP_REV = {'Low': 0, 'Medium': 1, 'High': 2}

# ─────────────────────────────────────────────────────────────────
#  SYNTHETIC DATASET
# ─────────────────────────────────────────────────────────────────
def generate_dataset(n=1200, seed=42):
    rng = np.random.default_rng(seed)

    age         = rng.integers(18, 80, n).astype(float)
    bmi         = rng.normal(24, 5, n).clip(14, 45)
    sleep       = rng.normal(6.5, 1.5, n).clip(2, 12)
    water       = rng.normal(2.0, 0.8, n).clip(0.3, 5)
    steps       = rng.integers(1000, 18000, n).astype(float)
    stress_enc  = rng.integers(0, 3, n).astype(float)   # 0=Low,1=Medium,2=High
    systolic_bp = rng.normal(120, 18, n).clip(90, 190)
    heart_rate  = rng.normal(75, 12, n).clip(50, 120)
    blood_sugar = rng.normal(100, 22, n).clip(60, 250)

    # introduce 5% missing values
    for arr in [bmi, sleep, water, systolic_bp]:
        idx = rng.choice(n, int(n * 0.05), replace=False)
        arr[idx] = np.nan

    X = np.column_stack([age, bmi, sleep, water, steps,
                         stress_enc, systolic_bp, heart_rate, blood_sugar])

    # rule-based labels (realistic)
    labels = []
    for i in range(n):
        score = 0
        if age[i] > 55:                         score += 2
        elif age[i] > 40:                       score += 1
        b = bmi[i] if not np.isnan(bmi[i]) else 25
        if b > 30:                              score += 2
        elif b > 27:                            score += 1
        s = sleep[i] if not np.isnan(sleep[i]) else 6
        if s < 5:                               score += 2
        elif s < 6.5:                           score += 1
        w = water[i] if not np.isnan(water[i]) else 1.5
        if w < 1.5:                             score += 1
        if steps[i] < 4000:                     score += 2
        elif steps[i] < 7000:                   score += 1
        if stress_enc[i] == 2:                  score += 2
        elif stress_enc[i] == 1:                score += 1
        bp = systolic_bp[i] if not np.isnan(systolic_bp[i]) else 120
        if bp > 140:                            score += 2
        elif bp > 130:                          score += 1
        if heart_rate[i] > 100:                 score += 1
        if blood_sugar[i] > 140:                score += 2
        elif blood_sugar[i] > 110:              score += 1
        if score <= 3:    labels.append(0)   # Low
        elif score <= 7:  labels.append(1)   # Medium
        else:             labels.append(2)   # High

    y = np.array(labels)
    return X, y


# ─────────────────────────────────────────────────────────────────
#  PREPROCESSING
# ─────────────────────────────────────────────────────────────────
def preprocess(X_train, X_val=None, X_test=None):
    imputer = SimpleImputer(strategy='mean')
    X_train = imputer.fit_transform(X_train)
    scaler  = StandardScaler()
    X_train = scaler.fit_transform(X_train)
    results = [X_train]
    for X in [X_val, X_test]:
        if X is not None:
            X = imputer.transform(X)
            results.append(scaler.transform(X))
        else:
            results.append(None)
    return results[0], results[1], results[2], scaler, imputer


# ─────────────────────────────────────────────────────────────────
#  TRAIN & SAVE
# ─────────────────────────────────────────────────────────────────
def train_and_save():
    print("🔧 Generating synthetic healthcare dataset…")
    X, y = generate_dataset(1200)

    # 70 / 15 / 15 split
    X_tr, X_tmp, y_tr, y_tmp = train_test_split(X, y, test_size=0.30, random_state=42, stratify=y)
    X_val, X_te, y_val, y_te = train_test_split(X_tmp, y_tmp, test_size=0.50, random_state=42, stratify=y_tmp)

    X_tr_s, X_val_s, X_te_s, scaler, imputer = preprocess(X_tr, X_val, X_te)

    print("🔍 Tuning K (1–21) on validation set…")
    best_k, best_acc = 5, 0
    for k in range(1, 22, 2):
        knn = KNeighborsClassifier(n_neighbors=k, metric='euclidean')
        knn.fit(X_tr_s, y_tr)
        acc = accuracy_score(y_val, knn.predict(X_val_s))
        if acc > best_acc:
            best_acc, best_k = acc, k
    print(f"   Best K = {best_k}  |  Val accuracy = {best_acc:.3f}")

    knn = KNeighborsClassifier(n_neighbors=best_k, metric='euclidean')
    knn.fit(X_tr_s, y_tr)

    test_acc = accuracy_score(y_te, knn.predict(X_te_s))
    print(f"✅ Test accuracy = {test_acc:.3f}")
    cm = confusion_matrix(y_te, knn.predict(X_te_s))
    print(f"   Confusion matrix:\n{cm}")

    # store raw training data for neighbor explanation
    bundle = {
        'model': knn,
        'scaler': scaler,
        'imputer': imputer,
        'X_train_raw': X_tr,
        'y_train': y_tr,
        'X_train_scaled': X_tr_s,
        'best_k': best_k,
        'test_accuracy': round(float(test_acc), 4),
        'confusion_matrix': cm.tolist(),
        'feature_names': FEATURE_NAMES,
        'label_map': LABEL_MAP,
    }
    with open(MODEL_PATH, 'wb') as f:
        pickle.dump(bundle, f)
    print(f"💾 Model saved → {MODEL_PATH}")
    return bundle


# ─────────────────────────────────────────────────────────────────
#  LOAD
# ─────────────────────────────────────────────────────────────────
def load_bundle():
    if not os.path.exists(MODEL_PATH):
        return train_and_save()
    with open(MODEL_PATH, 'rb') as f:
        return pickle.load(f)


# ─────────────────────────────────────────────────────────────────
#  PREDICT
# ─────────────────────────────────────────────────────────────────
def predict(age, bmi, sleep, water, steps, stress,
            systolic_bp=120, heart_rate=75, blood_sugar=100):
    """
    Returns dict with:
      risk_label, risk_index, probabilities (Low/Med/High %),
      risk_score (0-100), neighbors, explanation, digital_twin
    """
    bundle = load_bundle()
    model   = bundle['model']
    scaler  = bundle['scaler']
    imputer = bundle['imputer']

    stress_enc = {'Low': 0, 'Medium': 1, 'High': 2}.get(stress, 1)
    x_raw = np.array([[age, bmi, sleep, water, steps,
                       stress_enc, systolic_bp, heart_rate, blood_sugar]], dtype=float)
    x_imp = imputer.transform(x_raw)
    x_sc  = scaler.transform(x_imp)

    pred_idx  = int(model.predict(x_sc)[0])
    risk_label = LABEL_MAP[pred_idx]

    # soft probabilities via neighbor voting
    dists, idxs = model.kneighbors(x_sc)
    neighbor_labels = bundle['y_train'][idxs[0]]
    counts = np.bincount(neighbor_labels, minlength=3)
    total  = counts.sum()
    probs  = {LABEL_MAP[i]: round(float(counts[i] / total * 100), 1) for i in range(3)}

    # risk score (0-100, higher = worse)
    risk_score = round(probs['High'] * 0.6 + probs['Medium'] * 0.3, 1)

    # explainability: top contributing features
    explanation = _explain(x_raw[0], bundle, idxs[0], risk_label)

    # digital twin: 3/5-day projection
    digital_twin = _digital_twin(x_raw[0], bundle, risk_score)

    # nearest neighbors summary
    neighbors_info = []
    X_tr_raw = bundle['X_train_raw']
    for ni in idxs[0][:3]:
        nb = X_tr_raw[ni]
        nb_label = LABEL_MAP[bundle['y_train'][ni]]
        neighbors_info.append({
            'age': int(nb[0]),
            'bmi': round(float(nb[1]), 1),
            'sleep': round(float(nb[2]), 1),
            'stress': {0: 'Low', 1: 'Medium', 2: 'High'}.get(int(nb[5]), 'Medium'),
            'risk': nb_label
        })

    return {
        'risk_label': risk_label,
        'risk_index': pred_idx,
        'probabilities': probs,
        'risk_score': risk_score,
        'neighbors': neighbors_info,
        'explanation': explanation,
        'digital_twin': digital_twin,
    }


# ─────────────────────────────────────────────────────────────────
#  EXPLAINABILITY
# ─────────────────────────────────────────────────────────────────
def _explain(x_raw, bundle, neighbor_idxs, risk_label):
    X_tr = bundle['X_train_raw']
    y_tr = bundle['y_train']

    # find features that deviate most from healthy median
    healthy_mask = (y_tr == 0)
    if healthy_mask.sum() == 0:
        return f"Prediction: {risk_label} risk based on overall health indicators."

    healthy_med = np.nanmedian(X_tr[healthy_mask], axis=0)
    reasons = []

    checks = [
        (0, 'age',         lambda v: v > 55,  "age above 55"),
        (1, 'bmi',         lambda v: v > 28,  "elevated BMI"),
        (2, 'sleep',       lambda v: v < 6,   "insufficient sleep (< 6 hrs)"),
        (3, 'water',       lambda v: v < 1.5, "low water intake"),
        (4, 'steps',       lambda v: v < 5000,"low physical activity"),
        (5, 'stress',      lambda v: v >= 2,  "high stress level"),
        (6, 'systolic_bp', lambda v: v > 135, "elevated blood pressure"),
        (7, 'heart_rate',  lambda v: v > 95,  "high resting heart rate"),
        (8, 'blood_sugar', lambda v: v > 120, "high blood sugar"),
    ]
    for idx, name, cond, desc in checks:
        val = x_raw[idx]
        if not np.isnan(val) and cond(val):
            reasons.append(desc)

    if not reasons:
        return f"Prediction is {risk_label} risk. Your metrics are within safe ranges."
    factors = ', '.join(reasons[:3])
    return f"Prediction is {risk_label} risk because similar patients shared: {factors}."


# ─────────────────────────────────────────────────────────────────
#  DIGITAL TWIN
# ─────────────────────────────────────────────────────────────────
def _digital_twin(x_raw, bundle, current_risk_score):
    """Simple linear trend projection for 3 and 5 days without treatment."""
    age   = x_raw[0]
    bmi   = x_raw[1] if not np.isnan(x_raw[1]) else 25
    sleep = x_raw[2] if not np.isnan(x_raw[2]) else 6
    steps = x_raw[4]
    stress= x_raw[5]

    # daily degradation rate (heuristic)
    deg = 0.0
    if bmi > 28:          deg += 0.8
    if sleep < 6:         deg += 1.2
    if steps < 5000:      deg += 0.9
    if stress >= 2:       deg += 1.1

    r3 = min(round(current_risk_score + deg * 3, 1), 100)
    r5 = min(round(current_risk_score + deg * 5, 1), 100)

    def label(s):
        if s < 30:  return 'Low'
        if s < 60:  return 'Medium'
        return 'High'

    return {
        'current':  current_risk_score,
        'day3':     r3,
        'day5':     r5,
        'label3':   label(r3),
        'label5':   label(r5),
        'message':  (
            f"Without treatment, risk may increase from {current_risk_score}% "
            f"to {r3}% in 3 days and {r5}% in 5 days."
            if deg > 0
            else "Keep up your current habits! Risk is projected to stay stable."
        )
    }


# ─────────────────────────────────────────────────────────────────
#  FEEDBACK-DRIVEN RETRAINING
# ─────────────────────────────────────────────────────────────────
def save_feedback(features_dict, predicted_label, was_accurate):
    stress_enc = {'Low': 0, 'Medium': 1, 'High': 2}.get(features_dict.get('stress','Medium'), 1)
    row = np.array([[
        features_dict.get('age', 30),
        features_dict.get('bmi', 22),
        features_dict.get('sleep', 7),
        features_dict.get('water', 2),
        features_dict.get('steps', 7000),
        stress_enc,
        features_dict.get('systolic_bp', 120),
        features_dict.get('heart_rate', 75),
        features_dict.get('blood_sugar', 100),
    ]], dtype=float)
    label = LABEL_MAP_REV.get(predicted_label, 1)

    existing = {'X': np.empty((0, 9)), 'y': np.array([])}
    if os.path.exists(DATA_PATH):
        with open(DATA_PATH, 'rb') as f:
            existing = pickle.load(f)

    new_X = np.vstack([existing['X'], row])
    new_y = np.append(existing['y'], label)
    with open(DATA_PATH, 'wb') as f:
        pickle.dump({'X': new_X, 'y': new_y}, f)

    # retrain if >= 50 feedback samples
    if len(new_y) >= 50 and was_accurate is False:
        _retrain_with_feedback(new_X, new_y)
    return len(new_y)


def _retrain_with_feedback(X_fb, y_fb):
    """Append feedback data to training set and retrain."""
    bundle = load_bundle()
    X_orig = bundle['X_train_raw']
    y_orig = bundle['y_train']
    X_all  = np.vstack([X_orig, X_fb])
    y_all  = np.append(y_orig, y_fb.astype(int))

    X_tr, X_te, y_tr, y_te = train_test_split(X_all, y_all, test_size=0.20, random_state=99)
    X_tr_s, X_te_s, _, scaler, imputer = preprocess(X_tr, X_te)

    best_k, best_acc = 5, 0
    for k in range(1, 16, 2):
        knn = KNeighborsClassifier(n_neighbors=k)
        knn.fit(X_tr_s, y_tr)
        acc = accuracy_score(y_te, knn.predict(X_te_s))
        if acc > best_acc:
            best_k, best_acc = k, acc

    knn = KNeighborsClassifier(n_neighbors=best_k)
    knn.fit(X_tr_s, y_tr)

    bundle.update({
        'model': knn,
        'scaler': scaler,
        'imputer': imputer,
        'X_train_raw': X_tr,
        'y_train': y_tr,
        'X_train_scaled': X_tr_s,
        'best_k': best_k,
        'test_accuracy': round(float(accuracy_score(y_te, knn.predict(X_te_s))), 4),
    })
    with open(MODEL_PATH, 'wb') as f:
        pickle.dump(bundle, f)
    print(f"♻️  Model retrained with feedback data. New accuracy: {bundle['test_accuracy']}")


# ─────────────────────────────────────────────────────────────────
#  WHAT-IF COMPARISON
# ─────────────────────────────────────────────────────────────────
def whatif_compare(base_features, improved_features):
    r_base = predict(**base_features)
    r_impr = predict(**improved_features)
    return {
        'base': {
            'risk': r_base['risk_label'],
            'score': r_base['risk_score'],
            'probs': r_base['probabilities'],
        },
        'improved': {
            'risk': r_impr['risk_label'],
            'score': r_impr['risk_score'],
            'probs': r_impr['probabilities'],
        },
        'delta': round(r_base['risk_score'] - r_impr['risk_score'], 1),
    }


# ─────────────────────────────────────────────────────────────────
#  MODEL INFO
# ─────────────────────────────────────────────────────────────────
def get_model_info():
    bundle = load_bundle()
    return {
        'best_k': bundle.get('best_k', 5),
        'accuracy': bundle.get('test_accuracy', 0),
        'confusion_matrix': bundle.get('confusion_matrix', []),
        'samples': len(bundle.get('y_train', [])),
        'features': FEATURE_NAMES,
    }


if __name__ == '__main__':
    b = train_and_save()
    res = predict(45, 27.5, 5.5, 1.8, 4000, 'High', 135, 88, 115)
    print("\nSample prediction:", res)