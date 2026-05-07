export const SUPPORTED_LOCALES = ['en', 'es', 'pt', 'ar', 'zh'] as const;
export type Locale = (typeof SUPPORTED_LOCALES)[number];

export function resolveLocale(lang?: string): Locale {
  if (!lang) return 'en';
  const normalized = lang.toLowerCase();
  return (SUPPORTED_LOCALES as readonly string[]).includes(normalized)
    ? (normalized as Locale)
    : 'en';
}

export const localeLabels: Record<Locale, string> = {
  en: 'English',
  es: 'Español',
  pt: 'Português',
  ar: 'العربية',
  zh: '中文',
};

// ─────────────────────────────────────────────────────────────────────────────
// HOME COPY — neurocomportamental: equilíbrio medo / esperança + âncora numérica
// ─────────────────────────────────────────────────────────────────────────────
export const homeCopy: Record<Locale, {
  heroTitle: string;
  heroSubtitle: string;
  heroStatement: string;
  heroAnchor: string;          // âncora cognitiva numérica (novo)
  primaryCta: string;
  secondaryCta: string;
  authorityTitle: string;
  authorityItems: [string, string, string, string];
  feature1Title: string;
  feature1Body: string;
  feature2Title: string;
  feature2Body: string;
  feature3Title: string;
  feature3Body: string;
  edgeTitle: string;
  edgeBody: string;
  // Prova social (novo)
  socialProofLabel: string;
  socialProofItems: [string, string, string];
  // Disclaimer legal visível (P0 jurídico — CVM/ESMA)
  legalBadge: string;
}> = {
  en: {
    heroTitle: 'Uni IA — Structure first. Profit follows.',
    heroSubtitle:
      'Institutional architecture for risk, discipline and execution. Eight specialized agents reach consensus before any signal is released.',
    heroStatement: 'Build governance before chasing returns.',
    heroAnchor: '8 agents · 4-layer governance · 100% auditable decisions',
    primaryCta: 'Start Premium Access',
    secondaryCta: 'Join Free Telegram',
    authorityTitle: 'Institutional control layer',
    authorityItems: [
      'Deterministic backtesting',
      'Mandatory RiskFilter (SENTINEL)',
      'Measurable governance gates',
      'Capital protected by mandate',
    ],
    feature1Title: 'Position Guardian Agent',
    feature1Body:
      'When market structure flips after entry, your risk desk receives a close-position alert before the crowd reacts. Discipline enforced by code, not willpower.',
    feature2Title: 'Multi-Timeframe Validation',
    feature2Body:
      'Scalping signals are only released when weekly and daily structure agree with intraday momentum — eliminating low-probability setups at the source.',
    feature3Title: 'Sentiment and Volatility Engine',
    feature3Body:
      'News, sentiment and volatility are fused with live Bybit momentum. Emotional entries are flagged and suppressed before they become losses.',
    edgeTitle: 'Why Paying Clients Switch to Uni IA',
    edgeBody:
      'Compared to generic signal channels, copy-trading rooms and static chart alerts, Uni IA delivers explainable alerts, real-time Bybit alignment and execution-ready confidence scores backed by full audit trails.',
    socialProofLabel: 'Governance in numbers',
    socialProofItems: [
      '8 specialized agents voting per signal',
      '4-layer governance gate before any dispatch',
      '100% traceable decisions — zero silent failures',
    ],
    // ⚠️ LEGAL — P0: visível no hero, obrigatório CVM/SEC/ESMA
    legalBadge:
      '⚠️ Not a licensed broker or investment adviser. Signals are analytical intelligence only. Free plan signals are delayed 15 minutes. Past results do not guarantee future performance. All trading involves risk of loss.',
  },

  es: {
    heroTitle: 'Uni IA — Estructura primero. El beneficio llega después.',
    heroSubtitle:
      'Arquitectura institucional de riesgo, disciplina y ejecución. Ocho agentes especializados alcanzan consenso antes de liberar cualquier señal.',
    heroStatement: 'Construye gobernanza antes de perseguir retornos.',
    heroAnchor: '8 agentes · gobernanza de 4 capas · decisiones 100% auditables',
    primaryCta: 'Comenzar acceso premium',
    secondaryCta: 'Entrar al Telegram gratis',
    authorityTitle: 'Capa institucional de control',
    authorityItems: [
      'Backtest determinístico',
      'RiskFilter obligatorio (SENTINEL)',
      'Gates de gobernanza medibles',
      'Capital protegido por mandato',
    ],
    feature1Title: 'Agente guardián de posición',
    feature1Body:
      'Si la estructura del mercado cambia tras la entrada, recibes alerta de cierre antes que la mayoría. Disciplina aplicada por código, no por fuerza de voluntad.',
    feature2Title: 'Validación multi-timeframe',
    feature2Body:
      'Las señales solo se liberan cuando semanal y diario confirman el impulso intradía, eliminando setups de baja probabilidad desde el origen.',
    feature3Title: 'Motor de sentimiento y volatilidad',
    feature3Body:
      'Fusiona noticias, sentimiento y presión de volatilidad con señales en vivo para identificar y suprimir entradas emocionales antes de que se conviertan en pérdidas.',
    edgeTitle: 'Por qué los clientes de pago eligen Uni IA',
    edgeBody:
      'Frente a canales genéricos, copy-trading y alertas estáticas, Uni IA entrega contexto de riesgo, alineamiento con Bybit y score explicable con trazabilidad de auditoría completa.',
    socialProofLabel: 'Gobernanza en números',
    socialProofItems: [
      '8 agentes especializados votan por señal',
      'Gate de gobernanza de 4 capas antes del despacho',
      'Decisiones 100% trazables — cero fallos silenciosos',
    ],
    legalBadge:
      '⚠️ No somos corredor ni asesor de inversiones autorizado. Las señales son inteligencia analítica, no recomendaciones. Las señales del plan gratuito tienen 15 minutos de retraso. Los resultados pasados no garantizan rendimiento futuro. Todo trading implica riesgo de pérdida.',
  },

  pt: {
    heroTitle: 'Uni IA — Estrutura primeiro. O lucro vem depois.',
    heroSubtitle:
      'Arquitetura institucional de risco, disciplina e execução com camada neurocomportamental. Oito agentes especializados votam antes de qualquer sinal ser liberado.',
    heroStatement: 'Governe antes de operar.',
    heroAnchor: '8 agentes · governança de 4 camadas · decisões 100% auditáveis',
    primaryCta: 'Iniciar Acesso Premium',
    secondaryCta: 'Entrar no Telegram Grátis',
    authorityTitle: 'Camada institucional de controle',
    authorityItems: [
      'Backtest determinístico',
      'RiskFilter obrigatório (SENTINEL)',
      'Gates de governança mensuráveis',
      'Capital protegido por mandato',
    ],
    feature1Title: 'Agente Guardião de Posição',
    feature1Body:
      'Quando a estrutura vira após sua entrada, você recebe alerta de fechamento antes do mercado em massa. Disciplina aplicada por código — não por força de vontade.',
    feature2Title: 'Validação Multi-Timeframe',
    feature2Body:
      'Sinais de curto prazo só saem quando semanal e diário confirmam o mesmo lado, eliminando setups de baixa probabilidade na origem.',
    feature3Title: 'Motor de Sentimento e Volatilidade',
    feature3Body:
      'Notícias, sentimento e pressão de volatilidade são combinados com sinais em tempo real do Bybit para identificar e suprimir entradas emocionais antes que virem perdas.',
    edgeTitle: 'Por que clientes pagantes migram para o Uni IA',
    edgeBody:
      'Contra grupos genéricos, copy-trading e alertas estáticos, o Uni IA entrega contexto de risco, alinhamento Bybit e score explicável com trilha de auditoria completa.',
    socialProofLabel: 'Governança em números',
    socialProofItems: [
      '8 agentes especializados votam por sinal',
      'Gate de governança de 4 camadas antes de qualquer disparo',
      'Decisões 100% rastreáveis — zero falhas silenciosas',
    ],
    // ⚠️ LEGAL — P0: CVM IN 621 / LGPD / PROCON
    // Uni IA não é corretora, não é CTVM, não é assessora de investimentos credenciada.
    // A atividade de envio de sinais analíticos sem recomendação individualizada
    // é permitida desde que o disclaimer seja claro, visível e permanente.
    legalBadge:
      '⚠️ Uni IA não é corretora, CTVM nem assessora de investimentos credenciada perante a CVM. Os sinais são inteligência analítica — não constituem recomendação de investimento. Sinais do plano gratuito possuem atraso de 15 minutos. Resultados passados não garantem desempenho futuro. Toda operação envolve risco de perda parcial ou total do capital.',
  },

  ar: {
    heroTitle: 'Uni IA — الهيكل أولاً. الربح يأتي بعده.',
    heroSubtitle:
      'بنية مؤسسية للمخاطر والانضباط والتنفيذ. ثمانية وكلاء متخصصون يصلون إلى توافق قبل إصدار أي إشارة.',
    heroStatement: 'ابن الحوكمة قبل ملاحقة العائدات.',
    heroAnchor: '8 وكلاء · حوكمة 4 طبقات · قرارات قابلة للتدقيق بنسبة 100٪',
    primaryCta: 'ابدأ الوصول المميز',
    secondaryCta: 'انضم إلى تليجرام المجاني',
    authorityTitle: 'طبقة السيطرة المؤسسية',
    authorityItems: [
      'اختبار رجعي حتمي',
      'مرشح مخاطر إلزامي (SENTINEL)',
      'بوابات حوكمة قابلة للقياس',
      'رأس مال محمي بموجب التفويض',
    ],
    feature1Title: 'وكيل حماية الصفقات',
    feature1Body:
      'عند انعكاس الهيكل بعد الدخول يصلك تنبيه إغلاق مبكر قبل السوق العام. الانضباط مُطبَّق بالكود وليس بالإرادة.',
    feature2Title: 'تحقق متعدد الأطر الزمنية',
    feature2Body:
      'لا يُرسَل أي إشارة سريعة إلا بعد توافق الاتجاه الأسبوعي واليومي، مما يُزيل الإعدادات منخفضة الاحتمالية من المنبع.',
    feature3Title: 'محرك المعنويات والتقلب',
    feature3Body:
      'يُدمج الأخبار ومعنويات السوق وضغط التقلب لتحديد ومنع قرارات الدخول العاطفية قبل أن تتحول إلى خسائر.',
    edgeTitle: 'لماذا ينتقل العملاء المدفوعون إلى Uni IA',
    edgeBody:
      'مقارنة بالقنوات العامة ونسخ التداول والتنبيهات الثابتة، يقدم Uni IA سياق مخاطر ودرجة ثقة واضحة مدعومة بمسار تدقيق كامل.',
    socialProofLabel: 'الحوكمة بالأرقام',
    socialProofItems: [
      '8 وكلاء متخصصون يصوتون لكل إشارة',
      'بوابة حوكمة من 4 طبقات قبل أي إرسال',
      'قرارات قابلة للتتبع بنسبة 100٪ — لا أعطال صامتة',
    ],
    legalBadge:
      '⚠️ Uni IA ليست وسيطاً مرخصاً أو مستشاراً للاستثمار. الإشارات هي ذكاء تحليلي فقط. إشارات الخطة المجانية متأخرة 15 دقيقة. النتائج الماضية لا تضمن الأداء المستقبلي. جميع عمليات التداول تنطوي على مخاطر الخسارة.',
  },

  zh: {
    heroTitle: 'Uni IA — 结构先行。利润随之而来。',
    heroSubtitle:
      '面向风险、纪律与执行的机构化架构。八名专业代理在任何信号发布前达成共识。',
    heroStatement: '先建立治理，再追求收益。',
    heroAnchor: '8 个代理 · 4 层治理 · 100% 可审计决策',
    primaryCta: '开始高级访问',
    secondaryCta: '加入免费 Telegram',
    authorityTitle: '机构控制层',
    authorityItems: [
      '确定性回测',
      '强制风险过滤器（SENTINEL）',
      '可量化治理门控',
      '按任务保护资本',
    ],
    feature1Title: '仓位守护代理',
    feature1Body:
      '入场后结构反转时，系统会先于市场人群发出平仓预警。纪律由代码执行，而非意志力。',
    feature2Title: '多周期一致性验证',
    feature2Body:
      '只有周线与日线方向一致，才会释放短线信号，从源头消除低概率交易机会。',
    feature3Title: '情绪与波动引擎',
    feature3Body:
      '融合新闻情绪与波动压力，在情绪化入场变成亏损之前识别并抑制它。',
    edgeTitle: '为什么付费客户选择 Uni IA',
    edgeBody:
      '相比普通喊单群、跟单房和静态图表提醒，Uni IA 提供风险语境与可解释评分，并附带完整审计记录。',
    socialProofLabel: '治理数字',
    socialProofItems: [
      '每个信号由 8 名专业代理投票',
      '任何发出前经过 4 层治理门控',
      '决策 100% 可追溯 — 零静默故障',
    ],
    legalBadge:
      '⚠️ Uni IA 不是持牌经纪商或投资顾问。信号仅为分析性智能，不构成投资建议。免费计划信号延迟 15 分钟。过往业绩不代表未来表现。所有交易均存在亏损风险。',
  },
};

