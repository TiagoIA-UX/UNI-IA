export const SUPPORTED_LOCALES = ['en', 'es', 'pt', 'ar', 'zh'] as const;
export type Locale = (typeof SUPPORTED_LOCALES)[number];

export function resolveLocale(lang?: string): Locale {
  if (!lang) return 'en';
  const normalized = lang.toLowerCase();
  return (SUPPORTED_LOCALES as readonly string[]).includes(normalized) ? (normalized as Locale) : 'en';
}

export const localeLabels: Record<Locale, string> = {
  en: 'English',
  es: 'Espanol',
  pt: 'Portugues',
  ar: 'Arabic',
  zh: 'Chinese',
};

export const homeCopy: Record<Locale, {
  heroTitle: string;
  heroSubtitle: string;
  primaryCta: string;
  secondaryCta: string;
  feature1Title: string;
  feature1Body: string;
  feature2Title: string;
  feature2Body: string;
  feature3Title: string;
  feature3Body: string;
  edgeTitle: string;
  edgeBody: string;
}> = {
  en: {
    heroTitle: 'Institutional-Grade AI Signals for FX, Macro and Indexes',
    heroSubtitle: 'Uni IA orchestrates 7 specialized agents to deliver explainable entries and exits in real time. Built for paid subscribers, desks and high-performance operators.',
    primaryCta: 'Start Premium Access',
    secondaryCta: 'Join Free Telegram',
    feature1Title: 'Position Guardian Agent',
    feature1Body: 'When market structure flips after entry, your risk desk receives a close-position alert before the crowd reacts.',
    feature2Title: 'Multi-Timeframe Validation',
    feature2Body: 'Scalping signals are only released when weekly and daily structure agree with intraday momentum.',
    feature3Title: 'Sentiment and Volatility Engine',
    feature3Body: 'News and sentiment signals are fused with volatility pressure to avoid emotional entries.',
    edgeTitle: 'Why Paying Clients Switch to Uni IA',
    edgeBody: 'Compared to generic signal channels, copy-trading rooms and static chart alerts, Uni IA delivers explainable alerts, risk context and execution-ready confidence scores.',
  },
  es: {
    heroTitle: 'Senales de IA de nivel institucional para FX, macro e indices',
    heroSubtitle: 'Uni IA orquesta 7 agentes especializados para entregar entradas y salidas explicables en tiempo real.',
    primaryCta: 'Comenzar acceso premium',
    secondaryCta: 'Entrar al Telegram gratis',
    feature1Title: 'Agente guardian de posicion',
    feature1Body: 'Si la estructura del mercado cambia tras la entrada, recibes alerta de cierre antes que la mayoria.',
    feature2Title: 'Validacion multi-timeframe',
    feature2Body: 'Las senales solo se liberan cuando semanal y diario confirman el impulso intradia.',
    feature3Title: 'Motor de sentimiento y volatilidad',
    feature3Body: 'Fusiona noticias, sentimiento y presion de volatilidad para evitar entradas emocionales.',
    edgeTitle: 'Por que los clientes de pago eligen Uni IA',
    edgeBody: 'Frente a canales genericos, copy-trading y alertas estaticas, Uni IA entrega contexto de riesgo y score explicable.',
  },
  pt: {
    heroTitle: 'Sinais de IA Institucional para Forex, Macro e Indices',
    heroSubtitle: 'O Uni IA orquestra 7 agentes especializados para entregar entradas e saidas explicaveis em tempo real.',
    primaryCta: 'Iniciar Acesso Premium',
    secondaryCta: 'Entrar no Telegram Gratis',
    feature1Title: 'Agente Guardiao de Posicao',
    feature1Body: 'Quando a estrutura vira apos sua entrada, voce recebe alerta de fechamento antes do mercado em massa.',
    feature2Title: 'Validacao Multi-Timeframe',
    feature2Body: 'Sinais de curto prazo so saem quando semanal e diario confirmam o mesmo lado.',
    feature3Title: 'Motor de Sentimento e Volatilidade',
    feature3Body: 'Noticias, sentimento e pressao de volatilidade sao combinados para evitar entradas emocionais.',
    edgeTitle: 'Por que clientes pagantes migram para o Uni IA',
    edgeBody: 'Contra grupos genericos, copy-trading e alertas estaticos, o Uni IA entrega contexto de risco e score explicavel.',
  },
  ar: {
    heroTitle: 'اشارات ذكاء اصطناعي بمستوى مؤسسي للفوركس والماكرو والمؤشرات',
    heroSubtitle: 'Uni IA يدير 7 وكلاء متخصصين لتقديم دخول وخروج واضح في الوقت الحقيقي.',
    primaryCta: 'ابدأ الوصول المميز',
    secondaryCta: 'انضم الى تليجرام المجاني',
    feature1Title: 'وكيل حماية الصفقات',
    feature1Body: 'عند انعكاس الهيكل بعد الدخول يصلك تنبيه اغلاق مبكر قبل السوق العام.',
    feature2Title: 'تحقق متعدد الاطارات الزمنية',
    feature2Body: 'لا يتم ارسال اشارة سريعة الا بعد توافق الاتجاه الاسبوعي واليومي.',
    feature3Title: 'محرك المعنويات والتقلب',
    feature3Body: 'يتم دمج الاخبار ومعنويات السوق والتقلب لتقليل القرارات العاطفية.',
    edgeTitle: 'لماذا ينتقل العملاء المدفوعون الى Uni IA',
    edgeBody: 'مقارنة بالقنوات العامة ونسخ التداول والتنبيهات الثابتة، يقدم Uni IA سياق مخاطر ودرجة ثقة واضحة.',
  },
  zh: {
    heroTitle: '面向外汇 宏观与指数的机构级AI信号',
    heroSubtitle: 'Uni IA 协同7个专业代理 实时提供可解释的入场与离场信号。',
    primaryCta: '开始高级访问',
    secondaryCta: '加入免费Telegram',
    feature1Title: '仓位守护代理',
    feature1Body: '入场后结构反转时 系统会先于市场人群发出平仓预警。',
    feature2Title: '多周期一致性验证',
    feature2Body: '只有周线与日线方向一致 才会释放短线信号。',
    feature3Title: '情绪与波动引擎',
    feature3Body: '融合新闻情绪与波动压力 避免情绪化入场。',
    edgeTitle: '为什么付费客户选择 Uni IA',
    edgeBody: '相比普通喊单群 跟单房和静态图表提醒 Uni IA 提供风险语境与可解释评分。',
  },
};

