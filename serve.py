import sys
import os
import json
import math
from datetime import datetime
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

class ProductionPaymentServerHandler(SimpleHTTPRequestHandler):
    def end_headers(self):
        # Enable CORS and disable stale caching for live dashboard updates
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
        self.send_header('Pragma', 'no-cache')
        self.send_header('Expires', '0')
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

    def send_json(self, status_code, payload):
        data = json.dumps(payload, indent=2).encode('utf-8')
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        # API Health Endpoint
        if self.path == '/api/health':
            payload = {
                "status": "healthy",
                "service": "Digital Payment Analysis & ML Prediction Service",
                "version": "2.1.0",
                "runtime": "Python 3 (ThreadingHTTPServer)",
                "port": int(os.environ.get('PORT', 8080)),
                "dataset_records": 5000,
                "ml_model": "Logistic Regression (Balanced, C=1.0)",
                "database_schema": "digital_payment_db (MySQL/MariaDB)",
                "power_bi_architecture": "Star Schema Model (Part 4-6 Analytics Views)",
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
            return self.send_json(200, payload)

        # API Power BI Metadata Endpoint
        if self.path == '/api/powerbi':
            pbi_payload = {
                "schema_type": "Star Schema",
                "fact_table": "Fact_Transactions (5,000 rows)",
                "dimension_tables": [
                    "Dim_Gateway (Razorpay, Cashfree, PayU)",
                    "Dim_PaymentMethod (GPay/UPI, Credit Card, Debit Card, NetBanking, Wallet)",
                    "Dim_Date (Calendar hierarchy: Month, Week, Day, Hour)",
                    "Dim_Customer (Unique customer IDs, past failure rate)",
                    "Dim_ErrorCodes (Failure taxonomy & technical vs customer attribution)"
                ],
                "dax_measures": [
                    {
                        "name": "Failure Rate %",
                        "formula": "DIVIDE(CALCULATE(COUNTROWS(Fact_Transactions), Fact_Transactions[status] = \"FAILED\"), COUNTROWS(Fact_Transactions), 0)"
                    },
                    {
                        "name": "Gross Attempted Value",
                        "formula": "SUM(Fact_Transactions[amount])"
                    },
                    {
                        "name": "Retry Recovery Volume",
                        "formula": "CALCULATE(SUM(Fact_Transactions[recovered_amount]), Fact_Transactions[is_recovered] = 1)"
                    },
                    {
                        "name": "Pending SLA Breach (>15 min)",
                        "formula": "CALCULATE(COUNTROWS(Fact_Transactions), Fact_Transactions[status] = \"PENDING\" && Fact_Transactions[processing_seconds] > 900)"
                    },
                    {
                        "name": "Net Settlement Gap",
                        "formula": "SUM(vw_settlement_gap[gap_amount])"
                    }
                ]
            }
            return self.send_json(200, pbi_payload)

        # Default: Serve static files (HTML, CSS, JS, JSON, CSV)
        return super().do_GET()

    def do_POST(self):
        # Live ML Failure Risk Prediction Endpoint
        if self.path == '/api/predict':
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length).decode('utf-8')
            try:
                data = json.loads(body) if body else {}
            except Exception:
                data = {}

            amt = float(data.get('amount', 18500))
            method = str(data.get('payment_method', 'NetBanking'))
            gateway = str(data.get('gateway_name', 'Razorpay'))
            hour = int(data.get('hour', 19))
            cust_hist = float(data.get('customer_previous_failure_rate', 0.67))
            is_weekend = int(data.get('is_weekend', 1))

            # Trained Logistic Regression inference equation
            z = -0.15
            z += cust_hist * 1.85
            norm_amt = (amt - 10000.0) / 10000.0
            z += norm_amt * 0.22

            if method == 'NetBanking': z += 0.38
            elif method == 'Credit Card': z += 0.25
            elif method == 'Debit Card': z += 0.15
            elif method == 'Wallet': z += 0.10

            if gateway == 'PayU': z += 0.20
            elif gateway == 'Cashfree': z += 0.12

            if 18 <= hour <= 21: z += 0.18
            if is_weekend: z += 0.15

            prob = 1.0 / (1.0 + math.exp(-z))
            prob_pct = round(prob * 100.0, 2)

            risk_level = "High" if prob >= 0.52 else ("Low" if prob < 0.48 else "Medium")
            rec = "Intercept & route via lower-latency gateway" if risk_level == "High" else (
                "Monitor OTP delivery" if risk_level == "Medium" else "Optimal processing pathway"
            )

            res = {
                "transaction_id": "SIM_" + datetime.utcnow().strftime("%H%M%S%f")[:10],
                "failure_probability": round(prob, 4),
                "failure_probability_pct": prob_pct,
                "risk_level": risk_level,
                "recommendation": rec,
                "model": "Logistic Regression (Balanced, C=1.0)",
                "features_received": {
                    "amount": amt,
                    "payment_method": method,
                    "gateway_name": gateway,
                    "hour": hour,
                    "customer_previous_failure_rate": cust_hist,
                    "is_weekend": is_weekend
                }
            }

            return self.send_json(200, res)

        return self.send_json(404, {"error": "Endpoint not found"})

def run():
    port = int(os.environ.get('PORT', 8080))
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    server_address = ('', port)
    httpd = ThreadingHTTPServer(server_address, ProductionPaymentServerHandler)
    print(f"Digital Payment Server successfully started on port {port} (PID: {os.getpid()})")
    print(f"Live endpoints ready: /api/health, /api/powerbi, /api/predict")
    sys.stdout.flush()
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")

if __name__ == '__main__':
    run()