// ─────────────────────────────────────────────────────────────────────────────
// RISK COPY
// ─────────────────────────────────────────────────────────────────────────────
export const riskCopy: Record<Locale, {
  title: string;
  body: string;
  freeDelay: string;
  jurisdiction: string;  // novo — LGPD / foro de eleição
}> = {
  en: {
    title: 'Risk Disclosure',
    body: 'This platform does not provide investment advice and does not guarantee profit. All market operations involve risk of partial or total capital loss.',
    freeDelay: '⚠️ Free signals are delayed by 15 minutes. Premium is a paid service with real-time delivery.',
    jurisdiction: 'This service operates under Brazilian law (LGPD, CVM regulations). Jurisdiction: São Paulo, Brazil.',
  },
  es: {
    title: 'Divulgación de Riesgo',
    body: 'Esta plataforma no ofrece asesoría de inversión ni garantiza beneficio. Toda operación implica riesgo de pérdida parcial o total del capital.',
    freeDelay: '⚠️ Las señales gratuitas tienen 15 minutos de retraso. Premium es un servicio de pago con entrega en tiempo real.',
    jurisdiction: 'Este servicio opera bajo la legislación brasileña (LGPD, regulaciones CVM). Jurisdicción: São Paulo, Brasil.',
  },
  pt: {
    title: 'Aviso de Risco',
    body: 'Esta plataforma não presta recomendação de investimento e não garante lucro. Toda operação de mercado envolve risco de perda parcial ou total do capital investido.',
    freeDelay: '⚠️ Os sinais do plano gratuito possuem atraso de 15 minutos. O plano Premium é pago e entrega em tempo real.',
    // LGPD Art. 41 — DPO / foro de eleição obrigatório para atividade comercial
    jurisdiction: 'Serviço operado sob legislação brasileira (LGPD, regulamentações CVM). Foro de eleição: Comarca de São Paulo/SP.',
  },
  ar: {
    title: 'إفصاح المخاطر',
    body: 'هذه المنصة لا تقدم نصيحة استثمار ولا تضمن الربح. كل عملية في السوق تنطوي على مخاطر خسارة جزئية أو كاملة لرأس المال.',
    freeDelay: '⚠️ إشارات الخطة المجانية متأخرة 15 دقيقة. الخطة المميزة مدفوعة وتقدم تنبيهات فورية.',
    jurisdiction: 'تعمل هذه الخدمة وفق القانون البرازيلي (LGPD، لوائح CVM). الاختصاص القضائي: ساو باولو، البرازيل.',
  },
  zh: {
    title: '风险披露',
    body: '本平台不提供投资建议，且不保证盈利。所有市场操作均存在部分或全部资本损失的风险。',
    freeDelay: '⚠️ 免费计划信号延迟 15 分钟。高级版为付费服务，提供实时推送。',
    jurisdiction: '本服务依据巴西法律（LGPD、CVM 法规）运营。管辖法院：巴西圣保罗。',
  },
};

