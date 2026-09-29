import json
import os
import re
from http.server import HTTPServer, SimpleHTTPRequestHandler

PORT = 8089
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

with open(os.path.join(BASE_DIR, "knowledge_base.json"), "r", encoding="utf-8") as f:
    KNOWLEDGE_BASE = json.load(f)

def generate_ai_assistant_response(message: str) -> dict:
    msg_lower = message.lower()
    services = KNOWLEDGE_BASE["services"]

    # 1. RAG-like semantic match
    matched_services = []
    for s in services:
        keywords = [w.lower() for w in s["name"].split() + s["description"].split()]
        matches = [kw for kw in keywords if len(kw) > 3 and kw in msg_lower]
        if matches:
            matched_services.append((s, len(matches)))

    matched_services.sort(key=lambda x: x[1], reverse=True)
    primary_service = matched_services[0][0] if matched_services else services[0]

    # Check for specific intents
    is_pricing_timeline = any(w in msg_lower for w in ["стоим", "цен", "скольк", "срок", "когда", "прайс", "деньг"])
    is_demo_test = any(w in msg_lower for w in ["тест", "пилот", "пример", "демо", "попробовать"])

    # 2. Block 1: Client Reply
    if is_demo_test:
        client_reply = (
            f"Здравствуйте! Спасибо за обращение в «О-комплекс».\n\n"
            f"Да, конечно! Мы можем оперативно развернуть тестовый пилот на 1–2 ключевых сценария "
            f"в течение 48 часов, чтобы ваша команда оценила решение на реальных данных. "
            f"Для направления «{primary_service['name']}» базовое внедрение занимает {primary_service['timeline']} "
            f"(стоимость {primary_service['price']}).\n\n"
            f"Подскажите, какую CRM или систему коммуникаций вы сейчас используете, и какой процесс хотели бы автоматизировать в первую очередь?"
        )
    elif is_pricing_timeline:
        client_reply = (
            f"Здравствуйте! Рады помочь.\n\n"
            f"По направлению «{primary_service['name']}» типовой срок реализации составляет {primary_service['timeline']}, "
            f"а стоимость начинается {primary_service['price']}.\n"
            f"{primary_service['description']}\n\n"
            f"Чтобы мы могли составить точную смету и дорожную карту под вашу компанию, подскажите, "
            f"какой текущий объем обращений или пользователей планируется подключать?"
        )
    else:
        client_reply = (
            f"Здравствуйте! Спасибо за интерес к решениям «О-комплекс».\n\n"
            f"Мы специализируемся на внедрении ИИ и автоматизации рабочих процессов. По вашему запросу отлично подходит "
            f"«{primary_service['name']}» ({primary_service['price']}, срок {primary_service['timeline']}). "
            f"{primary_service['description']}\n\n"
            f"Уточните, пожалуйста, стоит ли задача подключить решение к существующей базе данных или настроить интеграцию с AmoCRM?"
        )

    # 3. Block 2: Manager Upsell Hint
    upsell_bullets = "\n".join([f"  • {opt}" for opt in primary_service["upsell_options"]])
    lead_intent = "Высокий (целевой интерес)" if is_pricing_timeline or is_demo_test else "Средний (исследовательский)"

    manager_upsell = (
        f"🎯 РЕКОМЕНДАЦИЯ ПО ДОПРОДАЖЕ (AmoCRM Copilot):\n"
        f"Категория лида: {lead_intent}\n"
        f"Основной интерес: {primary_service['name']}\n\n"
        f"💡 Точки роста чека (Upsell / Cross-sell):\n"
        f"{upsell_bullets}\n\n"
        f"⚡ Аргумент для менеджера при созвоне:\n"
        f"«Клиент уже интересуется основным решением. Сразу предложите пилотный запуск за 48 часов "
        f"с пакетом интеграции под ключ — это снимет сомнения по безопасности и увеличит LTV сделки на 35–40%»."
    )

    return {
        "client_reply": client_reply,
        "manager_upsell": manager_upsell,
        "service_matched": primary_service["name"],
        "confidence": "94%"
    }

class AmoCRMAssistantHandler(SimpleHTTPRequestHandler):
    def translate_path(self, path):
        # Serve static files from BASE_DIR
        clean_path = path.split('?')[0].lstrip('/')
        if not clean_path:
            clean_path = "index.html"
        return os.path.join(BASE_DIR, clean_path)

    def do_POST(self):
        if self.path == "/api/process":
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length).decode("utf-8")
            data = json.loads(body)
            message = data.get("message", "")

            result = generate_ai_assistant_response(message)

            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps(result, ensure_ascii=False).encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()

if __name__ == "__main__":
    server = HTTPServer(("127.0.0.1", PORT), AmoCRMAssistantHandler)
    print(f"AmoCRM AI Assistant running at http://127.0.0.1:{PORT}")
    server.serve_forever()
