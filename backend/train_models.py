import os
import joblib
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report

# Setup paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
MODEL_DIR = os.path.join(BASE_DIR, "app", "models", "saved_models")

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(MODEL_DIR, exist_ok=True)

DATASET_PATH = os.path.join(DATA_DIR, "sample_textile_dataset.csv")

def generate_synthetic_dataset(num_samples=2500):
    """
    Generates a synthetic textile recycling dataset mimicking the rules 
    of the original rule-based classifiers but with some random noise.
    """
    print(f"Generating synthetic dataset with {num_samples} samples...")
    np.random.seed(42)

    # 1. Continuous feature generation
    # std_dev (weave contrast): Denim/Wool are rough (>22), Silk/Cotton/Nylon are smooth (<22)
    std_dev = np.random.normal(18, 8, num_samples)
    std_dev = np.clip(std_dev, 2, 55)

    # color_variance: printed (>25), plain (<25)
    color_variance = np.random.normal(20, 12, num_samples)
    color_variance = np.clip(color_variance, 0.5, 90)

    # damage_score & contamination_score (range 0 to 1)
    damage_score = np.random.beta(0.5, 1.5, num_samples)  # skewed towards low damage
    contamination_score = np.random.beta(0.5, 1.5, num_samples)  # skewed towards low contamination

    # RGB values
    red = np.random.randint(0, 256, num_samples)
    green = np.random.randint(0, 256, num_samples)
    blue = np.random.randint(0, 256, num_samples)

    # Color Name probabilities
    color_names_pool = ["Blue", "White", "Beige", "Grey", "Brown", "Black", "Pink", "Yellow", "Red", "Green"]
    color_name = np.random.choice(color_names_pool, num_samples)

    # 2. Boolean proxies
    is_rough = std_dev > 22.0
    is_printed = color_variance > 25.0
    damage_detected = damage_score > 0.18
    contamination_detected = contamination_score > 0.15

    # 3. Fabric Type labeling based on rules + 8% noise
    fabric_types = []
    for idx in range(num_samples):
        c = color_name[idx]
        rough = is_rough[idx]
        printed = is_printed[idx]

        if c == "Blue" and rough:
            choice = "Denim"
        elif c in ("Beige", "White") and rough and not printed:
            choice = "Linen"
        elif rough and c in ("Grey", "Brown", "Black"):
            choice = "Wool"
        elif not rough and not printed and c in ("White", "Pink", "Yellow"):
            choice = "Silk"
        elif printed:
            choice = "Polyester"
        elif not rough and c in ("Grey", "Blue"):
            choice = "Nylon"
        else:
            choice = "Cotton"

        # Inject noise (8% probability of random fabric type)
        if np.random.rand() < 0.08:
            choice = np.random.choice(["Denim", "Linen", "Wool", "Silk", "Polyester", "Nylon", "Cotton"])
        fabric_types.append(choice)

    # 4. Quality labeling + 5% noise
    qualities = []
    for idx in range(num_samples):
        dmg = damage_detected[idx]
        contam = contamination_detected[idx]
        
        if dmg and contam:
            choice = "low"
        elif dmg or contam:
            choice = "medium"
        else:
            choice = "high"

        # Inject noise
        if np.random.rand() < 0.05:
            choice = np.random.choice(["low", "medium", "high"])
        qualities.append(choice)

    # 5. Waste Category labeling + 5% noise
    waste_categories = []
    for idx in range(num_samples):
        q = qualities[idx]
        f = fabric_types[idx]
        dmg = damage_detected[idx]
        contam = contamination_detected[idx]
        c = color_name[idx]

        if q == "high":
            choice = "Reusable"
        elif q == "medium":
            if dmg and not contam:
                choice = "Repairable"
            else:
                choice = "Upcyclable"
        else: # low quality
            natural_fibers = ("Cotton", "Linen", "Wool")
            if f in natural_fibers and not contam:
                choice = "Compostable"
            elif contam and c in ("Black", "Grey"):
                choice = "Hazardous"
            else:
                choice = "Recyclable"

        # Inject noise
        if np.random.rand() < 0.05:
            choice = np.random.choice(["Reusable", "Repairable", "Upcyclable", "Compostable", "Hazardous", "Recyclable"])
        waste_categories.append(choice)

    df = pd.DataFrame({
        "std_dev": std_dev,
        "color_variance": color_variance,
        "damage_score": damage_score,
        "contamination_score": contamination_score,
        "red": red,
        "green": green,
        "blue": blue,
        "color_name": color_name,
        "is_rough": is_rough.astype(int),
        "is_printed": is_printed.astype(int),
        "damage_detected": damage_detected.astype(int),
        "contamination_detected": contamination_detected.astype(int),
        "fabric_type": fabric_types,
        "quality": qualities,
        "waste_category": waste_categories
    })
    
    df.to_csv(DATASET_PATH, index=False)
    print(f"Synthetic dataset saved to {DATASET_PATH}")
    return df