export const termsCopy: Record<Locale, {
  title: string;
  intro: string;
  s1Title: string;
  s1Body: string;
  s2Title: string;
  s2Body: string;
  s3Title: string;
  s3Body: string;
  s4Title: string;
  s4Body: string;
  s5Title: string;
  s5Body: string;
}> = {
  en: {
    title: 'Terms of Use - Uni IA (Zairyx)',
    intro: 'These terms define legal boundaries, risk disclosure and platform usage conditions for paid and free users.',
    s1Title: '1. Acceptance of Terms',
    s1Body: 'By using Uni IA services, you agree to these terms. The platform provides analytical intelligence and does not constitute direct investment advice.',
    s2Title: '2. Risk Disclaimer',
    s2Body: 'Financial markets involve high risk. Uni IA is not liable for capital losses, execution failures or broker-side disruptions.',
    s3Title: '3. Compliance and Fraud Control',
    s3Body: 'We may audit suspicious accounts and suspend access in case of abuse, fraud patterns or violation of legal regulations.',
    s4Title: '4. Algorithmic Transparency',
    s4Body: 'Our models combine LLM reasoning and quantitative indicators. No model guarantees 100% accuracy. Continuous audits are performed for stability and quality.',
    s5Title: '5. No Profit Guarantee',
    s5Body: 'No signal, scenario, performance chart or score guarantees profits. Every operation involves risk and may result in partial or total loss.',
  },
  es: {
    title: 'Terminos de Uso - Uni IA (Zairyx)',
    intro: 'Estos terminos definen los limites legales, divulgacion de riesgo y condiciones de uso para clientes gratuitos y de pago.',
    s1Title: '1. Aceptacion de Terminos',
    s1Body: 'Al usar Uni IA, aceptas estos terminos. La plataforma ofrece inteligencia analitica y no constituye asesoria de inversion directa.',
    s2Title: '2. Aviso de Riesgo',
    s2Body: 'Los mercados financieros implican alto riesgo. Uni IA no responde por perdidas de capital, fallos de ejecucion o problemas del broker.',
    s3Title: '3. Cumplimiento y Control de Fraude',
    s3Body: 'Podemos auditar cuentas sospechosas y suspender acceso ante abuso, fraude o incumplimiento regulatorio.',
    s4Title: '4. Transparencia Algoritmica',
    s4Body: 'Nuestros modelos combinan LLM e indicadores cuantitativos. Ningun modelo garantiza 100% de acierto. Se realizan auditorias continuas.',
    s5Title: '5. Sin Garantia de Beneficio',
    s5Body: 'Ninguna senal, escenario, grafico de rendimiento o score garantiza ganancias. Toda operacion implica riesgo y puede generar perdida parcial o total.',
  },
  pt: {
    title: 'Termos de Uso - Uni IA (Zairyx)',
    intro: 'Estes termos definem limites legais, divulgacao de risco e condicoes de uso para clientes gratuitos e pagantes.',
    s1Title: '1. Aceitacao dos Termos',
    s1Body: 'Ao utilizar o Uni IA, voce concorda com estes termos. A plataforma fornece inteligencia analitica e nao constitui recomendacao direta de investimento.',
    s2Title: '2. Aviso de Risco',
    s2Body: 'Mercado financeiro envolve alto risco. O Uni IA nao se responsabiliza por perdas de capital, falhas de execucao ou indisponibilidade de corretoras.',
    s3Title: '3. Compliance e Controle de Fraude',
    s3Body: 'Podemos auditar contas suspeitas e suspender acessos em casos de abuso, fraude ou violacao regulatoria.',
    s4Title: '4. Transparencia Algoritmica',
    s4Body: 'Nossos modelos combinam LLM e indicadores quantitativos. Nenhum modelo garante 100% de acerto. Auditorias continuas sao realizadas.',
    s5Title: '5. Sem Garantia de Lucro',
    s5Body: 'Nenhum sinal, cenario, grafico de performance ou score garante lucro. Toda operacao envolve risco e pode resultar em perda parcial ou total.',
  },
  ar: {
    title: 'شروط الاستخدام - Uni IA (Zairyx)',
    intro: 'تحدد هذه الشروط الحدود القانونية وافصاح المخاطر وشروط استخدام المنصة.',
    s1Title: '1. قبول الشروط',
    s1Body: 'باستخدام خدمات Uni IA فانك توافق على هذه الشروط. المنصة تقدم تحليلات ولا تشكل نصيحة استثمار مباشرة.',
    s2Title: '2. اخلاء مسؤولية المخاطر',
    s2Body: 'الاسواق المالية عالية المخاطر. لا تتحمل Uni IA خسائر راس المال او اعطال التنفيذ او مشاكل الوسيط.',
    s3Title: '3. الامتثال ومكافحة الاحتيال',
    s3Body: 'قد نقوم بتدقيق الحسابات المشتبه بها وتعليق الوصول عند اساءة الاستخدام او الاحتيال او مخالفة الانظمة.',
    s4Title: '4. الشفافية الخوارزمية',
    s4Body: 'نماذجنا تجمع بين LLM ومؤشرات كمية. لا يوجد نموذج يضمن دقة كاملة. نقوم بتدقيقات مستمرة للجودة.',
    s5Title: '5. لا يوجد ضمان للربح',
    s5Body: 'لا توجد اشارة او نتيجة تاريخية تضمن الربح. كل عملية تداول تنطوي على مخاطر وقد تؤدي الى خسارة جزئية او كاملة.',
  },
  zh: {
    title: '使用条款 - Uni IA (Zairyx)',
    intro: '本条款说明平台的法律边界 风险披露与使用条件。',
    s1Title: '1. 条款接受',
    s1Body: '使用 Uni IA 即表示你同意本条款。平台提供分析智能 不构成直接投资建议。',
    s2Title: '2. 风险声明',
    s2Body: '金融市场具有高风险。Uni IA 不对资金损失 执行失败或券商侧故障负责。',
    s3Title: '3. 合规与反欺诈',
    s3Body: '如发现滥用 欺诈或违规行为 我们可审计相关账户并暂停访问。',
    s4Title: '4. 算法透明性',
    s4Body: '模型结合 LLM 与量化指标。不存在 100% 准确率。我们持续进行稳定性与质量审计。',
    s5Title: '5. 不保证盈利',
    s5Body: '任何信号 场景或历史表现都不保证盈利。每一笔交易都存在风险 可能导致部分或全部亏损。',
  },
};

