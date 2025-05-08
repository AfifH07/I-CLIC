import joblib
import pandas as pd

model = joblib.load("iclic-model.pkl")
data = pd.DataFrame([[25, 1, 90, 36.5, 98, 120, 80, 1, 0, 1, 1, 0, 1, 1, 0]], 
                    columns=['Age', 'Gender', 'Heart_Rate_bpm', 'Body_Temperature_C', 
                             'Oxygen_Saturation_%', 'Systolic', 'Diastolic', 
                             'Runny nose', 'Shortness of breath', 'Body ache', 
                             'Headache', 'Cough', 'Fever', 'Sore throat', 'Fatigue'])
pred = model.predict(data)
proba = model.predict_proba(data)
print(pred, proba)
