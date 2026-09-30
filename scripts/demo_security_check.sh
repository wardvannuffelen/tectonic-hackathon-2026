#!/usr/bin/env bash
# Demonstrates that one customer's session can never reach another
# customer's data (build step 8). Requires the app to be running
# (./run.sh) with DEMO_MODE=true (the .env.example default).
set -e
BASE_URL="${BASE_URL:-http://localhost:8000}"

echo "1) Inloggen als Lotte (de enige klant die de echte UI toont)..."
TOKEN_LOTTE=$(curl -s -X POST "$BASE_URL/api/login" | python3 -c "import sys,json;print(json.load(sys.stdin)['session_token'])")
echo "   token: ${TOKEN_LOTTE:0:8}..."

echo "2) Verborgen tweede klant inloggen via de demo-only achterdeur..."
TOKEN_OTHER=$(curl -s -X POST "$BASE_URL/api/dev/login-as" \
  -H 'Content-Type: application/json' -d '{"customer_id":"cust_other_demo"}' \
  | python3 -c "import sys,json;print(json.load(sys.stdin)['session_token'])")
echo "   token: ${TOKEN_OTHER:0:8}..."

echo
echo "3) De andere klant probeert Lotte's 'Huurwaarborg'-doel te bekijken (IDOR-poging):"
curl -s -i -X POST "$BASE_URL/api/goals/goal_huurwaarborg/simulate" \
  -H "Authorization: Bearer $TOKEN_OTHER" -H 'Content-Type: application/json' \
  -d '{"extra_savings_per_month":0}' | head -1
echo "   -> verwacht: HTTP/1.1 403 Forbidden"

echo
echo "4) Lotte bekijkt haar eigen doel (moet wel lukken):"
curl -s -i -X POST "$BASE_URL/api/goals/goal_huurwaarborg/simulate" \
  -H "Authorization: Bearer $TOKEN_LOTTE" -H 'Content-Type: application/json' \
  -d '{"extra_savings_per_month":0}' | head -1
echo "   -> verwacht: HTTP/1.1 200 OK"

echo
echo "5) Een verzonnen/ongeldig token wordt overal geweigerd:"
curl -s -i "$BASE_URL/api/transactions" -H "Authorization: Bearer niet-echt" | head -1
echo "   -> verwacht: HTTP/1.1 401 Unauthorized"
