from flask import Flask, request, jsonify
from transformers import pipeline

app = Flask(__name__)

# 🧠 GLOBAL LOAD: Server start hone par sirf 1 baar load hoga.
# Isse har request par model dobara load nahi hoga aur RAM bachegi!
print("🔄 Loading Model into RAM... (Pehli baar mein 1-2 min lagenge)")
model = pipeline("sentiment-analysis", model="distilbert-base-uncased-finetuned-sst-2-english")
print("✅ Model Loaded Successfully! Ready for predictions.")

@app.route('/predict', methods=['POST'])
def predict():
    try:
        # Frontend se JSON data lo
        data = request.get_json()
        text = data.get('text', '')
        
        if not text:
            return jsonify({"error": "No text provided"}), 400
        
        # Model se prediction lo
        result = model(text)[0]
        
        # Result wapas frontend ko bhejo
        return jsonify({
            "label": result['label'], 
            "score": round(result['score'], 4)
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    # Local testing ke liye ye best hai. Production mein hum gunicorn use karenge.
    app.run(host='0.0.0.0', port=5000, debug=False)