// ─────────────────────────────────────────────────────────────────────────────
// TERMS COPY — adicionado cláusula de jurisdição e DPO (LGPD Art. 41)
// ─────────────────────────────────────────────────────────────────────────────
export const termsCopy: Record<Locale, {
  title: string;
  intro: string;
  s1Title: string; s1Body: string;
  s2Title: string; s2Body: string;
  s3Title: string; s3Body: string;
  s4Title: string; s4Body: string;
  s5Title: string; s5Body: string;
  s6Title: string; s6Body: string;  // novo — Jurisdição e Foro
  s7Title: string; s7Body: string;  // novo — DPO / LGPD
}> = {
  en: {
    title: 'Terms of Use — UNI IA',
    intro: 'These terms define legal boundaries, risk disclosure and platform usage conditions for paid and free users. Uni IA is not a licensed broker, dealer or investment adviser.',
    s1Title: '1. Acceptance of Terms',
    s1Body: 'By using Uni IA services, you agree to these terms. The platform provides analytical intelligence only and does not constitute direct investment advice or a regulated financial service.',
    s2Title: '2. Risk Disclaimer',
    s2Body: 'Financial markets involve high risk. Uni IA is not liable for capital losses, execution failures or broker-side disruptions. Free plan signals are delayed by 15 minutes — this delay is material and must be considered before any trading decision.',
    s3Title: '3. Compliance and Fraud Control',
    s3Body: 'We may audit suspicious accounts and suspend access in case of abuse, fraud patterns or violation of applicable legal regulations, including CVM instructions and LGPD.',
    s4Title: '4. Algorithmic Transparency',
    s4Body: 'Our models combine LLM reasoning and quantitative indicators. No model guarantees 100% accuracy. Continuous audits are performed for stability, quality and regulatory compliance.',
    s5Title: '5. No Profit Guarantee',
    s5Body: 'No signal, scenario, performance chart or score guarantees profits. Every operation involves risk and may result in partial or total loss. Past results are not indicative of future performance.',
    s6Title: '6. Jurisdiction and Governing Law',
    s6Body: 'These terms are governed by the laws of the Federative Republic of Brazil. Any disputes shall be submitted to the exclusive jurisdiction of the courts of the city of São Paulo, State of São Paulo, Brazil, waiving any other forum, however privileged.',
    s7Title: '7. Data Protection (LGPD)',
    s7Body: 'Uni IA processes personal data in accordance with the Brazilian General Data Protection Law (Lei 13.709/2018 — LGPD). Data subjects may exercise their rights (access, correction, deletion, portability) by contacting our Data Protection Officer (DPO) via the official support channel.',
  },
  es: {
    title: 'Términos de Uso — UNI IA',
    intro: 'Estos términos definen los límites legales, divulgación de riesgo y condiciones de uso. Uni IA no es un corredor ni asesor de inversiones autorizado.',
    s1Title: '1. Aceptación de Términos',
    s1Body: 'Al usar Uni IA, aceptas estos términos. La plataforma ofrece inteligencia analítica únicamente y no constituye asesoría de inversión directa ni servicio financiero regulado.',
    s2Title: '2. Aviso de Riesgo',
    s2Body: 'Los mercados financieros implican alto riesgo. Las señales del plan gratuito tienen 15 minutos de retraso — este retraso es relevante y debe considerarse antes de cualquier decisión de trading.',
    s3Title: '3. Cumplimiento y Control de Fraude',
    s3Body: 'Podemos auditar cuentas sospechosas y suspender acceso ante abuso, fraude o incumplimiento de regulaciones aplicables, incluyendo LGPD y normativa CVM.',
    s4Title: '4. Transparencia Algorítmica',
    s4Body: 'Nuestros modelos combinan LLM e indicadores cuantitativos. Ningún modelo garantiza 100% de acierto. Se realizan auditorías continuas de estabilidad, calidad y cumplimiento regulatorio.',
    s5Title: '5. Sin Garantía de Beneficio',
    s5Body: 'Ninguna señal, escenario o resultado histórico garantiza ganancias. Los resultados pasados no son indicativos del rendimiento futuro.',
    s6Title: '6. Jurisdicción y Ley Aplicable',
    s6Body: 'Estos términos se rigen por las leyes de la República Federativa de Brasil. Cualquier disputa se someterá a la jurisdicción exclusiva de los tribunales de la ciudad de São Paulo, Brasil.',
    s7Title: '7. Protección de Datos (LGPD)',
    s7Body: 'Uni IA trata datos personales conforme a la Ley General de Protección de Datos Personales de Brasil (LGPD — Lei 13.709/2018). Los titulares pueden ejercer sus derechos contactando a nuestro Oficial de Protección de Datos (DPO).',
  },
  pt: {
    title: 'Termos de Uso — UNI IA',
    intro: 'Estes termos definem limites legais, divulgação de risco e condições de uso. A Uni IA não é corretora, CTVM nem assessora de investimentos credenciada perante a CVM.',
    s1Title: '1. Aceitação dos Termos',
    s1Body: 'Ao utilizar o Uni IA, você concorda com estes termos. A plataforma fornece inteligência analítica e não constitui recomendação direta de investimento nem serviço financeiro regulado pela CVM.',
    s2Title: '2. Aviso de Risco',
    s2Body: 'Mercado financeiro envolve alto risco. O Uni IA não se responsabiliza por perdas de capital, falhas de execução ou indisponibilidade de corretoras. Os sinais do plano gratuito possuem atraso de 15 minutos — este atraso é relevante e deve ser considerado antes de qualquer decisão operacional.',
    s3Title: '3. Compliance e Controle de Fraude',
    s3Body: 'Podemos auditar contas suspeitas e suspender acessos em casos de abuso, fraude ou violação da legislação aplicável, incluindo LGPD e instruções normativas da CVM.',
    s4Title: '4. Transparência Algorítmica',
    s4Body: 'Nossos modelos combinam LLM e indicadores quantitativos. Nenhum modelo garante 100% de acerto. Auditorias contínuas de estabilidade, qualidade e conformidade regulatória são realizadas.',
    s5Title: '5. Sem Garantia de Lucro',
    s5Body: 'Nenhum sinal, cenário, gráfico de performance ou score garante lucro. Toda operação envolve risco e pode resultar em perda parcial ou total do capital. Resultados passados não são indicativos de desempenho futuro.',
    // CRITICAL — foro de eleição obrigatório para contratos de adesão (CC Art. 112 / CPC Art. 63)
    s6Title: '6. Jurisdição e Foro de Eleição',
    s6Body: 'Estes termos são regidos pelas leis da República Federativa do Brasil. Fica eleito o foro da comarca de São Paulo/SP para dirimir quaisquer controvérsias decorrentes deste instrumento, com renúncia expressa a qualquer outro, por mais privilegiado que seja.',
    // LGPD Art. 41 — indicação do DPO é obrigatória para controladores que operam em escala comercial
    s7Title: '7. Proteção de Dados Pessoais (LGPD)',
    s7Body: 'A Uni IA trata dados pessoais em conformidade com a Lei Geral de Proteção de Dados Pessoais (Lei nº 13.709/2018 — LGPD). Os titulares podem exercer os direitos previstos no Art. 18 (acesso, correção, exclusão, portabilidade e revogação de consentimento) mediante solicitação ao Encarregado de Dados (DPO) pelo canal de suporte oficial da plataforma.',
  },
  ar: {
    title: 'شروط الاستخدام — UNI IA',
    intro: 'تحدد هذه الشروط الحدود القانونية وإفصاح المخاطر وشروط استخدام المنصة. Uni IA ليست وسيطاً مرخصاً أو مستشاراً للاستثمار.',
    s1Title: '1. قبول الشروط',
    s1Body: 'باستخدام خدمات Uni IA فأنت توافق على هذه الشروط. المنصة تقدم تحليلات فقط ولا تشكل نصيحة استثمار مباشرة أو خدمة مالية منظمة.',
    s2Title: '2. إخلاء مسؤولية المخاطر',
    s2Body: 'الأسواق المالية عالية المخاطر. إشارات الخطة المجانية متأخرة 15 دقيقة — هذا التأخير جوهري ويجب مراعاته قبل أي قرار تداول.',
    s3Title: '3. الامتثال ومكافحة الاحتيال',
    s3Body: 'قد نقوم بتدقيق الحسابات المشتبه بها وتعليق الوصول عند إساءة الاستخدام أو الاحتيال أو مخالفة الأنظمة المعمول بها بما في ذلك LGPD ولوائح CVM.',
    s4Title: '4. الشفافية الخوارزمية',
    s4Body: 'نماذجنا تجمع بين LLM ومؤشرات كمية. لا يوجد نموذج يضمن دقة كاملة. نقوم بتدقيقات مستمرة للجودة والامتثال التنظيمي.',
    s5Title: '5. لا يوجد ضمان للربح',
    s5Body: 'لا توجد إشارة أو نتيجة تاريخية تضمن الربحية. النتائج الماضية لا تدل على الأداء المستقبلي.',
    s6Title: '6. الاختصاص القضائي والقانون الحاكم',
    s6Body: 'تخضع هذه الشروط لقوانين جمهورية البرازيل الاتحادية. تُحال أي نزاعات إلى الاختصاص القضائي الحصري لمحاكم مدينة ساو باولو، البرازيل.',
    s7Title: '7. حماية البيانات (LGPD)',
    s7Body: 'تعالج Uni IA البيانات الشخصية وفقاً للقانون البرازيلي العام لحماية البيانات (LGPD — Lei 13.709/2018). يمكن لأصحاب البيانات ممارسة حقوقهم بالتواصل مع مسؤول حماية البيانات (DPO) عبر قناة الدعم الرسمية.',
  },
  zh: {
    title: '使用条款 — UNI IA',
    intro: '本条款说明平台的法律边界、风险披露与使用条件。Uni IA 不是持牌经纪商或投资顾问。',
    s1Title: '1. 条款接受',
    s1Body: '使用 Uni IA 即表示你同意本条款。平台仅提供分析性智能，不构成直接投资建议或受监管金融服务。',
    s2Title: '2. 风险声明',
    s2Body: '金融市场具有高风险。免费计划信号延迟 15 分钟——此延迟具有重要意义，在做出任何交易决策前必须予以考虑。',
    s3Title: '3. 合规与反欺诈',
    s3Body: '如发现滥用、欺诈或违反适用法律法规（包括 LGPD 和 CVM 规定）的行为，我们可审计相关账户并暂停访问。',
    s4Title: '4. 算法透明性',
    s4Body: '模型结合 LLM 与量化指标。不存在 100% 准确率。我们持续进行稳定性、质量与合规审计。',
    s5Title: '5. 不保证盈利',
    s5Body: '任何信号或历史表现都不保证未来收益。过往业绩不代表未来表现。',
    s6Title: '6. 司法管辖与适用法律',
    s6Body: '本条款受巴西联邦共和国法律管辖。任何争议均提交巴西圣保罗市法院专属管辖。',
    s7Title: '7. 数据保护（LGPD）',
    s7Body: 'Uni IA 依据巴西《通用数据保护法》（LGPD — Lei 13.709/2018）处理个人数据。数据主体可通过官方支持渠道联系数据保护官（DPO）行使相关权利。',
  },
};

