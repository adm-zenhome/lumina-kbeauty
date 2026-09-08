/**
 * Endpoint Serverless 24/7 na Vercel para Recuperação de Abandono & PIX Pendente
 * Disparado por Webhooks de Pagamento (Mercado Pago / Yampi / Landing Page)
 */

const { AUDIO_MATRIX } = require("./jiwoo_brain");

module.exports = async (req, res) => {
  res.setHeader("Access-Control-Allow-Origin", "*");
  res.setHeader("Access-Control-Allow-Methods", "POST, GET, OPTIONS");
  res.setHeader("Access-Control-Allow-Headers", "Content-Type");

  if (req.method === "OPTIONS") return res.status(200).end();
  if (req.method === "GET") {
    return res.status(200).json({ status: "ready", service: "Recovery Engine" });
  }

  try {
    const data = req.body || {};
    const customerPhone = (data.phone || data.payer?.phone?.number || "").replace(/\D/g, "");
    const customerName = data.name || data.payer?.first_name || "querida";
    const eventType = data.type || data.action || "pix_pendente";

    if (!customerPhone) {
      return res.status(400).json({ error: "Telefone do cliente é obrigatório." });
    }

    let recoveryMessage = "";
    let audioUrl = AUDIO_MATRIX.recuperacao_pix;

    if (eventType === "pix_pendente") {
      recoveryMessage = 
`Oi, ${customerName}! Tudo bem? 🌸

Passei rapidinho só para te avisar que a sua caixinha lacrada da Lumina já está pré-separada no nosso centro de expedição em São Paulo!

Notamos que o seu código PIX ainda consta como pendente no sistema. Como o nosso lote de pronta entrega é concorrido, você prefere que eu mantenha reservado para envio hoje ou gostaria de gerar um novo código?`;
    } else {
      recoveryMessage = 
`Oi, ${customerName}! Tudo bem? 🌸

Vi que você estava escolhendo a sua rotina de K-Beauty no nosso site mas não concluiu o pedido. Ficou com alguma dúvida sobre a indicação para a sua pele ou sobre os prazos de entrega? Estou à disposição por aqui!`;
    }

    // Dispara via Z-API se configurado
    const ZAPI_INSTANCE = process.env.ZAPI_INSTANCE;
    const ZAPI_TOKEN = process.env.ZAPI_TOKEN;
    const ZAPI_CLIENT_TOKEN = process.env.ZAPI_CLIENT_TOKEN;

    if (ZAPI_INSTANCE && ZAPI_TOKEN) {
      const zapiBase = `https://api.z-api.io/instances/${ZAPI_INSTANCE}/token/${ZAPI_TOKEN}`;
      const headers = {
        "Content-Type": "application/json",
        ...(ZAPI_CLIENT_TOKEN ? { "Client-Token": ZAPI_CLIENT_TOKEN } : {})
      };

      // Envia Mensagem de Recuperação
      await fetch(`${zapiBase}/send-text`, {
        method: "POST",
        headers,
        body: JSON.stringify({ phone: customerPhone, message: recoveryMessage })
      });

      // Envia Áudio da Ji-woo
      await fetch(`${zapiBase}/send-voice`, {
        method: "POST",
        headers,
        body: JSON.stringify({ phone: customerPhone, audio: audioUrl })
      });
    }

    return res.status(200).json({
      success: true,
      phone: customerPhone,
      recoveryType: eventType,
      sentMessage: recoveryMessage,
      audioAttached: audioUrl
    });

  } catch (error) {
    console.error("Erro na recuperação:", error);
    return res.status(500).json({ error: error.message });
  }
};
