/**
 * Motor de Inteligência & Playbook da Ji-woo (Lumina K-Beauty)
 * Executa 100% Serverless na Vercel (Cloud 24/7).
 */

const BASE_URL = process.env.PUBLIC_URL || "https://lumina-skincare.vercel.app";

const AUDIO_MATRIX = {
  acolhimento: `${BASE_URL}/audios/audio_01_acolhimento.ogg`,
  estoque_garantia: `${BASE_URL}/audios/audio_02_estoque_brasil_garantia.ogg`,
  order_bump: `${BASE_URL}/audios/audio_03_order_bump_sabonete.ogg`,
  recuperacao_pix: `${BASE_URL}/audios/audio_04_recuperacao_pix.ogg`,
  medicube: `${BASE_URL}/audios/audio_05_medicube_alta_tecnologia.ogg`
};

const KNOWLEDGE_BASE = {
  melasma: {
    title: "Protocolo Anti-Manchas e Melasma (Bíblia da Pele Cap. 4)",
    copy: "Para manchas e melasma, o segredo da cosmética coreana é inibir a melanogênese sem inflamar a barreira cutânea. A nossa recomendação de ouro é a combinação do Sérum Numbuzin Nº 5 (Glutationa + Niacinamida 5%) com o Sérum de PDRN Salmon DNA. Eles uniformizam o tom da pele devolvendo a luminosidade natural logo nas primeiras semanas.",
    product: "Kit Clareamento & Manchas (Numbuzin 5 + PDRN)"
  },
  flacidez: {
    title: "Protocolo Lifting e Firmeza (Bíblia da Pele Cap. 6)",
    copy: "Para combater linhas finas e perda de sustentação, o padrão-ouro de Seul é o Medicube Booster Pro com o Sérum Firmador de Retinal da Celimax. O Booster Pro realiza microcorrentes e eletroporação clínica, abrindo canais celulares para os ativos penetrarem com 400x mais eficácia que a aplicação manual.",
    product: "Medicube Booster Pro + Creme Firmador Celimax",
    audio: AUDIO_MATRIX.medicube
  },
  poros: {
    title: "Protocolo Poros Invisíveis e Textura (Bíblia da Pele Cap. 3)",
    copy: "Para fechar poros aparentes e controlar a oleosidade sem ressecar, a base da rotina é o Tônico Anua Heartleaf 77% somado à limpeza profunda com o Sabonete Zero Foam. Ele desintoxica os microductos sebáceos, deixando a textura aveludada.",
    product: "Tônico Anua 77 + Sabonete Zero Foam"
  }
};

/**
 * Analisa a mensagem da cliente e retorna a melhor resposta e áudio contextual
 */