// ─────────────────────────────────────────────────────────────────────────────
// PRIVACY COPY — adicionado DPO e direitos LGPD Art. 18
// ─────────────────────────────────────────────────────────────────────────────
export const privacyCopy: Record<Locale, {
  title: string;
  intro: string;
  p1: string;
  p2: string;
  p3: string;
  p4: string;
  p5: string;  // novo — DPO / LGPD Art. 41
}> = {
  en: {
    title: 'Privacy Policy',
    intro: 'This policy explains how we collect, process and protect user data across Free and Premium plans, in compliance with the Brazilian General Data Protection Law (LGPD).',
    p1: 'We collect account, subscription and interaction data needed to deliver alerts and billing operations. No data is collected beyond what is strictly necessary for the service.',
    p2: 'We do not sell personal data. Data is shared only with required infrastructure providers (payment, messaging, hosting), all subject to equivalent data protection obligations.',
    p3: 'You may request access, correction, deletion, portability or revocation of consent for your data at any time, subject to legal and compliance obligations under LGPD Art. 18.',
    p4: 'By using the platform, you agree to this policy and to periodic updates required by applicable legal frameworks.',
    p5: 'Data Protection Officer (DPO): Requests related to personal data rights must be directed to our DPO via the official support channel. We commit to responding within the legal timeframe established by LGPD.',
  },
  es: {
    title: 'Política de Privacidad',
    intro: 'Esta política explica cómo recopilamos, procesamos y protegemos datos en conformidad con la Ley General de Protección de Datos de Brasil (LGPD).',
    p1: 'Recopilamos datos de cuenta, suscripción e interacción para entregar alertas y facturación. No recopilamos más datos de los estrictamente necesarios.',
    p2: 'No vendemos datos personales. Solo compartimos con proveedores de infraestructura necesarios, sujetos a obligaciones equivalentes de protección.',
    p3: 'Puedes solicitar acceso, corrección, eliminación, portabilidad o revocación del consentimiento en cualquier momento conforme al Art. 18 de la LGPD.',
    p4: 'Al usar la plataforma aceptas esta política y sus actualizaciones legales.',
    p5: 'Oficial de Protección de Datos (DPO): Las solicitudes sobre derechos de datos deben dirigirse a nuestro DPO mediante el canal de soporte oficial.',
  },
  pt: {
    title: 'Política de Privacidade',
    intro: 'Esta política explica como coletamos, processamos e protegemos dados nos planos Free e Premium, em conformidade com a Lei Geral de Proteção de Dados Pessoais (LGPD — Lei nº 13.709/2018).',
    p1: 'Coletamos dados de conta, assinatura e interação estritamente necessários para entregar alertas e operações de cobrança. Não coletamos dados além do mínimo necessário (princípio da necessidade, LGPD Art. 6º, III).',
    p2: 'Não vendemos dados pessoais. O compartilhamento ocorre apenas com provedores essenciais de infraestrutura (pagamento, mensageria, hospedagem), todos submetidos a obrigações equivalentes de proteção.',
    p3: 'Você pode exercer os direitos do Art. 18 da LGPD (acesso, correção, exclusão, portabilidade e revogação de consentimento) a qualquer momento, respeitadas as obrigações legais e regulatórias.',
    p4: 'Ao usar a plataforma, você concorda com esta política e com as atualizações exigidas por lei.',
    // LGPD Art. 41 — DPO obrigatório para controladores em escala comercial
    p5: 'Encarregado de Dados (DPO): Solicitações relativas a direitos sobre dados pessoais devem ser encaminhadas ao nosso DPO pelo canal de suporte oficial. Comprometemo-nos a responder dentro do prazo legal estabelecido pela LGPD.',
  },
  ar: {
    title: 'سياسة الخصوصية',
    intro: 'توضح هذه السياسة كيف نجمع البيانات ونعالجها ونحميها وفقاً للقانون البرازيلي العام لحماية البيانات (LGPD).',
    p1: 'نجمع فقط البيانات الضرورية للحساب والاشتراك والتفاعل لتقديم التنبيهات وعمليات الفوترة.',
    p2: 'لا نبيع البيانات الشخصية. تتم المشاركة فقط مع مزودي البنية التحتية الضروريين الخاضعين لالتزامات حماية مكافئة.',
    p3: 'يمكنك طلب الوصول أو التصحيح أو الحذف أو النقل أو إلغاء الموافقة وفقاً للمادة 18 من LGPD.',
    p4: 'باستخدام المنصة فأنت توافق على هذه السياسة وتحديثاتها القانونية.',
    p5: 'مسؤول حماية البيانات (DPO): يجب توجيه طلبات حقوق البيانات الشخصية إلى DPO عبر قناة الدعم الرسمية.',
  },
  zh: {
    title: '隐私政策',
    intro: '本政策说明我们如何依据巴西《通用数据保护法》（LGPD）在免费与高级计划中收集、处理和保护数据。',
    p1: '我们仅收集提供告警与计费所必需的账户、订阅与交互数据，遵循数据最小化原则。',
    p2: '我们不出售个人数据。仅与必要的基础设施服务商共享，且这些服务商承担同等数据保护义务。',
    p3: '你可随时依据 LGPD 第 18 条申请访问、更正、删除、可携性或撤回同意，但需遵守法律义务。',
    p4: '使用本平台即表示你同意本政策及其依法更新。',
    p5: '数据保护官（DPO）：个人数据权利请求须通过官方支持渠道提交给我们的 DPO，我们承诺在 LGPD 规定的法定期限内答复。',
  },
};

