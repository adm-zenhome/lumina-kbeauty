/**
 * Webhook Serverless 24/7 na Vercel para WhatsApp (Lumina K-Beauty)
 * Compatível com Z-API e Evolution API.
 */

const { processCustomerMessage } = require("./jiwoo_brain");

// Cache em memória efêmero para demonstração / serverless
// Em produção prolongada, recomenda-se salvar em KV / Supabase
const sessionStore = new Map();

module.exports = async (req, res) => {
  // CORS
  res.setHeader("Access-Control-Allow-Origin", "*");
  res.setHeader("Access-Control-Allow-Methods", "POST, GET, OPTIONS");
  res.setHeader("Access-Control-Allow-Headers", "Content-Type");

  if (req.method === "OPTIONS") {
    return res.status(200).end();
  }

  if (req.method === "GET") {
    return res.status(200).json({
      status: "online",
      agent: "Ji-woo AI Concierge (Lumina K-Beauty)",
      engine: "Serverless Vercel Edge",
      timestamp: new Date().toISOString()
    });
  }

  if (req.method !== "POST") {
    return res.status(405).json({ error: "Method not allowed" });
  }

  try {
    const payload = req.body || {};
    
    // Normalização de campos vindos da Z-API ou Evolution API
    let phone = payload.phone || (payload.data && payload.data.key && payload.data.key.remoteJid) || payload.from || "";
    phone = phone.replace("@s.whatsapp.net", "").replace(/\D/g, "");

    let messageText = "";
    if (payload.text && payload.text.message) {
      messageText = payload.text.message;
    } else if (payload.message) {
      messageText = typeof payload.message === "string" ? payload.message : (payload.message.conversation || payload.message.extendedTextMessage?.text || "");
    } else if (payload.data && payload.data.message) {
      messageText = payload.data.message.conversation || payload.data.message.extendedTextMessage?.text || "";
    }

    // Se não houver mensagem válida ou for mensagem enviada pelo próprio bot
    if (payload.fromMe === true || (payload.data && payload.data.key && payload.data.key.fromMe)) {
      return res.status(200).json({ status: "ignored_from_me" });
    }

    if (!messageText) {
      return res.status(200).json({ status: "no_text_content" });
    }

    // Recupera estado da sessão
    const currentSession = sessionStore.get(phone) || { state: "NEW" };
    
    // Processa no Cérebro da Ji-woo
    const result = processCustomerMessage(messageText, currentSession);
    
    // Atualiza estado
    sessionStore.set(phone, { state: result.nextState, lastUpdated: Date.now() });

    // Envio para WhatsApp se credenciais da Z-API estiverem configuradas
    const ZAPI_INSTANCE = process.env.ZAPI_INSTANCE;
    const ZAPI_TOKEN = process.env.ZAPI_TOKEN;
    const ZAPI_CLIENT_TOKEN = process.env.ZAPI_CLIENT_TOKEN;

    if (ZAPI_INSTANCE && ZAPI_TOKEN && phone) {
      const zapiBase = `https://api.z-api.io/instances/${ZAPI_INSTANCE}/token/${ZAPI_TOKEN}`;
      const headers = {
        "Content-Type": "application/json",
        ...(ZAPI_CLIENT_TOKEN ? { "Client-Token": ZAPI_CLIENT_TOKEN } : {})
      };

      // 1. Envia Texto
      if (result.responseText) {
        await fetch(`${zapiBase}/send-text`, {
          method: "POST",
          headers,
          body: JSON.stringify({
            phone: phone,
            message: result.responseText
          })
        }).catch(err => console.error("Erro envio Z-API texto:", err));
      }

      // 2. Envia Áudio (PTT - Nota de Voz com onda verde nativa) se houver
      if (result.audioUrl) {
        await fetch(`${zapiBase}/send-voice`, {
          method: "POST",
          headers,
          body: JSON.stringify({
            phone: phone,
            audio: result.audioUrl
          })
        }).catch(err => console.error("Erro envio Z-API audio:", err));
      }
    }

    return res.status(200).json({
      success: true,
      phone,
      state: result.nextState,
      reply: result.responseText,
      audioAttached: result.audioUrl || null
    });

  } catch (error) {
    console.error("Erro no processamento do webhook:", error);
    return res.status(500).json({ error: error.message });
  }
};
