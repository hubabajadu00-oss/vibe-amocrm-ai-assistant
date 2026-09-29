import json
import os
import re
from http.server import HTTPServer, SimpleHTTPRequestHandler
import urllib.parse

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
KB_PATH = os.path.join(BASE_DIR, "knowledge_base.json")

def load_kb():
    if os.path.exists(KB_PATH):
        with open(KB_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"services": [], "faq": []}

def analyze_and_respond(client_message: str):
    kb = load_kb()
    text = client_message.lower()

    # 1. Matching service in Knowledge Base
    matched = None
    if any(k in text for k in ["mvp", "вайб", "vibe", "быстр", "прототип", "разработ"]):
        matched = next((s for s in kb.get("services", []) if s["id"] == "vibe_coding_mvp"), None)
    elif any(k in text for k in ["баз", "знани", "rag", "документ", "регламент", "поиск"]):
        matched = next((s for s in kb.get("services", []) if s["id"] == "rag_knowledge_base"), None)
    elif any(k in text for k in ["crm", "amocrm", "амо", "менеджер", "отдел продаж", "подсказк"]):
        matched = next((s for s in kb.get("services", []) if s["id"] == "crm_ai_integration"), None)
    else:
        # Default to first relevant or generic service
        matched = kb.get("services", [None])[0]

    service_name = matched["name"] if matched else "Разработка AI-решений под ключ"
    price = matched["price"] if matched else "от 60 000 руб."
    timeline = matched["timeline"] if matched else "от 3 до 7 рабочих дней"
    upsells = matched.get("upsell_options", [
        "Интеграция с корпоративной CRM (+30 000 руб.)",
        "Техподдержка и мониторинг 24/7 (+25 000 руб./мес)"
    ])

    # 2. Block 1: Polite client reply
    client_reply = (
        f"Здравствуйте! Спасибо за обращение в О-комплекс. По вашей задаче отлично подходит наше решение «{service_name}». "
        f"Ориентировочные сроки внедрения составляют {timeline}, а стоимость базового этапа — {price}. "
        f"Мы можем продемонстрировать демо-стенд или собрать пилот на ваших данных за 2 дня. "
        f"Подскажите, пожалуйста, в какое время вам было бы удобно провести короткий 15-минутный звонок для обсуждения деталей?"
    )

    # 3. Block 2: Manager Upsell & Cross-sell tips
    manager_upsell = {
        "target_service": service_name,
        "primary_price": price,
        "upsell_recommendations": upsells,
        "sales_strategy": [
            "1. Предложите сразу закрыть вопрос интеграции с текущей CRM: связка баз знаний с AmoCRM повышает конверсию менеджеров на 30–40%.",
            "2. Укажите на выгоду годовой или квартальной поддержки — это гарантирует регулярное обновление промптов и моделей без найма штатного инженера.",
            "3. Предложите бесплатный 48-часовой пилот на 1 регламенте компании как триггер для быстрого заключения договора."
        ],
        "suggested_manager_question": "«Кстати, помимо базового сценария, планируете ли подключать сотрудников через Telegram-бота или делать автоматический скоринг лидов в AmoCRM?»"
    }

    ai_meta = {
        "engine": "Claude Code & Cursor AI-Assisted Architecture",
        "method": "RAG Pattern (Knowledge-Retrieval -> Split Generation)",
        "components": [
            "Structured Knowledge Base indexing",
            "Dual-Output Dispatcher (Client-Facing / Manager-Private)",
            "Upsell Strategy Decision Matrix"
        ]
    }

    return {
        "status": "success",
        "query": client_message,
        "client_reply": client_reply,
        "manager_upsell": manager_upsell,
        "ai_meta": ai_meta
    }

class AmoAssistantHandler(SimpleHTTPRequestHandler):
    def translate_path(self, path):
        # Serve index.html from BASE_DIR for root
        parsed = urllib.parse.urlparse(path).path
        if parsed in ["", "/"]:
            return os.path.join(BASE_DIR, "index.html")
        return super().translate_path(path)

    def do_POST(self):
        if self.path == "/api/generate":
            content_length = int(self.headers.get("Content-Length", 0))
            post_data = self.rfile.read(content_length)
            try:
                payload = json.loads(post_data.decode("utf-8"))
                message = payload.get("message", "")
                result = analyze_and_respond(message)
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps(result, ensure_ascii=False, indent=2).encode("utf-8"))
            except Exception as e:
                self.send_response(400)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()

def run(port=8085):
    server_address = ("", port)
    httpd = HTTPServer(server_address, AmoAssistantHandler)
    print(f"[*] AmoCRM AI Assistant Prototype running at http://localhost:{port}")
    httpd.serve_forever()

if __name__ == "__main__":
    run()
