import pickle

d = pickle.load(open('models/win_probability_xgb_v2.pkl', 'rb'))
print(f"模型特徵數: {len(d['feature_columns'])}")
print(f"特徵列表: {d['feature_columns']}")
