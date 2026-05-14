from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import os
from datetime import datetime, timedelta

app = Flask(__name__)
CORS(app, origins="*")

CJ_EMAIL    = os.environ.get('CJ_EMAIL', '')
CJ_PASSWORD = os.environ.get('CJ_PASSWORD', '')
CJ_API_KEY  = os.environ.get('CJ_API_KEY', '')   # CJ5297560@api@xxxx format
BASE_URL    = "https://developers.cjdropshipping.com/api2.0/v1"

_token_cache = {'token': None, 'expiry': None}

def get_token():
    now = datetime.now()
    if _token_cache['token'] and _token_cache['expiry'] and now < _token_cache['expiry']:
        return _token_cache['token']
    try:
        r = requests.post(f"{BASE_URL}/authentication/getAccessToken",
                          json={"email": CJ_EMAIL, "password": CJ_PASSWORD},
                          timeout=10)
        d = r.json()
        if d.get('result') and d.get('data'):
            _token_cache['token']  = d['data']['accessToken']
            _token_cache['expiry'] = now + timedelta(hours=23)
            return _token_cache['token']
    except Exception as e:
        print("Token error:", e)
    # Fallback: use API key directly
    return CJ_API_KEY

def hdrs():
    return {"CJ-Access-Token": get_token(), "Content-Type": "application/json"}

# ── Health ──────────────────────────────────────────────
@app.route('/')
def home():
    return jsonify({"status": "CJ Store API ✅", "version": "1.0"})

@app.route('/health')
def health():
    return jsonify({"ok": True})

# ── Categories ──────────────────────────────────────────
@app.route('/api/categories')
def categories():
    try:
        r = requests.get(f"{BASE_URL}/product/listed/getPlatformCategoryTree",
                         headers=hdrs(), timeout=10)
        return jsonify(r.json())
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ── Products list ────────────────────────────────────────
@app.route('/api/products')
def products():
    try:
        params = {
            "pageNum":  request.args.get('page', 1),
            "pageSize": request.args.get('pageSize', 20),
        }
        kw  = request.args.get('keyword', '')
        cat = request.args.get('categoryId', '')
        if kw:  params['productNameEn'] = kw
        if cat: params['categoryId']    = cat

        r = requests.get(f"{BASE_URL}/product/query",
                         params=params, headers=hdrs(), timeout=15)
        return jsonify(r.json())
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ── Single product ───────────────────────────────────────
@app.route('/api/product/<pid>')
def product(pid):
    try:
        r = requests.get(f"{BASE_URL}/product/query",
                         params={"pid": pid}, headers=hdrs(), timeout=10)
        return jsonify(r.json())
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ── Variants ─────────────────────────────────────────────
@app.route('/api/variants')
def variants():
    try:
        r = requests.get(f"{BASE_URL}/product/variant/queryByVid",
                         params={"vid": request.args.get('vid', '')},
                         headers=hdrs(), timeout=10)
        return jsonify(r.json())
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ── Shipping calculation ─────────────────────────────────
@app.route('/api/shipping', methods=['POST'])
def shipping():
    try:
        r = requests.post(f"{BASE_URL}/logistic/freightCalculate",
                          json=request.json, headers=hdrs(), timeout=10)
        return jsonify(r.json())
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ── Place order ──────────────────────────────────────────
@app.route('/api/order', methods=['POST'])
def order():
    try:
        r = requests.post(f"{BASE_URL}/shopping/order/confirmOrder",
                          json=request.json, headers=hdrs(), timeout=15)
        return jsonify(r.json())
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ── Order list (admin) ───────────────────────────────────
@app.route('/api/orders')
def orders():
    try:
        params = {
            "pageNum":  request.args.get('page', 1),
            "pageSize": request.args.get('pageSize', 20),
        }
        r = requests.get(f"{BASE_URL}/shopping/order/list",
                         params=params, headers=hdrs(), timeout=10)
        return jsonify(r.json())
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
