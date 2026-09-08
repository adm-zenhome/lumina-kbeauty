/**
 * Motor Conversacional Inteligente & Empático da Ji-woo (Lumina K-Beauty)
 * Combina LLM (Gemini) com Fallback Conversacional de Alta Qualidade (zero repetição).
 */

const GEMINI_API_KEY = process.env.GEMINI_API_KEY || "";
const BASE_URL = process.env.PUBLIC_URL || "https://lumina-skincare.vercel.app";

const AUDIO_MATRIX = {
  estoque_garantia: `${BASE_URL}/audios/audio_02_estoque_brasil_garantia.ogg`,
  order_bump: `${BASE_URL}/audios/audio_03_order_bump_sabonete.ogg`,
  recuperacao_pix: `${BASE_URL}/audios/audio_04_recuperacao_pix.ogg`,
  medicube: `${BASE_URL}/audios/audio_05_medicube_alta_tecnologia.ogg`
};

/**
 * Motor Heurístico Conversacional Humano (Ativado instantaneamente ou em caso de 429 da LLM)
 */
function getSmartFallbackReply(messageText, history = []) {
  const text = (messageText || "").toLowerCase().trim();

  // 1. MANCHAS / MELASMA
  if (text.includes("melasma") || text.includes("mancha") || text.includes("uniformiz") || text.includes("clarear")) {
    return {
      reply: 
`Ah, eu te entendo perfeitamente, maravilhosa... Melasma é uma das queixas que mais acolho por aqui! E eu sei bem a frustração de testar vários ácidos agressivos de farmácia que deixam a pele vermelha ou causam aquele efeito rebote. 🌸

Na rotina coreana, o segredo é clarear acalmando a barreira: a nossa indicação de ouro é o **Sérum Numbuzin Nº 5 (com Glutationa pura e Niacinamida)** associado ao **Sérum de PDRN**. Eles uniformizam as manchinhas e devolvem a luminosidade natural de porcelana logo nos primeiros 14 dias de uso.

Você já costuma usar protetor solar todo dia ou essa seria sua primeira rotina completa de skincare?`,
      audio: null
    };
  }

  // 2. POROS DILATADOS / OLEOSIDADE / ACNE
  if (text.includes("poro") || text.includes("oleos") || text.includes("acne") || text.includes("cravos") || text.includes("espinha")) {
    return {
      reply: 
`Perfeito! Poros dilatados e excesso de brilho acontecem quando a pele está pedindo equilíbrio de água e acalmia nos microductos. ✨

O protocolo que as dermatologistas coreanas mais prescrevem é a dupla do **Tônico Anua Heartleaf 77%** com a limpeza profunda do **Sabonete Clínico Zero Foam**. Ele desintoxica os poros sem ressecar ou repuxar a pele, deixando aquele toque sedoso e aveludado o dia todo!

Quer que eu te passe o passo a passo de como encaixar na sua rotina da manhã e da noite?`,
      audio: null
    };
  }

  // 3. MEDICUBE BOOSTER PRO / FLACIDEZ / LINHAS / RUGAS
  if (text.includes("medicube") || text.includes("booster") || text.includes("aparelho") || text.includes("ruga") || text.includes("flacide") || text.includes("lifting") || text.includes("colágeno")) {
    return {
      reply: 
`O **Medicube Booster Pro** é simplesmente surreal! Ele é o segredo por trás do efeito glass skin e do lifting imediato que você vê nas celebridades de Seul. 🤍

Ele não é um massageador comum: ele utiliza eletroporação clínica e microcorrentes, abrindo microcanais temporários que fazem qualquer sérum penetrar com **400x mais profundidade** na derme do que aplicando apenas com as mãos. Em 5 minutos de uso noturno você já sente o efeito tensor nítido!

Vou te mandar uma breve explicação em áudio de como ele age nas camadas mais profundas:`,
      audio: AUDIO_MATRIX.medicube
    };
  }

  // 4. AUTENTICIDADE & TAXA DE ALFÂNDEGA
  if (text.includes("original") || text.includes("taxa") || text.includes("alfandega") || text.includes("alfândega") || text.includes("réplica") || text.includes("verdadeiro") || text.includes("importa")) {
    return {
      reply: 
`Pode ficar 100% tranquila e segura quanto a isso! 🛡️✨

Todos os nossos produtos vêm diretamente das marcas oficiais em Seul (Medicube, Numbuzin, Anua, Celimax), lacrados de fábrica e com código de lote de autenticidade.

E o detalhe mais importante: **nosso estoque físico fica sediado em São Paulo!** O seu pedido é despachado por transportadora expressa no mesmo dia útil. **Zero risco de taxa de alfândega** e sem você precisar esperar semanas por encomendas internacionais dos Correios!`,
      audio: AUDIO_MATRIX.estoque_garantia
    };
  }

  // 5. PEDIDO DE PIX / FECHAMENTO / LINK
  if (text.includes("pix") || text.includes("pagar") || text.includes("comprar") || text.includes("chave") || text.includes("link") || text.includes("fechar")) {
    return {
      reply: 
`Maravilha! Antes de eu gerar o seu código com frete grátis, deixa eu te dar uma dica de ouro de consultora: 🌸

Como o seu pacote já está com **Frete Grátis** garantido hoje, você gostaria de incluir o **Sabonete Clínico Zero Foam (120g)** por apenas **R$ 170,05**? Ele prepara a pele para os séruns agirem com o dobro de absorção!

Se preferir só o kit principal, me avisa que eu já gero a sua chave PIX com o cupom **5INSTA** aplicado! ✨`,
      audio: AUDIO_MATRIX.order_bump
    };
  }

  // 6. CONFIRMAÇÃO DO PEDIDO (SIM / QUERO / SÓ O KIT)
  if (text.includes("sim") || text.includes("quero") || text.includes("pode colocar") || text.includes("só o kit") || text.includes("não")) {
    return {
      reply: 
`Perfeito, querida! Seu pedido já está sendo preparado para embalagem com lote lacrado:

🎁 **Sua Rotina Coreana:** Reservada
🚚 **Frete:** Expresso Grátis para Todo o Brasil
📚 **Presente VIP:** Acesso à Bíblia Digital da Pele de Porcelana (100 Páginas)

🔑 **Chave PIX Oficial Lumina:**
\`contato@luminacare.com.br\`
*(Nome: LUMINA Cuidados & Cosmética)*

Assim que fizer, só me mandar o comprovante por aqui e o seu endereço com CEP para eu já despachar o seu pacote hoje mesmo! 📦✨`,
      audio: null
    };
  }

  // 7. DEFAULT HUMANO
  return {
    reply: 
`Que ótimo falar com você! Me conta um pouquinho mais sobre como é a sua rotina hoje e o que mais te incomoda na sua pele no momento (manchas, textura, poros ou viço)? Estou aqui para te ajudar a escolher exatamente o que funciona pra você! 🌸`,
    audio: null
  };
}

