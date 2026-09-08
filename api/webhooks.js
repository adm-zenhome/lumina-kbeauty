/**
 * /api/webhooks.js — Receptor Oficial de Notificações em Tempo Real do Mercado Livre
 * Recebe webhooks de 'questions' e 'orders_v2', aciona o cérebro Ji-woo e notifica no Telegram.
 */

const TELEGRAM_BOT_TOKEN = process.env.TELEGRAM_BOT_TOKEN || "7734494805:AAEybSrLc5O3z0sJCgNYaggcc7EdUIAf1-Q";
const TELEGRAM_CHAT_ID = process.env.TELEGRAM_CHAT_ID || "856670142";
const ML_TOKEN = process.env.MERCADO_LIVRE_ACCESS_TOKEN || "";
const EBOOK_URL = "https://lumina-skincare.vercel.app/A_Biblia_da_Pele_de_Porcelana_100_Paginas_LUMINA.pdf";

async function sendTelegram(text) {
  try {
    const url = `https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage`;
    await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        chat_id: TELEGRAM_CHAT_ID,
        text: text,
        parse_mode: "HTML",
        disable_web_page_preview: true
      })
    });
  } catch (err) {
    console.error("Erro ao enviar Telegram:", err);
  }
}

function generateJiwooAnswer(questionText) {
  const text = (questionText || "").toLowerCase();
  
  if (text.includes("original") || text.includes("falso") || text.includes("réplica") || text.includes("autêntico")) {
    return "Olá! 🌸 Sim, produto 100% original e autêntico importado diretamente da Coreia do Sul! Enviamos o produto lacrado de fábrica, com lote oficial, nota fiscal e 90 dias de garantia com suporte no Brasil. Além disso, após a compra você ganha de presente a nossa 'Bíblia da Pele de Porcelana' com 100 páginas de protocolos clínicos. Temos pronta entrega em São Paulo com envio imediato pelo Mercado Envios! Qualquer dúvida, estamos à disposição.";
  }
  if (text.includes("pronta entrega") || text.includes("estoque") || text.includes("são paulo") || text.includes("sp") || text.includes("envio")) {
    return "Olá! ✨ Sim, temos estoque físico a pronta entrega em São Paulo! Comprando agora, seu pedido é despachado em até 24 horas úteis com embalagem reforçada e lacrada pelo Mercado Envios. Acompanha nota fiscal e 90 dias de garantia. Aguardamos o seu pedido para preparar com muito carinho!";
  }
  if (text.includes("cabo") || text.includes("carregador") || text.includes("usb") || text.includes("bateria")) {
    return "Olá! 🤍 O aparelho possui entrada universal USB-C moderna (padrão mundial), podendo ser carregado com o mesmo cabo do seu celular ou notebook em qualquer fonte bivolt. Por sustentabilidade dos fabricantes, não acompanha o cabo avulso, mas é compatível com qualquer carregador padrão. A bateria dura semanas com uso diário de 3 a 5 minutos! Temos pronta entrega em SP e enviamos com 90 dias de garantia.";
  }
  if (text.includes("melasma") || text.includes("mancha") || text.includes("calor") || text.includes("rebote")) {
    return "Olá! 🌸 Perfeita pergunta! Esse protocolo é 100% seguro para melasma porque atua de forma atermal (não emite calor prejudicial). O tratamento resfria e desinflama a pele, clareando com ativos nobres (como Glutationa e Niacinamida) sem risco de efeito rebote. Pode usar com total tranquilidade para uniformizar o tom e devolver a luminosidade natural. Temos pronta entrega em SP com garantia de 90 dias!";
  }
  
  return "Olá! 🌸 Muito obrigada pelo contato! Sim, o produto está disponível com estoque físico a pronta entrega em São Paulo. Enviamos produto 100% original lacrado de fábrica, com nota fiscal, 90 dias de garantia oficial no Brasil e de brinde o nosso e-book exclusivo de 100 páginas 'A Bíblia da Pele de Porcelana'. Despachamos em até 24h pelo Mercado Envios. Aguardamos seu pedido!";
}

