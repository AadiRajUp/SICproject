import pandas as pd
import numpy as np
import joblib

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import r2_score, mean_squared_error


print("STEP 1: Loading dataset...")
df = pd.read_csv("dataset.csv")
df.dropna(inplace=True)
print(f"Dataset shape: {df.shape}")


print("\nSTEP 2: Preprocessing...")

if 'student_id' in df.columns:
    df.drop(columns=['student_id'], inplace=True)

label_encoders = {}

categorical_columns = df.select_dtypes(include=['object', 'string']).columns

for col in categorical_columns:
        le = LabelEncoder()
        df[col] = le.fit_transform(df[col].astype(str))
        label_encoders[col] = le
        print(f"Encoded column: {col}")

joblib.dump(label_encoders, "label_encoders.pkl")


print("\nSTEP 3: Feature selection...")

corr = df.corr(numeric_only=True)["productivity_score"].drop("productivity_score").abs().sort_values(ascending=False)

top_features = corr.head(4).index.tolist() 
print("Top features:", top_features)

joblib.dump(top_features, "top_features.pkl")


print("\nSTEP 4: Train-test split...")

X = df[top_features]
y = df["productivity_score"]

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)


print("\nSTEP 5: Training model...")

model = RandomForestRegressor(
    n_estimators=200,
    random_state=42,
    max_depth=None
)

model.fit(X_train, y_train)

joblib.dump(model, "model.pkl")


print("\nSTEP 6: Evaluation...")

y_pred = model.predict(X_test)

r2 = r2_score(y_test, y_pred)
rmse = np.sqrt(mean_squared_error(y_test, y_pred))

print(f"R2 Score: {r2:.4f}")
print(f"RMSE    : {rmse:.4f}")


print("\n✅ Training complete!")
print("Saved files:")
print("- model.pkl")
print("- label_encoders.pkl")
print("- top_features.pkl")