export const riskCopy: Record<Locale, { title: string; body: string; freeDelay: string }> = {
  en: {
    title: 'Risk Disclosure',
    body: 'This platform does not provide investment advice and does not guarantee profit. All market operations involve risk.',
    freeDelay: 'Free signals are delayed by 15 minutes. Premium is paid and provides real-time delivery.',
  },
  es: {
    title: 'Divulgacion de Riesgo',
    body: 'Esta plataforma no ofrece asesoria de inversion ni garantiza beneficio. Toda operacion de mercado implica riesgo.',
    freeDelay: 'Las senales free tienen 15 minutos de retraso. Premium es pago y entrega en tiempo real.',
  },
  pt: {
    title: 'Aviso de Risco',
    body: 'Esta plataforma nao presta recomendacao de investimento e nao garante lucro. Toda operacao de mercado envolve risco.',
    freeDelay: 'Os sinais free possuem atraso de 15 minutos. O Premium e pago e entrega em tempo real.',
  },
  ar: {
    title: 'افصاح المخاطر',
    body: 'هذه المنصة لا تقدم نصيحة استثمار ولا تضمن الربح. كل عملية في السوق تنطوي على مخاطر.',
    freeDelay: 'اشارات الخطة المجانية متاخرة 15 دقيقة. الخطة المميزة مدفوعة وتقدم تنبيهات فورية.',
  },
  zh: {
    title: '风险披露',
    body: '本平台不提供投资建议 且不保证盈利。所有市场操作均存在风险。',
    freeDelay: '免费信号延迟15分钟。高级版为付费服务并提供实时推送。',
  },
};

