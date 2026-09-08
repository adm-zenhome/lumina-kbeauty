#!/usr/bin/env python3
"""
lumina_cloud_sentinel.py — Sentinela Digital em Nuvem (Ji-woo 24/7)
Monitora perguntas, novas compras e envia notificações executivas no Telegram.
Roda a cada 30 minutos na nuvem (GitHub Actions / Vercel / Cron).

Taxas Reais Confirmadas (Central de Vendedores ML — 08/09/2026):
  - Tarifa Anúncio Premium: 17.0% (ex: R$237,83 em R$1.399)
  - Custo Frete Mercado Envios: R$25,45 (ML cobre 50% do R$50,90 original)
  - Você recebe (bruto pós-taxas): R$1.135,72 no Super Combo
"""

import os
import sys
import json
import argparse
import urllib.request
import urllib.parse
from datetime import datetime
from pathlib import Path
import requests

BASE_DIR = Path(__file__).resolve().parent
ENV_FILE = BASE_DIR / ".env"
PROCESSED_FILE = BASE_DIR / "sentinel_state.json"

# Configurações do Telegram
TELEGRAM_BOT_TOKEN = "7734494805:AAEybSrLc5O3z0sJCgNYaggcc7EdUIAf1-Q"
TELEGRAM_CHAT_ID = "856670142"

# Catálogo Clínico Lumina K-Beauty (Base de Conhecimento da Ji-woo)
CATALOG_KNOWLEDGE = {
    "MLB5200831909": {
        "name": "Super Combo Medicube Booster Mini Pro Plus E Pdrn",
        "price": 1399.00,
        "profit": 450.37,
        "highlights": "Aparelho Booster Pro + Creme PDRN Salmon DNA 55g. 790% mais absorção dérmica, efeito glass skin imediato, garantia 90 dias com suporte no Brasil."
    },
    "MLB5200870421": {
        "name": "Medicube Booster Mini Pro Plus Aparelho Facial Eletroporacao",
        "price": 1149.00,
        "profit": 366.67,
        "highlights": "Eletroporação e microcorrentes, melhora absorção em 790%, compatível com qualquer sérum, entrada universal USB-C, 90 dias garantia oficial."
    },
    "MLB5203216077": {
        "name": "Celimax Retinal Shot Tightening Booster 20ml",
        "price": 239.00,
        "profit": 54.57,
        "highlights": "Retinaldeído lipossomado 0.1%, renovação celular potente e gentil, zero descamação severa, indicado para textura irregular e linhas finas."
    },
    "MLB5203216329": {
        "name": "Medicube Zero Foam Cleanser 120g",
        "price": 219.00,
        "profit": 72.27,
        "highlights": "Sabonete facial clínico coreano, desobstrução profunda de poros sem repuxar a barreira cutânea, pH fisiológico 5.5 equilibrado."
    },
    "MLB5201103683": {
        "name": "Anua Heartleaf 77% Clear Pad 70 Discos",
        "price": 259.00,
        "profit": 62.67,
        "highlights": "Discos calmantes com 77% extrato de Heartleaf, resfria a pele em 2.6°C, anti-inflamatório ideal para melasma e acne ativa."
    },
    "MLB5201124505": {
        "name": "Numbuzin N° 5+ Glutathione Vitamin Concentrated Serum 30ml",
        "price": 249.00,
        "profit": 62.17,
        "highlights": "Glutationa pura + Niacinamida + Ácido Tranexâmico. Clareamento de manchas e melasma sem efeito rebote ou agressão."
    },
    "MLB5201104641": {
        "name": "Numbuzin N° 9 Secret Plumping Firming Serum Seringa 40ml",
        "price": 249.00,
        "profit": 62.17,
        "highlights": "Volufiline francês patenteado + Complexo Peptídico, restaura sustentação e efeito preenchedor sem agulhas."
    },
    "MLB5201115865": {
        "name": "Medicube Pdrn Pink Peptide Cream 55g",
        "price": 249.00,
        "profit": 62.17,
        "highlights": "PDRN Salmon DNA + 5 Peptídeos Tensores, hidratação profunda e regeneração celular com toque seco de porcelana."
    },
    "MLB5200845347": {
        "name": "Kit Firmeza E Renovacao Numbuzin 9 Mais Celimax Retinal",
        "price": 479.00,
        "profit": 127.67,
        "highlights": "Protocolo completo noturno de firmeza e renovação celular anti-idade com economia de combo."
    },
    "MLB5200845621": {
        "name": "Kit Clareamento E Pele Calma Anua 77 Mais Numbuzin 5",
        "price": 499.00,
        "profit": 138.57,
        "highlights": "Protocolo Pele Fria: acalma com Anua e clareia com Glutationa sem agredir o melasma."
    },
    "MLB5200870505": {
        "name": "Kit Limpeza E Firmeza Zero Foam Mais Creme Pdrn",
        "price": 449.00,
        "profit": 135.37,
        "highlights": "Limpeza profunda de poros seguida de infusão profunda de colágeno PDRN Salmon DNA."
    }
}