def train_models():
    # Load dataset or generate synthetic
    if os.path.exists(DATASET_PATH):
        print(f"Loading existing dataset from {DATASET_PATH}...")
        df = pd.read_csv(DATASET_PATH)
    else:
        df = generate_synthetic_dataset()

    print("\n--- Training Fabric Type Classifier ---")
    # Features for Fabric Type: continuous + categorical
    fabric_features = ["std_dev", "color_variance", "red", "green", "blue", "color_name", "is_rough", "is_printed"]
    X_fab = df[fabric_features]
    y_fab = df["fabric_type"]

    X_train_fab, X_test_fab, y_train_fab, y_test_fab = train_test_split(X_fab, y_fab, test_size=0.2, random_state=42)

    # Define Preprocessor
    numeric_features = ["std_dev", "color_variance", "red", "green", "blue"]
    categorical_features = ["color_name", "is_rough", "is_printed"]
    
    preprocessor = ColumnTransformer(
        transformers=[
            ("num", StandardScaler(), numeric_features),
            ("cat", OneHotEncoder(handle_unknown="ignore"), categorical_features)
        ]
    )

    # Define Pipeline
    fabric_pipeline = Pipeline(steps=[
        ("preprocessor", preprocessor),
        ("classifier", RandomForestClassifier(n_estimators=100, random_state=42, max_depth=12))
    ])

    # Fit & evaluate
    fabric_pipeline.fit(X_train_fab, y_train_fab)
    y_pred_fab = fabric_pipeline.predict(X_test_fab)
    print("Fabric Type Accuracy:", (y_pred_fab == y_test_fab).mean())
    print(classification_report(y_test_fab, y_pred_fab))

    # Save
    joblib.dump(fabric_pipeline, os.path.join(MODEL_DIR, "fabric_classifier.joblib"))
    print("Saved fabric_classifier.joblib")


    print("\n--- Training Quality Classifier ---")
    # Features for Quality: damage and contamination
    quality_features = ["damage_score", "contamination_score", "damage_detected", "contamination_detected"]
    X_q = df[quality_features]
    y_q = df["quality"]

    X_train_q, X_test_q, y_train_q, y_test_q = train_test_split(X_q, y_q, test_size=0.2, random_state=42)

    quality_pipeline = Pipeline(steps=[
        ("scaler", StandardScaler()),
        ("classifier", RandomForestClassifier(n_estimators=50, random_state=42, max_depth=6))
    ])

    quality_pipeline.fit(X_train_q, y_train_q)
    y_pred_q = quality_pipeline.predict(X_test_q)
    print("Quality Classifier Accuracy:", (y_pred_q == y_test_q).mean())
    print(classification_report(y_test_q, y_pred_q))

    # Save
    joblib.dump(quality_pipeline, os.path.join(MODEL_DIR, "quality_classifier.joblib"))
    print("Saved quality_classifier.joblib")


    print("\n--- Training Waste Category Classifier ---")
    # Waste Category depends on: fabric_type, quality, damage, contamination, color_name, etc.
    waste_features = [
        "damage_score", "contamination_score", 
        "damage_detected", "contamination_detected", 
        "color_name", "fabric_type", "quality"
    ]
    X_w = df[waste_features]
    y_w = df["waste_category"]

    X_train_w, X_test_w, y_train_w, y_test_w = train_test_split(X_w, y_w, test_size=0.2, random_state=42)

    numeric_w = ["damage_score", "contamination_score"]
    categorical_w = ["damage_detected", "contamination_detected", "color_name", "fabric_type", "quality"]

    preprocessor_w = ColumnTransformer(
        transformers=[
            ("num", StandardScaler(), numeric_w),
            ("cat", OneHotEncoder(handle_unknown="ignore"), categorical_w)
        ]
    )

    waste_pipeline = Pipeline(steps=[
        ("preprocessor", preprocessor_w),
        ("classifier", RandomForestClassifier(n_estimators=100, random_state=42, max_depth=12))
    ])

    waste_pipeline.fit(X_train_w, y_train_w)
    y_pred_w = waste_pipeline.predict(X_test_w)
    print("Waste Category Accuracy:", (y_pred_w == y_test_w).mean())
    print(classification_report(y_test_w, y_pred_w))

    # Save
    joblib.dump(waste_pipeline, os.path.join(MODEL_DIR, "waste_classifier.joblib"))
    print("Saved waste_classifier.joblib")
    
    print("\nAll models trained and saved to:", MODEL_DIR)

if __name__ == "__main__":
    train_models()