export const privacyCopy: Record<Locale, {
  title: string;
  intro: string;
  p1: string;
  p2: string;
  p3: string;
  p4: string;
}> = {
  en: {
    title: 'Privacy Policy',
    intro: 'This policy explains how we collect, process and protect user data across Free and Premium plans.',
    p1: 'We collect account, subscription and interaction data needed to deliver alerts and billing operations.',
    p2: 'We do not sell personal data. Data is shared only with required infrastructure providers (payment, messaging, hosting).',
    p3: 'You may request access, correction or deletion of your data, subject to legal and compliance obligations.',
    p4: 'By using the platform, you agree to this policy and to periodic updates required by legal frameworks.',
  },
  es: {
    title: 'Politica de Privacidad',
    intro: 'Esta politica explica como recopilamos, procesamos y protegemos datos en planes Free y Premium.',
    p1: 'Recopilamos datos de cuenta, suscripcion e interaccion para entregar alertas y facturacion.',
    p2: 'No vendemos datos personales. Solo compartimos con proveedores necesarios de infraestructura.',
    p3: 'Puedes solicitar acceso, correccion o eliminacion de datos, sujeto a obligaciones legales.',
    p4: 'Al usar la plataforma aceptas esta politica y sus actualizaciones legales.',
  },
  pt: {
    title: 'Politica de Privacidade',
    intro: 'Esta politica explica como coletamos, processamos e protegemos dados nos planos Free e Premium.',
    p1: 'Coletamos dados de conta, assinatura e interacao para entregar alertas e operacoes de cobranca.',
    p2: 'Nao vendemos dados pessoais. O compartilhamento ocorre apenas com provedores essenciais de infraestrutura.',
    p3: 'Voce pode solicitar acesso, correcao ou exclusao de dados, respeitando obrigacoes legais.',
    p4: 'Ao usar a plataforma, voce concorda com esta politica e com atualizacoes exigidas por lei.',
  },
  ar: {
    title: 'سياسة الخصوصية',
    intro: 'توضح هذه السياسة كيف نجمع البيانات ونعالجها ونحميها في الخطط المجانية والمدفوعة.',
    p1: 'نجمع بيانات الحساب والاشتراك والتفاعل لتقديم التنبيهات وعمليات الفوترة.',
    p2: 'لا نبيع البيانات الشخصية. تتم المشاركة فقط مع مزودي البنية التحتية الضروريين.',
    p3: 'يمكنك طلب الوصول او التصحيح او الحذف وفقا للمتطلبات القانونية.',
    p4: 'باستخدام المنصة فانك توافق على هذه السياسة وتحديثاتها القانونية.',
  },
  zh: {
    title: '隐私政策',
    intro: '本政策说明我们如何在免费与高级计划中收集 处理和保护数据。',
    p1: '我们收集账户 订阅与交互数据 用于告警交付与计费。',
    p2: '我们不出售个人数据。仅与必要的基础设施服务商共享。',
    p3: '你可申请访问 更正或删除数据 但需遵守法律义务。',
    p4: '使用本平台即表示你同意本政策及其依法更新。',
  },
};