async function processCustomerMessage(messageText, conversationHistory = []) {
  // 1. Tenta chamar o Gemini 3.6 Flash se a chave estiver livre
  if (GEMINI_API_KEY) {
    try {
      const url = `https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent?key=${GEMINI_API_KEY}`;
      const systemPrompt = `Você é a Ji-woo, dermoconsultora da marca Lumina (cosmética coreana). Atenda a cliente no WhatsApp. Seja calorosa, empática, profissional e use no máximo 2 parágrafos curtos. NUNCA pergunte o que ela já disse. Conhecimento: Melasma trata com Numbuzin 5 (glutationa) + PDRN; Poros com Anua 77; Linhas com Medicube Booster Pro; Estoque pronta entrega em São Paulo sem risco de taxa de alfândega.`;
      
      const contents = [
        { role: "user", parts: [{ text: systemPrompt }] },
        { role: "model", parts: [{ text: "Entendido. Atenderei com calor humano, empatia e sem repetições." }] }
      ];

      for (const m of conversationHistory.slice(-4)) {
        contents.push({
          role: m.role === "assistant" ? "model" : "user",
          parts: [{ text: m.content }]
        });
      }
      contents.push({ role: "user", parts: [{ text: messageText }] });

      const controller = new AbortController();
      const timeout = setTimeout(() => controller.abort(), 4000);

      const resp = await fetch(url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          contents,
          generationConfig: { temperature: 0.7, maxOutputTokens: 250 }
        }),
        signal: controller.signal
      });
      clearTimeout(timeout);

      if (resp.ok) {
        const data = await resp.json();
        const textResp = data?.candidates?.[0]?.content?.parts?.[0]?.text?.trim();
        if (textResp) {
          let audio = null;
          const lower = messageText.toLowerCase();
          if (lower.includes("original") || lower.includes("taxa") || lower.includes("alfandega")) {
            audio = AUDIO_MATRIX.estoque_garantia;
          } else if (lower.includes("medicube") || lower.includes("booster")) {
            audio = AUDIO_MATRIX.medicube;
          }
          return { responseText: textResp, audioUrl: audio };
        }
      }
    } catch (e) {
      // Silently fall back to the smart conversational engine
    }
  }

  // 2. Fallback conversacional empático e cirúrgico (zero repetição)
  const fallback = getSmartFallbackReply(messageText, conversationHistory);
  return {
    responseText: fallback.reply,
    audioUrl: fallback.audio
  };
}

module.exports = {
  processCustomerMessage
};