function processCustomerMessage(messageText, customerState = {}) {
  const text = (messageText || "").toLowerCase().trim();
  let responseText = "";
  let audioUrl = null;
  let nextState = customerState.state || "NEW";

  // 1. GATILHO: Chegada com lista de produtos do site (LP)
  if (text.includes("montei minha rotina de produtos k-beauty") || text.includes("cupom 5insta") || nextState === "NEW") {
    responseText = 
`Olá, maravilhosa! Tudo bem? Que alegria receber você por aqui! 🌸✨

Já localizei a sua seleção no nosso sistema de pronta entrega com o cupom **5INSTA** e **Frete Expresso Grátis** garantidos! 

Antes de eu separar a sua caixinha lacrada: me conta rapidinho... qual é a sua queixa principal de pele hoje? *(Manchinhas/Melasma, Poros/Oleosidade ou Linhas/Flacidez?)*`;
    audioUrl = AUDIO_MATRIX.acolhimento;
    nextState = "AWAITING_CONCERN";
    return { responseText, audioUrl, nextState };
  }

  // 2. QUEBRA DE OBJEÇÃO: Originalidade / Réplica / Garantia
  if (text.includes("original") || text.includes("réplica") || text.includes("falsificad") || text.includes("verdadeiro") || text.includes("garantia")) {
    responseText = 
`Com certeza! Prezamos pela máxima transparência e excelência clínica:

✅ **100% Originais de Seul:** Produtos importados diretamente das marcas parceiras (Medicube, Numbuzin, Celimax, Anua).
✅ **Lotes Lacrados:** Todas as embalagens possuem selo e código de autenticidade no fundo da caixa.
✅ **Garantia Incondicional:** Se notar qualquer divergência, reembolsamos 100% do seu valor.`;
    audioUrl = AUDIO_MATRIX.estoque_garantia;
    return { responseText, audioUrl, nextState };
  }

  // 3. QUEBRA DE OBJEÇÃO: Alfândega / Taxa / Prazo de Entrega
  if (text.includes("taxa") || text.includes("alfandega") || text.includes("alfândega") || text.includes("correios") || text.includes("quanto tempo") || text.includes("prazo") || text.includes("demora")) {
    responseText = 
`Pode ficar 100% tranquila! 📦

O nosso estoque físico fica sediado em **São Paulo**! 
- **Zero risco de taxa de alfândega** (o lote já está internalizado no Brasil).
- Despacho imediato por transportadora expressa e Sedex para qualquer região do país.
- Código de rastreamento enviado diretamente no seu WhatsApp no mesmo dia útil!`;
    audioUrl = AUDIO_MATRIX.estoque_garantia;
    return { responseText, audioUrl, nextState };
  }

  // 4. DIAGNÓSTICO CONSULTIVO: Queixas de Pele
  if (text.includes("mancha") || text.includes("melasma") || text.includes("uniformiz")) {
    responseText = 
`Perfeita colocação! Para o seu caso, o protocolo de Seul é cirúrgico:

${KNOWLEDGE_BASE.melasma.copy}

Essa combinação vai agir diretamente na uniformidade da sua pele sem irritar ou descamar. 

Você gostaria de fechar o seu pacote via **PIX com envio prioritário hoje** ou no **Cartão em até 12x**?`;
    nextState = "OFFER_ORDER_BUMP";
    return { responseText, audioUrl, nextState };
  }

  if (text.includes("ruga") || text.includes("flacide") || text.includes("colágeno") || text.includes("medicube") || text.includes("booster")) {
    responseText = 
`Excelente escolha! Quando o assunto é efeito lifting e regeneração profunda:

${KNOWLEDGE_BASE.flacidez.copy}

A tecnologia de Seul entrega o que nenhum cosmético tópico convencional consegue sozinho!

Quer que eu reserve a sua unidade do Medicube pronta entrega agora mesmo?`;
    audioUrl = AUDIO_MATRIX.medicube;
    nextState = "OFFER_ORDER_BUMP";
    return { responseText, audioUrl, nextState };
  }

  if (text.includes("poro") || text.includes("oleosidade") || text.includes("acne") || text.includes("espinha")) {
    responseText = 
`Maravilha! Tratar poros dilatados exige desobstrução e acalmia:

${KNOWLEDGE_BASE.poros.copy}

A sua pele vai ganhar aquele toque aveludado e sequinho durante o dia todo!`;
    nextState = "OFFER_ORDER_BUMP";
    return { responseText, audioUrl, nextState };
  }

  // 5. ORDER BUMP ESTRATÉGICO (+R$ 170)
  if (customerState.state === "OFFER_ORDER_BUMP" || text.includes("pix") || text.includes("link") || text.includes("fechar") || text.includes("comprar")) {
    responseText = 
`Maravilha! Antes de eu gerar o seu código com frete grátis, deixa eu te dar uma dica de ouro de consultora: 🌸

Como o seu pacote já está com **Frete Grátis** garantido hoje, você gostaria de incluir o **Sabonete Clínico Zero Foam (120g)** por apenas **R$ 170,05**?

Ele remove os resíduos profundos dos poros e faz os séruns renderem o dobro na absorção da sua pele. Quer que eu coloque junto no mesmo envio?`;
    audioUrl = AUDIO_MATRIX.order_bump;
    nextState = "AWAITING_PAYMENT_METHOD";
    return { responseText, audioUrl, nextState };
  }

  // 6. DADOS DE PAGAMENTO (PIX)
  if (text.includes("sim") || text.includes("pode colocar") || text.includes("quero") || text.includes("não") || text.includes("só o kit") || customerState.state === "AWAITING_PAYMENT_METHOD") {
    responseText = 
`Tudo pronto! Seu pacote VIP já está em processo de separação:

🎁 **Itens da sua Rotina:** Reservados com Lote Lacrado
🚚 **Frete:** Expresso Grátis para Todo o Brasil
📚 **Bônus Especial:** Acesso imediato à Bíblia Digital da Pele de Porcelana (100 Páginas)

🔑 **Chave PIX Oficial Lumina:**
\`contato@luminacare.com.br\`
*(Nome: LUMINA Cuidados & Cosmética)*

Assim que fizer, basta me enviar o comprovante por aqui e o seu endereço com CEP que eu já emito a sua etiqueta de envio prioritário! ✨📦`;
    nextState = "WAITING_PROOF";
    return { responseText, audioUrl: null, nextState };
  }

  // RESPOSTA PADRÃO ACOLHEDORA
  responseText = 
`Entendi perfeitamente, querida! Estou aqui à sua disposição. Qualquer dúvida sobre a ordem de aplicação dos produtos ou indicação para a sua pele, pode me perguntar! 🌸`;

  return { responseText, audioUrl, nextState };
}

module.exports = {
  processCustomerMessage,
  AUDIO_MATRIX,
  KNOWLEDGE_BASE
};