export const disclosureCopy: Record<Locale, {
  title: string;
  intro: string;
  d1: string;
  d2: string;
  d3: string;
}> = {
  en: {
    title: 'Risk Disclosure',
    intro: 'Trading and investment operations involve substantial risk and are not suitable for every profile.',
    d1: 'No signal, alert or historical result guarantees future profitability.',
    d2: 'You are solely responsible for your execution decisions, position sizing and risk exposure.',
    d3: 'Free plan signals are delayed. Premium is paid and designed for real-time delivery.',
  },
  es: {
    title: 'Divulgacion de Riesgo',
    intro: 'Las operaciones de trading e inversion implican riesgo significativo.',
    d1: 'Ninguna senal o resultado historico garantiza rentabilidad futura.',
    d2: 'Eres responsable de tus decisiones de ejecucion y gestion de riesgo.',
    d3: 'Las senales Free tienen retraso. Premium es pago y en tiempo real.',
  },
  pt: {
    title: 'Disclosure de Risco',
    intro: 'Operacoes de trading e investimento envolvem risco relevante e nao servem para todos os perfis.',
    d1: 'Nenhum sinal, alerta ou resultado historico garante rentabilidade futura.',
    d2: 'A decisao de execucao, tamanho de posicao e exposicao de risco e de responsabilidade exclusiva do usuario.',
    d3: 'Sinais Free possuem atraso. Premium e pago e entregue em tempo real.',
  },
  ar: {
    title: 'افصاح المخاطر',
    intro: 'عمليات التداول والاستثمار تنطوي على مخاطر كبيرة وقد لا تناسب الجميع.',
    d1: 'لا توجد اشارة او نتيجة تاريخية تضمن الربحية المستقبلية.',
    d2: 'انت المسؤول بالكامل عن قرارات التنفيذ وادارة المخاطر.',
    d3: 'اشارات الخطة المجانية متاخرة. الخطة المميزة مدفوعة وفورية.',
  },
  zh: {
    title: '风险披露',
    intro: '交易与投资具有较高风险 并不适合所有人。',
    d1: '任何信号 警报或历史表现都不保证未来收益。',
    d2: '执行决策 仓位大小与风险暴露由用户自行负责。',
    d3: '免费信号存在延迟。高级版为付费实时推送。',
  },
};
