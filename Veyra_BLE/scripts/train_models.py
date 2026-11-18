import joblib
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC

df = pd.read_csv("csi_features.csv")

meta_cols = ["filename", "round", "label_4class", "label_3class", "label_2class"]
feature_cols = [c for c in df.columns if c not in meta_cols]

models = {
    "Random Forest": RandomForestClassifier(n_estimators=200, random_state=42, class_weight="balanced"),
    "SVM (RBF Kernel)": make_pipeline(StandardScaler(), SVC(kernel="rbf", C=1.0, probability=True, random_state=42, class_weight="balanced")),
}

def evaluate_task(target_col, task_name):
    print("\n==========================================")
    print(f"TASK: {task_name}")
    print("==========================================")
    
    rounds = sorted(df["round"].unique())
    for model_name, model in models.items():
        y_true_all, y_pred_all = [], []
        for test_round in rounds:
            train_df = df[df["round"] != test_round]
            test_df = df[df["round"] == test_round]
            model.fit(train_df[feature_cols], train_df[target_col])
            preds = model.predict(test_df[feature_cols])
            y_true_all.extend(test_df[target_col])
            y_pred_all.extend(preds)
            
        acc = accuracy_score(y_true_all, y_pred_all)
        print(f"\n--- {model_name} | Cross-Round Accuracy: {acc:.2%} ---")
        print(classification_report(y_true_all, y_pred_all, zero_division=0))

evaluate_task("label_2class", "2-CLASS MOTION DETECTION (No Movement vs Movement)")
evaluate_task("label_3class", "3-CLASS CORE DETECTION (Empty vs Stationary vs Movement)")

# Save best 3-class model for Streamlit dashboard integration
final_model = RandomForestClassifier(n_estimators=200, random_state=42, class_weight="balanced")
final_model.fit(df[feature_cols], df["label_3class"])
joblib.dump({"model": final_model, "features": feature_cols}, "veyra_csi_model.joblib")
print("\nSaved trained model bundle to: veyra_csi_model.joblib")


