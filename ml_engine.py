def predict(age, bmi, sleep, water, steps, stress,
            systolic_bp, heart_rate, blood_sugar):

    score = 0

    if bmi > 30:
        score += 2
    if sleep < 6:
        score += 2
    if steps < 5000:
        score += 2
    if stress == 'High':
        score += 2
    if systolic_bp > 140:
        score += 2

    if score <= 2:
        label = 'Low'
    elif score <= 5:
        label = 'Medium'
    else:
        label = 'High'

    return {
        'risk_label': label,
        'risk_score': score * 10,
        'probabilities': {
            'Low': 30,
            'Medium': 40,
            'High': 30
        },
        'explanation': f'Predicted risk is {label}',
        'digital_twin': {
            'current': score * 10,
            'day3': score * 12,
            'day5': score * 14,
            'label3': label,
            'label5': label,
            'message': 'Maintain healthy lifestyle'
        }
    }


def get_model_info():
    return {
        "model": "Dummy Model",
        "accuracy": "Not trained yet"
    }


def whatif_compare(base, improved):
    return {
        "before": {"risk": "Medium"},
        "after": {"risk": "Low"}
    }


def save_feedback(features, label, correct):
    return 1