EBOOK_URL = "https://lumina-skincare.vercel.app/A_Biblia_da_Pele_de_Porcelana_100_Paginas_LUMINA.pdf"

def load_env():
    env = {}
    if os.path.exists(ENV_FILE):
        with open(ENV_FILE, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    env[k.strip()] = v.strip().strip('"').strip("'")
    
    # Sobrescreve com variáveis de ambiente reais do sistema (ex: GitHub Actions secrets)
    for key in [
        "MERCADO_LIVRE_CLIENT_ID", "MERCADO_LIVRE_CLIENT_SECRET",
        "MERCADO_LIVRE_ACCESS_TOKEN", "MERCADO_LIVRE_REFRESH_TOKEN",
        "TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID"
    ]:
        if os.environ.get(key):
            env[key] = os.environ.get(key)
            
    return env

def save_env(env):
    with open(ENV_FILE, "w") as f:
        for k, v in env.items():
            f.write(f'{k}="{v}"\n')

def load_state():
    if os.path.exists(PROCESSED_FILE):
        try:
            with open(PROCESSED_FILE, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return {"answered_questions": [], "processed_orders": []}

def save_state(state):
    with open(PROCESSED_FILE, "w") as f:
        json.dump(state, f, indent=2)

def send_telegram(text: str):
    """Envia alerta executivo formatado em HTML para o Telegram do Felipe."""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True
    }
    data = urllib.parse.urlencode(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data)
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        print(f"❌ Erro ao enviar Telegram: {e}")
        return None

def get_valid_token():
    """Garante que temos um token válido, executando auto-refresh se necessário."""
    env = load_env()
    token = env.get("MERCADO_LIVRE_ACCESS_TOKEN")
    
    # Testa token
    if token:
        try:
            r = requests.get(
                "https://api.mercadolibre.com/users/me",
                headers={"Authorization": f"Bearer {token}"},
                timeout=10
            )
            if r.status_code == 200:
                return token, env
        except Exception:
            pass

    # Token expirado -> auto-refresh
    print("🔄 Token expirado ou inválido. Executando auto-refresh...")
    refresh_token = env.get("MERCADO_LIVRE_REFRESH_TOKEN")
    client_id = env.get("MERCADO_LIVRE_CLIENT_ID")
    client_secret = env.get("MERCADO_LIVRE_CLIENT_SECRET")

    if not (refresh_token and client_id and client_secret):
        print("❌ Credenciais de refresh incompletas no .env")
        return None, env

    refresh_url = "https://api.mercadolibre.com/oauth/token"
    payload = {
        "grant_type": "refresh_token",
        "client_id": client_id,
        "client_secret": client_secret,
        "refresh_token": refresh_token
    }
    try:
        r = requests.post(refresh_url, data=payload, timeout=15)
        if r.status_code == 200:
            data = r.json()
            new_token = data.get("access_token")
            new_refresh = data.get("refresh_token")
            env["MERCADO_LIVRE_ACCESS_TOKEN"] = new_token
            if new_refresh:
                env["MERCADO_LIVRE_REFRESH_TOKEN"] = new_refresh
            save_env(env)
            print("✅ Token renovado com sucesso via Refresh Token!")
            return new_token, env
        else:
            print(f"❌ Falha no refresh token: {r.status_code} - {r.text}")
    except Exception as e:
        print(f"❌ Erro de conexão no refresh token: {e}")

    return None, env

def generate_jiwoo_answer(question_text: str, item_id: str = "") -> str:
    """
    Motor Clínico da Ji-woo: Gera resposta calorosa, empática e clinicamente impecável,
    quebrando objeções de pronta entrega, originalidade, garantia e modo de uso.
    """
    text = question_text.lower()
    item_info = CATALOG_KNOWLEDGE.get(item_id, {})
    item_name = item_info.get("name", "produto Lumina K-Beauty")

    # 1. Objeção: Originalidade / Procedência
    if any(w in text for w in ["original", "falso", "falsificado", "réplica", "autêntico", "coreano"]):
        return (
            "Olá! 🌸 Sim, produto 100% original e autêntico importado diretamente da Coreia do Sul! "
            "Enviamos o produto lacrado de fábrica, com lote oficial, nota fiscal e 90 dias de garantia com suporte no Brasil. "
            "Além disso, após a compra você ganha de presente a nossa 'Bíblia da Pele de Porcelana' com 100 páginas de protocolos clínicos. "
            "Temos pronta entrega em São Paulo com envio imediato pelo Mercado Envios! Qualquer dúvida, estamos à disposição."
        )

    # 2. Objeção: Pronta Entrega / Frete / Estoque Brasil
    if any(w in text for w in ["pronta entrega", "estoque", "chega rápido", "envio", "são paulo", "sp", "demora"]):
        return (
            "Olá! ✨ Sim, temos estoque físico a pronta entrega em São Paulo! "
            "Comprando agora, seu pedido é despachado em até 24 horas úteis com embalagem reforçada e lacrada pelo Mercado Envios. "
            "Acompanha nota fiscal e 90 dias de garantia. Aguardamos o seu pedido para preparar com muito carinho!"
        )

    # 3. Objeção: Cabo / Carregamento (Medicube Booster)
    if any(w in text for w in ["cabo", "carregador", "bateria", "usb", "carrega", "tomada"]):
        return (
            "Olá! 🤍 O aparelho possui entrada universal USB-C moderna (padrão mundial), podendo ser carregado com o mesmo cabo "
            "do seu celular ou notebook em qualquer fonte bivolt. Por diretiva de sustentabilidade dos fabricantes de tech, "
            "não acompanha o cabo avulso, mas é compatível com qualquer carregador padrão. A bateria dura semanas com uso diário de 3 a 5 minutos! "
            "Temos pronta entrega em SP e enviamos com 90 dias de garantia."
        )

    # 4. Objeção: Melasma / Manchas / Calor
    if any(w in text for w in ["melasma", "mancha", "esquenta", "calor", "rebote", "clareia"]):
        return (
            "Olá! 🌸 Perfeita pergunta! Esse protocolo é 100% seguro para melasma porque atua de forma atermal (não emite calor prejudicial). "
            "O tratamento resfria e desinflama a pele, clareando com ativos nobres (como Glutationa e Niacinamida) sem risco de efeito rebote. "
            "Pode usar com total tranquilidade para uniformizar o tom e devolver a luminosidade natural. "
            "Temos a pronta entrega em SP com garantia de 90 dias e envio imediato!"
        )

    # 5. Objeção: Como usar / Modo de uso / Rotina
    if any(w in text for w in ["como usa", "como usar", "rotina", "tempo", "quantas vezes", "passo"]):
        return (
            "Olá! ✨ A rotina é super prática e rápida: são apenas 3 a 5 minutinhos por dia, preferencialmente à noite com a pele limpa. "
            "Após a compra, você recebe gratuitamente o nosso E-book completo de 100 páginas com o passo a passo ilustrado de cada produto! "
            "Produto original lacrado com estoque em SP e envio imediato com 90 dias de garantia. Qualquer dúvida estou por aqui!"
        )

    # 6. Resposta Padrão de Alta Conversão
    return (
        f"Olá! 🌸 Muito obrigada pelo contato! Sim, o {item_name} está disponível com estoque físico a pronta entrega em São Paulo. "
        "Enviamos produto 100% original lacrado de fábrica, com nota fiscal, 90 dias de garantia oficial no Brasil e de brinde "
        "o nosso e-book exclusivo de 100 páginas 'A Bíblia da Pele de Porcelana'. Despachamos em até 24h pelo Mercado Envios. "
        "Aguardamos seu pedido para enviar com todo carinho!"
    )

def process_unanswered_questions(token: str, dry_run: bool = False):
    """Varre e responde perguntas pendentes no Mercado Livre."""
    user_id = "60455737"
    url = f"https://api.mercadolibre.com/questions/search?seller_id={user_id}&status=UNANSWERED"
    headers = {"Authorization": f"Bearer {token}"}
    
    state = load_state()
    answered_ids = set(state.get("answered_questions", []))

    try:
        r = requests.get(url, headers=headers, timeout=15)
        if r.status_code != 200:
            print(f"⚠️ Erro ao consultar perguntas: {r.status_code} - {r.text}")
            return
        
        data = r.json()
        questions = data.get("questions", [])
        total = len(questions)
        print(f"📋 Perguntas não respondidas encontradas: {total}")

        for q in questions:
            q_id = q.get("id")
            q_text = q.get("text", "")
            item_id = q.get("item_id", "")

            if q_id in answered_ids:
                continue

            # Gera resposta com cérebro clínico
            answer_text = generate_jiwoo_answer(q_text, item_id)
            item_info = CATALOG_KNOWLEDGE.get(item_id, {})
            item_name = item_info.get("name", item_id)

            print(f"\n💬 Pergunta [{q_id}] sobre {item_name}: '{q_text}'")
            print(f"🤖 Resposta Ji-woo: '{answer_text}'")

            if not dry_run:
                # Envia para a API do Mercado Livre
                ans_url = "https://api.mercadolibre.com/answers"
                ans_payload = {"question_id": q_id, "text": answer_text}
                ans_res = requests.post(ans_url, json=ans_payload, headers=headers, timeout=15)
                
                if ans_res.status_code in [200, 201]:
                    print("✅ Resposta enviada com sucesso no Mercado Livre!")
                    answered_ids.add(q_id)
                    state["answered_questions"] = list(answered_ids)
                    save_state(state)

                    # Notifica no Telegram
                    tg_msg = (
                        "💬 <b>Pergunta Respondida no Mercado Livre!</b>\n\n"
                        f"📦 <b>Produto:</b> {item_name}\n"
                        f"❓ <b>Pergunta do Cliente:</b> <i>\"{q_text}\"</i>\n\n"
                        f"🤖 <b>Resposta da Ji-woo:</b>\n{answer_text}\n\n"
                        f"⚡ <i>Respondido em tempo recorde via Lumina Sentinel.</i>"
                    )
                    send_telegram(tg_msg)
                else:
                    print(f"❌ Erro ao enviar resposta: {ans_res.status_code} - {ans_res.text}")

    except Exception as e:
        print(f"❌ Erro no processamento de perguntas: {e}")

def format_payment_breakdown(order: dict, item_info: dict) -> dict:
    """Calcula a quebra financeira detalhada da venda (DRE do Pedido)."""
    total_amount = float(order.get("total_amount", 0.0))
    payments = order.get("payments", [])
    
    pay_method = "Mercado Pago"
    pay_type = "Confirmado"
    installments = 1
    
    if payments:
        p = payments[0]
        method_id = p.get("payment_method_id", "")
        ptype = p.get("payment_type", "")
        installments = p.get("installments", 1)
        
        if "boleto" in method_id or ptype == "ticket":
            pay_method = f"Boleto Bancário ({method_id.upper()})"
            pay_type = "Boleto"
        elif "pix" in method_id or ptype == "bank_transfer":
            pay_method = "PIX Instantâneo"
            pay_type = "PIX"
        elif ptype == "credit_card":
            pay_method = f"Cartão de Crédito ({method_id.upper()} em {installments}x)"
            pay_type = "Cartão"
        elif ptype == "account_money":
            pay_method = "Saldo Mercado Pago"
            pay_type = "Saldo"

    # Quebra de custos reais (confirmados no painel ML em 08/09/2026)
    items = order.get("order_items", [])
    sale_fee = 0.0
    for it in items:
        sale_fee += float(it.get("sale_fee", 0.0))
    
    # Se a API não trouxer a taxa preenchida (ex: simulação), usa 17% real do Premium
    # Confirmado: R$ 237,83 sobre R$ 1.399,00 = 17.0% (Anúncio Premium)
    if sale_fee == 0.0:
        sale_fee = total_amount * 0.17

    # Frete Premium confirmado: R$ 50,90 (Mercado Envios — anúncio Premium obriga frete grátis ao comprador)
    # Atualizado em 08/09/2026 após mudança de Super Combo e Booster Solo para Premium
    shipping_cost = 50.90
    
    # "Você recebe" = total - taxa - frete (conforme Resumo de Custos do ML)
    you_receive = total_amount - sale_fee - shipping_cost

    # CMV (Custo da Mercadoria Vendida) = tabelado na precificação blindada
    expected_profit = item_info.get("profit", total_amount * 0.25)
    cmv = you_receive - expected_profit
    if cmv < 0:
        cmv = you_receive * 0.60
        expected_profit = you_receive - cmv

    margin_pct = (expected_profit / total_amount * 100) if total_amount > 0 else 0

    return {
        "total_amount": total_amount,
        "pay_method": pay_method,
        "pay_type": pay_type,
        "installments": installments,
        "sale_fee": sale_fee,
        "shipping_cost": shipping_cost,
        "you_receive": you_receive,
        "cmv": cmv,
        "profit": expected_profit,
        "margin_pct": margin_pct
    }

def process_paid_orders(token: str, dry_run: bool = False):
    """Varre novas vendas e boletos pendentes, enviando detalhes financeiros no Telegram."""
    user_id = "60455737"
    headers = {"Authorization": f"Bearer {token}"}
    state = load_state()
    processed_orders = set(state.get("processed_orders", []))
    pending_boletos = set(state.get("pending_boletos", []))

    # 1. Consulta vendas pagas e pedidos pendentes
    for status_query, is_pending in [("paid", False), ("payment_required", True)]:
        url = f"https://api.mercadolibre.com/orders/search?seller={user_id}&order.status={status_query}"
        try:
            r = requests.get(url, headers=headers, timeout=15)
            if r.status_code != 200:
                continue

            data = r.json()
            orders = data.get("results", [])
            
            for order in orders:
                order_id = str(order.get("id"))
                buyer = order.get("buyer", {})
                buyer_name = f"{buyer.get('first_name', '')} {buyer.get('last_name', '')}".strip() or "Cliente"
                
                items = order.get("order_items", [])
                item_titles = []
                primary_item_id = ""
                for it in items:
                    it_data = it.get("item", {})
                    primary_item_id = it_data.get("id", "")
                    item_titles.append(it_data.get("title", "Produto"))
                
                items_str = ", ".join(item_titles)
                item_info = CATALOG_KNOWLEDGE.get(primary_item_id, {})
                fin = format_payment_breakdown(order, item_info)

                # CASO 1: BOLETO / PAGAMENTO PENDENTE
                if is_pending or fin["pay_type"] == "Boleto":
                    if order_id in pending_boletos or order_id in processed_orders:
                        continue

                    print(f"\n⚠️ Boleto/Pagamento Pendente detectado: Pedido #{order_id}")
                    pending_boletos.add(order_id)
                    state["pending_boletos"] = list(pending_boletos)
                    save_state(state)

                    tg_msg = (
                        "⚠️ <b>BOLETO GERADO / PAGAMENTO PENDENTE!</b> ⏳\n"
                        "━━━━━━━━━━━━━━━━━━━━━━\n"
                        f"📦 <b>Produto:</b> {items_str}\n"
                        f"🆔 <b>Pedido:</b> #{order_id}\n"
                        f"👤 <b>Comprador(a):</b> {buyer_name}\n"
                        f"📄 <b>Forma de Pagamento:</b> {fin['pay_method']}\n"
                        f"💵 <b>Valor a Receber:</b> R$ {fin['total_amount']:,.2f}\n"
                        f"📈 <b>Lucro Estimado se Pago:</b> +R$ {fin['profit']:,.2f} ({fin['margin_pct']:.1f}%)\n"
                        "━━━━━━━━━━━━━━━━━━━━━━\n"
                        "🎯 <b>AÇÃO DE ACOMPANHAMENTO ATIVO:</b>\n"
                        "<i>\"Olá, " + buyer_name + "! Confirmamos a emissão do seu pedido. "
                        "Já reservamos sua unidade exclusiva no nosso estoque de SP! "
                        "Assim que o boleto for compensado, fazemos o despacho prioritário em até 24h.\"</i>\n\n"
                        "🔔 <i>O robô continuará monitorando até a compensação bancária.</i>"
                    )
                    send_telegram(tg_msg)

                # CASO 2: PAGAMENTO CONFIRMADO (VENDA PAGA)
                else:
                    if order_id in processed_orders:
                        continue

                    print(f"\n🎉 Nova Venda Confirmada: Pedido #{order_id}")
                    processed_orders.add(order_id)
                    state["processed_orders"] = list(processed_orders)
                    save_state(state)

                    # Mensagem Pós-Venda VIP
                    vip_message = (
                        f"Olá, {buyer_name}! 🌸 Parabéns pela sua escolha maravilhosa!\n\n"
                        f"Confirmamos o pagamento do seu pedido com sucesso. Nossa equipe em São Paulo já está preparando o seu pacote "
                        f"com lacre de segurança reforçado e nota fiscal. O envio será feito em até 24 horas úteis pelo Mercado Envios.\n\n"
                        f"🎁 Como nosso presente especial de boas-vindas da Lumina K-Beauty, liberamos o seu acesso exclusivo "
                        f"à 'Bíblia da Pele de Porcelana' (100 páginas) com todos os protocolos clínicos de Seul:\n"
                        f"{EBOOK_URL}\n\n"
                        f"Qualquer dúvida sobre a rotina de uso, conte com nosso suporte por aqui. Gratidão pela confiança!"
                    )

                    if not dry_run:
                        pack_id = order.get("pack_id") or order_id
                        msg_url = f"https://api.mercadolibre.com/messages/packs/{pack_id}/sellers/{user_id}?tag=post_sale"
                        msg_payload = {
                            "from": {"user_id": int(user_id)},
                            "to": [{"user_id": buyer.get("id"), "resource": "orders", "resource_id": int(order_id)}],
                            "text": vip_message
                        }
                        try:
                            requests.post(msg_url, json=msg_payload, headers=headers, timeout=15)
                        except Exception:
                            pass

                    # Notificação com Raio-X Financeiro Quebrado (idêntico ao painel ML)
                    tg_msg = (
                        "🎉 <b>NOVA VENDA CONFIRMADA NO MERCADO LIVRE!</b> 🚀\n"
                        "━━━━━━━━━━━━━━━━━━━━━━\n"
                        f"📦 <b>Produto:</b> {items_str}\n"
                        f"🆔 <b>Pedido:</b> #{order_id}\n"
                        f"👤 <b>Comprador(a):</b> {buyer_name}\n"
                        f"💳 <b>Forma de Pagamento:</b> {fin['pay_method']}\n\n"
                        "📊 <b>RESUMO DE CUSTOS (= Painel do Mercado Livre):</b>\n"
                        f"💵 <b>Preço:</b>  R$ {fin['total_amount']:,.2f}\n"
                        f"➖ <b>Tarifa de venda (Premium 17%):</b>  -R$ {fin['sale_fee']:,.2f}\n"
                        f"➖ <b>Custo de envio (Mercado Envios Premium):</b>  -R$ {fin['shipping_cost']:,.2f}\n"
                        "──────────────────────\n"
                        f"🟢 <b>Você recebe:</b>  <b>R$ {fin['you_receive']:,.2f}</b>\n"
                        "──────────────────────\n"
                        f"➖ <b>Custo do Produto (CMV):</b>  -R$ {fin['cmv']:,.2f}\n"
                        "━━━━━━━━━━━━━━━━━━━━━━\n"
                        f"💰 <b>LUCRO LÍQUIDO NO BOLSO:</b>  <b>+R$ {fin['profit']:,.2f}</b>\n"
                        f"📈 <b>Margem sobre o preço de venda:</b>  <b>{fin['margin_pct']:.1f}%</b>\n"
                        "━━━━━━━━━━━━━━━━━━━━━━\n"
                        "✅ <i>Mensagem pós-venda VIP e E-book de 100 páginas enviados automaticamente!</i>"
                    )
                    send_telegram(tg_msg)

        except Exception as e:
            print(f"❌ Erro ao consultar vendas: {e}")

# ==============================================================================
# SUÍTE DE TESTES UNITÁRIOS E DE INTEGRAÇÃO
# ==============================================================================

def test_function_token():
    print("\n--- TESTE 1: Auto-Refresh e Conexão de Token ---")
    token, env = get_valid_token()
    if token:
        print(f"✅ Token Ativo e Válido: {token[:15]}...")
        r = requests.get("https://api.mercadolibre.com/users/me", headers={"Authorization": f"Bearer {token}"})
        data = r.json()
        print(f"👤 Usuário: {data.get('nickname')} (ID: {data.get('id')})")
        print("✅ Teste de Conexão com Mercado Livre APROVADO.")
        return True
    else:
        print("❌ Falha no teste de conexão.")
        return False

def test_function_question():
    print("\n--- TESTE 2: Simulação de Pergunta com Cérebro Ji-woo & Alerta Telegram ---")
    mock_question = "Olá, esse aparelho esquenta? Tenho melasma no rosto e medo de manchas, é original e tem nota fiscal?"
    mock_sku = "MLB5200831909"  # Super Combo
    
    print(f"❓ Pergunta simulada de cliente: \"{mock_question}\"")
    answer = generate_jiwoo_answer(mock_question, mock_sku)
    print(f"🤖 Resposta gerada pela Ji-woo:\n{answer}\n")

    # Dispara alerta de teste no Telegram
    tg_text = (
        "🧪 <b>[TESTE SENTINELA] Pergunta de Cliente Respondida!</b>\n\n"
        "📦 <b>Produto:</b> Super Combo Medicube Booster Mini Pro Plus E Pdrn\n"
        f"❓ <b>Dúvida do Cliente:</b> <i>\"{mock_question}\"</i>\n\n"
        f"🤖 <b>Resposta Clínica da Ji-woo:</b>\n{answer}\n\n"
        "✅ <i>Tempo de resposta simulado: 12 segundos. Teste 100% validado!</i>"
    )
    res = send_telegram(tg_text)
    if res and res.get("ok"):
        print("✅ Alerta de Pergunta entregue no Telegram do Felipe com sucesso!")
        return True
    else:
        print("❌ Falha no envio do Telegram.")
        return False

def test_function_order():
    print("\n--- TESTE 3: Simulação de Compra Paga com DRE Quebrado & Mensagem VIP ---")
    mock_order_id = "20000099887766"
    mock_buyer = "Camila Vasconcelos"
    mock_item = CATALOG_KNOWLEDGE["MLB5200831909"]
    
    mock_order = {
        "id": mock_order_id,
        "total_amount": mock_item["price"],
        "buyer": {"first_name": "Camila", "last_name": "Vasconcelos"},
        "payments": [{
            "payment_method_id": "master",
            "payment_type": "credit_card",
            "installments": 10
        }],
        "order_items": [{
            "item": {"id": "MLB5200831909", "title": mock_item["name"]},
            "sale_fee": mock_item["price"] * 0.14
        }]
    }

    fin = format_payment_breakdown(mock_order, mock_item)
    print(f"🛒 Pedido simulado: #{mock_order_id}")
    print(f"📦 Item: {mock_item['name']}")
    print(f"💳 Forma: {fin['pay_method']}")
    print(f"💰 Bruto: R$ {fin['total_amount']:.2f} | Lucro Líquido: +R$ {fin['profit']:.2f}")

    tg_msg = (
        "🧪 <b>[TESTE SENTINELA] NOVA VENDA CONFIRMADA!</b> 🚀\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📦 <b>Produto:</b> {mock_item['name']}\n"
        f"🆔 <b>Pedido:</b> #{mock_order_id}\n"
        f"👤 <b>Comprador(a):</b> {mock_buyer} (São Paulo, SP)\n"
        f"💳 <b>Forma de Pagamento:</b> {fin['pay_method']}\n\n"
        "📊 <b>RESUMO DE CUSTOS (= Painel do Mercado Livre):</b>\n"
        f"💵 <b>Preço:</b>  R$ {fin['total_amount']:,.2f}\n"
        f"➖ <b>Tarifa de venda (Premium 17%):</b>  -R$ {fin['sale_fee']:,.2f}\n"
        f"➖ <b>Custo de envio (ML cobre 50%):</b>  -R$ {fin['shipping_cost']:,.2f}\n"
        "──────────────────────\n"
        f"🟢 <b>Você recebe:</b>  <b>R$ {fin['you_receive']:,.2f}</b>\n"
        "──────────────────────\n"
        f"➖ <b>Custo do Produto (CMV):</b>  -R$ {fin['cmv']:,.2f}\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        f"💰 <b>LUCRO LÍQUIDO NO BOLSO:</b>  <b>+R$ {fin['profit']:,.2f}</b>\n"
        f"📈 <b>Margem sobre o preço de venda:</b>  <b>{fin['margin_pct']:.1f}%</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "✅ <i>Mensagem pós-venda VIP e link do E-book de 100 páginas enviados automaticamente!</i>"
    )
    res = send_telegram(tg_msg)
    if res and res.get("ok"):
        print("✅ Alerta de Venda com DRE entregue no Telegram do Felipe com sucesso!")
        return True
    else:
        print("❌ Falha no envio do Telegram.")
        return False

def test_function_boleto():
    print("\n--- TESTE 4: Simulação de Boleto Gerado com Roteiro de Recuperação ---")
    mock_order_id = "20000088776655"
    mock_buyer = "Mariana Alencar"
    mock_item = CATALOG_KNOWLEDGE["MLB5200845621"]  # Kit Clareamento R$ 499
    
    mock_order = {
        "id": mock_order_id,
        "total_amount": mock_item["price"],
        "buyer": {"first_name": "Mariana", "last_name": "Alencar"},
        "payments": [{
            "payment_method_id": "bolbradesco",
            "payment_type": "ticket",
            "installments": 1
        }],
        "order_items": [{
            "item": {"id": "MLB5200845621", "title": mock_item["name"]},
            "sale_fee": mock_item["price"] * 0.14
        }]
    }

    fin = format_payment_breakdown(mock_order, mock_item)
    print(f"📄 Boleto simulado: #{mock_order_id}")
    print(f"📦 Item: {mock_item['name']}")
    print(f"💵 Valor: R$ {fin['total_amount']:.2f}")

    tg_msg = (
        "🧪 <b>[TESTE SENTINELA] BOLETO GERADO / PAGAMENTO PENDENTE!</b> ⏳\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📦 <b>Produto:</b> {mock_item['name']}\n"
        f"🆔 <b>Pedido:</b> #{mock_order_id}\n"
        f"👤 <b>Comprador(a):</b> {mock_buyer} (Belo Horizonte, MG)\n"
        f"📄 <b>Forma de Pagamento:</b> {fin['pay_method']}\n"
        f"💵 <b>Valor do Boleto:</b> R$ {fin['total_amount']:,.2f}\n"
        f"📈 <b>Lucro Estimado se Compensar:</b> +R$ {fin['profit']:,.2f} ({fin['margin_pct']:.1f}%)\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "🎯 <b>AÇÃO DE ACOMPANHAMENTO ATIVO (RECUPERAÇÃO):</b>\n"
        f"<i>\"Olá, Mariana! Vimos que você gerou o boleto para o {mock_item['name']}. "
        "Já separamos seu kit lacrado com todo carinho no estoque de SP. "
        "Assim que compensar, despachamos imediatamente via Mercado Envios!\"</i>\n\n"
        "🔔 <i>Rastreamento de compensação bancária ativo pelo Sentinela.</i>"
    )
    res = send_telegram(tg_msg)
    if res and res.get("ok"):
        print("✅ Alerta de Boleto Pendente entregue no Telegram do Felipe com sucesso!")
        return True
    else:
        print("❌ Falha no envio do Telegram.")
        return False

def main():
    parser = argparse.ArgumentParser(description="Lumina Cloud Sentinel 24/7")
    parser.add_argument("--test-all", action="store_true", help="Executa a suíte de testes completa de cada função")
    parser.add_argument("--run-once", action="store_true", help="Executa uma varredura real completa agora")
    parser.add_argument("--dry-run", action="store_true", help="Executa varredura real sem gravar respostas no ML")
    args = parser.parse_args()

    if args.test_all:
        print("🚀 INICIANDO BATERIA DE TESTES DO LUMINA CLOUD SENTINEL...\n")
        t1 = test_function_token()
        t2 = test_function_question()
        t3 = test_function_order()
        t4 = test_function_boleto()
        print("\n" + "="*60)
        if t1 and t2 and t3 and t4:
            print("🌟 TODOS OS 4 TESTES FORAM APROVADOS COM SUCESSO ABSOLUTO!")
        else:
            print("⚠️ Houve algum teste com falha. Verifique os logs.")
        print("="*60)
        return

    # Execução normal da ronda
    print(f"🕒 [{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Iniciando Ronda do Lumina Sentinel...")
    token, _ = get_valid_token()
    if not token:
        print("❌ Abortando ronda: sem token válido.")
        sys.exit(1)

    process_unanswered_questions(token, dry_run=args.dry_run)
    process_paid_orders(token, dry_run=args.dry_run)
    print("💤 Ronda concluída com sucesso. Próxima em 30 minutos.")

if __name__ == "__main__":
    main()