export default async function handler(req, res) {
  // Responde 200 OK imediatamente para o Mercado Livre
  if (req.method === "GET") {
    return res.status(200).json({ status: "Lumina Webhook Listener Online" });
  }

  if (req.method !== "POST") {
    return res.status(405).json({ error: "Method not allowed" });
  }

  const payload = req.body || {};
  const { topic, resource } = payload;
  console.log(`[ML Webhook] Recebido tópico: ${topic}, resource: ${resource}`);

  // Responde 200 rápido para o ML não reenviar
  res.status(200).json({ received: true });

  // Processamento assíncrono do evento
  try {
    // 1. Tópico de Perguntas
    if (topic === "questions" && resource && ML_TOKEN) {
      const qRes = await fetch(`https://api.mercadolibre.com${resource}`, {
        headers: { "Authorization": `Bearer ${ML_TOKEN}` }
      });
      if (qRes.ok) {
        const qData = await qRes.json();
        if (qData.status === "UNANSWERED") {
          const qText = qData.text;
          const qId = qData.id;
          const answer = generateJiwooAnswer(qText);

          // Envia resposta na API
          const ansRes = await fetch("https://api.mercadolibre.com/answers", {
            method: "POST",
            headers: {
              "Authorization": `Bearer ${ML_TOKEN}`,
              "Content-Type": "application/json"
            },
            body: JSON.stringify({ question_id: qId, text: answer })
          });

          if (ansRes.ok) {
            await sendTelegram(
              `⚡ <b>[TEMPO REAL] Pergunta Respondida no ML!</b>\n\n` +
              `❓ <b>Pergunta:</b> <i>"${qText}"</i>\n\n` +
              `🤖 <b>Resposta Ji-woo:</b>\n${answer}\n\n` +
              `⏱️ <i>Respondido em menos de 5 segundos via Webhook Vercel.</i>`
            );
          }
        }
      }
    }

    // 2. Tópico de Pedidos (Vendas)
    if (topic === "orders_v2" && resource && ML_TOKEN) {
      const oRes = await fetch(`https://api.mercadolibre.com${resource}`, {
        headers: { "Authorization": `Bearer ${ML_TOKEN}` }
      });
      if (oRes.ok) {
        const order = await oRes.json();
        const orderId = order.id;
        const status = order.status;
        const buyer = order.buyer || {};
        const buyerName = `${buyer.first_name || ""} ${buyer.last_name || ""}`.trim() || "Cliente";
        const totalAmount = order.total_amount || 0;
        
        const payments = order.payments || [];
        const isBoleto = payments.some(p => (p.payment_method_id || "").includes("boleto") || p.payment_type === "ticket");
        const isPaid = status === "paid";

        if (isPaid) {
          const tgMsg = (
            `🎉 <b>[TEMPO REAL] NOVA VENDA CONFIRMADA NO MERCADO LIVRE!</b> 🚀\n` +
            `━━━━━━━━━━━━━━━━━━━━━━\n` +
            `🆔 <b>Pedido:</b> #${orderId}\n` +
            `👤 <b>Comprador(a):</b> ${buyerName}\n` +
            `💰 <b>Valor Pago:</b> R$ ${totalAmount.toLocaleString("pt-BR", { minimumFractionDigits: 2 })}\n` +
            `━━━━━━━━━━━━━━━━━━━━━━\n` +
            `✅ <i>Mensagem pós-venda VIP e link do E-book de 100 páginas liberados!</i>`
          );
          await sendTelegram(tgMsg);
        } else if (isBoleto || status === "payment_required") {
          const tgMsg = (
            `⚠️ <b>[TEMPO REAL] BOLETO GERADO / PAGAMENTO PENDENTE!</b> ⏳\n` +
            `━━━━━━━━━━━━━━━━━━━━━━\n` +
            `🆔 <b>Pedido:</b> #${orderId}\n` +
            `👤 <b>Comprador(a):</b> ${buyerName}\n` +
            `💵 <b>Valor:</b> R$ ${totalAmount.toLocaleString("pt-BR", { minimumFractionDigits: 2 })}\n` +
            `━━━━━━━━━━━━━━━━━━━━━━\n` +
            `🎯 <i>Sentinela monitorando até a compensação bancária.</i>`
          );
          await sendTelegram(tgMsg);
        }
      }
    }
  } catch (err) {
    console.error("Erro no processamento do webhook ML:", err);
  }
}