// ─────────────────────────────────────────────────────────────────────────────
// DISCLOSURE COPY (sem alteração estrutural — mantido compatível)
// ─────────────────────────────────────────────────────────────────────────────
export const disclosureCopy: Record<Locale, {
  title: string;
  intro: string;
  d1: string;
  d2: string;
  d3: string;
}> = {
  en: {
    title: 'Risk Disclosure',
    intro: 'Trading and investment operations involve substantial risk and are not suitable for every profile. Uni IA is not a licensed broker or investment adviser.',
    d1: 'No signal, alert or historical result guarantees future profitability.',
    d2: 'You are solely responsible for your execution decisions, position sizing and risk exposure.',
    d3: '⚠️ Free plan signals are delayed 15 minutes. Premium is a paid service with real-time delivery.',
  },
  es: {
    title: 'Divulgación de Riesgo',
    intro: 'Las operaciones de trading e inversión implican riesgo significativo y no son adecuadas para todos los perfiles.',
    d1: 'Ninguna señal o resultado histórico garantiza rentabilidad futura.',
    d2: 'Eres responsable de tus decisiones de ejecución y gestión de riesgo.',
    d3: '⚠️ Las señales gratuitas tienen 15 minutos de retraso. Premium es un servicio de pago en tiempo real.',
  },
  pt: {
    title: 'Disclosure de Risco',
    intro: 'Operações de trading e investimento envolvem risco relevante e não servem para todos os perfis. A Uni IA não é corretora, CTVM nem assessora de investimentos credenciada.',
    d1: 'Nenhum sinal, alerta ou resultado histórico garante rentabilidade futura.',
    d2: 'A decisão de execução, tamanho de posição e exposição de risco é de responsabilidade exclusiva do usuário.',
    d3: '⚠️ Sinais do plano gratuito possuem atraso de 15 minutos. O plano Premium é pago e entregue em tempo real.',
  },
  ar: {
    title: 'إفصاح المخاطر',
    intro: 'عمليات التداول والاستثمار تنطوي على مخاطر كبيرة وقد لا تناسب الجميع. Uni IA ليست وسيطاً مرخصاً.',
    d1: 'لا توجد إشارة أو نتيجة تاريخية تضمن الربحية المستقبلية.',
    d2: 'أنت المسؤول بالكامل عن قرارات التنفيذ وإدارة المخاطر.',
    d3: '⚠️ إشارات الخطة المجانية متأخرة 15 دقيقة. الخطة المميزة مدفوعة وفورية.',
  },
  zh: {
    title: '风险披露',
    intro: '交易与投资具有较高风险，并不适合所有人。Uni IA 不是持牌经纪商或投资顾问。',
    d1: '任何信号、警报或历史表现都不保证未来收益。',
    d2: '执行决策、仓位大小与风险暴露由用户自行负责。',
    d3: '⚠️ 免费计划信号延迟 15 分钟。高级版为付费实时推送服务。',
  },
};
