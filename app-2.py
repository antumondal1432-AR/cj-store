from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import os
from datetime import datetime, timedelta

app = Flask(__name__)
CORS(app, origins="*")

CJ_EMAIL    = os.environ.get('CJ_EMAIL', '')
CJ_PASSWORD = os.environ.get('CJ_PASSWORD', '')
CJ_API_KEY  = os.environ.get('CJ_API_KEY', '')
BASE_URL    = "https://developers.cjdropshipping.com/api2.0/v1"

_token_cache = {'token': None, 'expiry': None}

def get_token():
    now = datetime.now()
    if _token_cache['token'] and _token_cache['expiry'] and now < _token_cache['expiry']:
        return _token_cache['token']
    if CJ_EMAIL and CJ_PASSWORD:
        try:
            r = requests.post(
                f"{BASE_URL}/authentication/getAccessToken",
                json={"email": CJ_EMAIL, "password": CJ_PASSWORD},
                timeout=15
            )
            d = r.json()
            print("CJ Auth:", d.get('result'), d.get('message',''))
            if d.get('result') and d.get('data'):
                token = d['data']['accessToken']
                _token_cache['token']  = token
                _token_cache['expiry'] = now + timedelta(hours=23)
                return token
        except Exception as e:
            print("Auth error:", e)
    return CJ_API_KEY

def hdrs():
    return {"CJ-Access-Token": get_token(), "Content-Type": "application/json"}

@app.route('/')
def home():
    return jsonify({"status": "CJ Store API OK", "version": "2.0"})

@app.route('/api/test-auth')
def test_auth():
    token = get_token()
    return jsonify({
        "token_exists": bool(token),
        "token_preview": token[:30] + "..." if token and len(token) > 30 else token,
        "email": CJ_EMAIL,
        "password_set": bool(CJ_PASSWORD),
        "api_key_set": bool(CJ_API_KEY),
    })

@app.route('/api/categories')
def categories():
    try:
        r = requests.get(f"{BASE_URL}/product/listed/getPlatformCategoryTree", headers=hdrs(), timeout=15)
        return jsonify(r.json())
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/products')
def products():
    try:
        params = {"pageNum": request.args.get('page', 1), "pageSize": request.args.get('pageSize', 20)}
        kw  = request.args.get('keyword', '')
        cat = request.args.get('categoryId', '')
        if kw:  params['productNameEn'] = kw
        if cat: params['categoryId']    = cat
        r = requests.get(f"{BASE_URL}/product/query", params=params, headers=hdrs(), timeout=20)
        return jsonify(r.json())
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/product/<pid>')
def product(pid):
    try:
        r = requests.get(f"{BASE_URL}/product/query", params={"pid": pid}, headers=hdrs(), timeout=15)
        return jsonify(r.json())
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/shipping', methods=['POST'])
def shipping():
    try:
        r = requests.post(f"{BASE_URL}/logistic/freightCalculate", json=request.json, headers=hdrs(), timeout=15)
        return jsonify(r.json())
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/order', methods=['POST'])
def order():
    try:
        r = requests.post(f"{BASE_URL}/shopping/order/confirmOrder", json=request.json, headers=hdrs(), timeout=20)
        return jsonify(r.json())
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/orders')
def orders():
    try:
        params = {"pageNum": request.args.get('page', 1), "pageSize": request.args.get('pageSize', 20)}
        r = requests.get(f"{BASE_URL}/shopping/order/list", params=params, headers=hdrs(), timeout=15)
        return jsonify(r.json())
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=False)
