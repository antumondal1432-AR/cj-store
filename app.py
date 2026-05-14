from flask import Flask, request, jsonify
from flask_cors import CORS
import requests, os
from datetime import datetime, timedelta

app = Flask(__name__)
CORS(app, origins="*")

CJ_EMAIL    = os.environ.get('CJ_EMAIL', '')
CJ_PASSWORD = os.environ.get('CJ_PASSWORD', '')
CJ_API_KEY  = os.environ.get('CJ_API_KEY', '')
BASE_URL    = "https://developers.cjdropshipping.com/api2.0/v1"
_cache      = {'token': None, 'expiry': None}

def get_token():
    now = datetime.now()
    if _cache['token'] and _cache['expiry'] and now < _cache['expiry']:
        return _cache['token']
    try:
        r = requests.post(f"{BASE_URL}/authentication/getAccessToken",
            json={"email": CJ_EMAIL, "password": CJ_PASSWORD}, timeout=15)
        d = r.json()
        print("Auth:", d.get('result'), d.get('message',''))
        if d.get('result') and d.get('data'):
            _cache['token']  = d['data']['accessToken']
            _cache['expiry'] = now + timedelta(hours=23)
            return _cache['token']
    except Exception as e:
        print("Auth error:", e)
    return CJ_API_KEY

def H():
    return {"CJ-Access-Token": get_token(), "Content-Type": "application/json"}

@app.route('/')
def home():
    return jsonify({"status": "CJ Store API OK", "version": "2.0"})

@app.route('/api/test-auth')
def test_auth():
    t = get_token()
    return jsonify({"token_exists": bool(t), "token": t[:25]+"..." if t else "", "email": CJ_EMAIL, "pass_set": bool(CJ_PASSWORD)})

@app.route('/api/categories')
def categories():
    try:
        r = requests.get(f"{BASE_URL}/product/listed/getPlatformCategoryTree", headers=H(), timeout=15)
        return jsonify(r.json())
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/products')
def products():
    try:
        p = {"pageNum": request.args.get('page',1), "pageSize": request.args.get('pageSize',20)}
        if request.args.get('keyword'): p['productNameEn'] = request.args.get('keyword')
        if request.args.get('categoryId'): p['categoryId'] = request.args.get('categoryId')
        r = requests.get(f"{BASE_URL}/product/query", params=p, headers=H(), timeout=20)
        return jsonify(r.json())
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/orders')
def orders():
    try:
        p = {"pageNum": request.args.get('page',1), "pageSize": 20}
        r = requests.get(f"{BASE_URL}/shopping/order/list", params=p, headers=H(), timeout=15)
        return jsonify(r.json())
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/order', methods=['POST'])
def order():
    try:
        r = requests.post(f"{BASE_URL}/shopping/order/confirmOrder", json=request.json, headers=H(), timeout=20)
        return jsonify(r.json())
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT',10000)), debug=False)
