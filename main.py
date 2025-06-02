import os
import sys
import pandas as pd
import mlflow
from src.utils import setup_mlflow
from src.data_preprocessing import (
    load_and_preprocess_data, split_data, 
    preprocess_features, encode_target
)
from src.feature_selection import (
    evaluate_feature_selection_chi2, 
    evaluate_feature_importance
)
from src.model_training import (
    apply_smote_tomek, 
    train_and_evaluate_model
)

def main():
    """Main training pipeline"""
    print("🚀 Starting Disease Diagnosis ML Pipeline with MLflow")
    
    # Setup MLflow
    experiment_name = setup_mlflow()
    print(f"📊 MLflow experiment: {experiment_name}")
    print(f"🌐 MLflow UI: http://localhost:5000")
    
    # Load and preprocess data
    print("\n📂 Loading and preprocessing data...")
    data_path = "data/disease_diagnosis.csv"
    
    if not os.path.exists(data_path):
        print(f"❌ Error: File {data_path} not found!")
        print("Please make sure to place your CSV file in the data/ directory")
        return
    
    X, y = load_and_preprocess_data(data_path)
    X_train, X_val, X_test, y_train, y_val, y_test = split_data(X, y)
    
    print(f"📊 Data shapes:")
    print(f"   Train: {X_train.shape}, Val: {X_val.shape}, Test: {X_test.shape}")
    
    # Preprocess features
    print("\n⚙️ Preprocessing features...")
    X_train, X_val, X_test, label_encoder = preprocess_features(X_train, X_val, X_test)
    y_train, y_val, y_test, diagnosis_encoding = encode_target(y_train, y_val, y_test)
    
    # Feature selection
    print("\n🎯 Performing feature selection...")
    optimal_k_chi2, optimal_features_chi2, _ = evaluate_feature_selection_chi2(X_train, y_train)
    optimal_k_fi, optimal_features_fi, _ = evaluate_feature_importance(X_train, y_train)
    
    print(f"   Chi-Square: {optimal_k_chi2} features selected")
    print(f"   Feature Importance: {optimal_k_fi} features selected")
    
    # Select features for training (using Chi-Square)
    X_train_selected = X_train[optimal_features_chi2]
    X_val_selected = X_val[optimal_features_chi2]
    X_test_selected = X_test[optimal_features_chi2]
    
    # Apply SMOTE + Tomek Links
    print("\n⚖️ Applying SMOTE + Tomek Links...")
    X_train_balanced, y_train_balanced = apply_smote_tomek(X_train_selected, y_train)
    
    # Model training and evaluation
    print("\n🤖 Training models...")
    
    # Model parameters
    best_params = {
        'n_estimators': 262,
        'criterion': 'entropy',
        'max_depth': 10,
        'min_samples_split': 5,
        'min_samples_leaf': 2,
        'bootstrap': True,
        'random_state': 42
    }
    
    # Train model with balanced data
    model, test_metrics = train_and_evaluate_model(
        X_train_balanced, y_train_balanced,
        X_val_selected, y_val,
        X_test_selected, y_test,
        model_name="RandomForest_Balanced",
        params=best_params
    )
    
    print(f"\n✅ Training completed!")
    print(f"🎯 Final Test Metrics:")
    print(f"   Accuracy: {test_metrics[0]:.4f}")
    print(f"   AUC: {test_metrics[1]:.4f}")
    print(f"   Recall: {test_metrics[2]:.4f}")
    print(f"\n📊 Check MLflow UI at http://localhost:5000 for detailed results")

if __name__ == "__main__":
    main()