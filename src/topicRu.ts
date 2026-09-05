const TOPIC_RU: Record<string, [string, string]> = {
  "ubiquitous computing": ["Вездесущие вычисления", "ubiquitous computing"],
  "ubicomp": ["Вездесущие вычисления", "ubiquitous computing"],
  "pervasive computing": ["Вездесущие вычисления", "pervasive computing"],
  "accessibility": ["Доступность", "accessibility"],
  "accessible computing": ["Доступные вычисления", "accessible computing"],
  "interaction design": ["Дизайн взаимодействия", "interaction design"],
  "human-centered ai": ["Человеко-ориентированный ИИ", "human-centered AI"],
  "human centered ai": ["Человеко-ориентированный ИИ", "human-centered AI"],
  "human-ai interaction": ["Взаимодействие человека и ИИ", "human-AI interaction"],
  "human–ai interaction": ["Взаимодействие человека и ИИ", "human-AI interaction"],
  "virtual reality": ["Виртуальная реальность", "virtual reality"],
  "augmented reality": ["Дополненная реальность", "augmented reality"],
  "mixed reality": ["Смешанная реальность", "mixed reality"],
  "information visualization": ["Визуализация информации", "information visualization"],
  "data visualization": ["Визуализация данных", "data visualization"],
  "visualization": ["Визуализация", "visualization"],
  "visual analytics": ["Визуальная аналитика", "visual analytics"],
  "computer supported cooperative work": ["Совместная работа", "CSCW"],
  "computer-supported cooperative work": ["Совместная работа", "CSCW"],
  "cscw": ["Совместная работа", "CSCW"],
  "user experience": ["Пользовательский опыт", "user experience"],
  "computer-mediated communication": ["Компьютерно-опосредованная связь", "CMC"],
  "computer mediated communication": ["Компьютерно-опосредованная связь", "CMC"],
  "компьютерно-опосредованная связь": ["Компьютерно-опосредованная связь", "CMC"],
  "recommender systems": ["Рекомендательные системы", "recommender systems"],
  "рекомендательные системы": ["Рекомендательные системы", "recommender systems"],
  "tabletop": ["Настольные поверхности", "tabletop"],
  "настольные поверхности": ["Настольные поверхности", "tabletop"],
  "haptics": ["Осязание", "haptics"],
  "participatory design": ["Совместный дизайн", "participatory design"],
  "information retrieval": ["Информационный поиск", "information retrieval"],
  "design research": ["Исследования дизайна", "design research"],
  "machine learning": ["Машинное обучение", "machine learning"],
  "mobile computing": ["Мобильные вычисления", "mobile computing"],
  "social computing": ["Социальные вычисления", "social computing"],
  "social media": ["Социальные медиа", "social media"],
  "data science": ["Наука о данных", "data science"],
  "human-centered data science": ["Человеко-ориентированная наука о данных", "human-centered data science"],
  "wearable computing": ["Носимые вычисления", "wearable computing"],
  "wearable": ["Носимые устройства", "wearable"],
  "eye tracking": ["Отслеживание взгляда", "eye tracking"],
  "video communication": ["Видеосвязь", "video communication"],
  "telepresence": ["Телеприсутствие", "telepresence"],
  "crowdsourcing": ["Коллективный вклад", "crowdsourcing"],
  "privacy": ["Конфиденциальность", "privacy"],
  "usable privacy and security": ["Удобство конфиденциальности и безопасности", "usable privacy and security"],
  "artificial intelligence": ["Искусственный интеллект", "artificial intelligence"],
  "human computer interaction": ["Человеко-компьютерное взаимодействие", "HCI"],
  "human-computer interaction": ["Человеко-компьютерное взаимодействие", "HCI"],
  "hci": ["Человеко-компьютерное взаимодействие", "HCI"],
  "3d user interfaces": ["Трёхмерные интерфейсы", "3D user interfaces"],
  "intelligent user interfaces": ["Интеллектуальные интерфейсы", "intelligent user interfaces"],
  "online communities": ["Онлайн-сообщества", "online communities"],
  "design theory": ["Теория дизайна", "design theory"],
  "cognitive science": ["Когнитивная наука", "cognitive science"],
  "health informatics": ["Медицинская информатика", "health informatics"],
  "ictd": ["ИКТ для развития", "ICTD"],
  "computer graphics": ["Компьютерная графика", "computer graphics"],
  "видеозвонки": ["Видеозвонки", "video calls"],
  "социальные медиа": ["Социальные медиа", "social media"],
  "отслеживание взгляда": ["Отслеживание взгляда", "eye tracking"],
  "носимые устройства": ["Носимые устройства", "wearable"],
};

function keyOf(raw: string): string {
  return raw.trim().toLowerCase().replace(/[–—]/g, "-").replace(/\s+/g, " ");
}

export function topicKey(raw: string): string {
  return keyOf(raw);
}

export function topicRu(raw: string): string {
  return topicLabel(raw, "ru");
}

export function topicLabel(raw: string, locale: "ru" | "en"): string {
  const hit = TOPIC_RU[keyOf(raw)];
  if (locale === "ru") {
    if (!hit) return raw;
    return `${hit[0]} (${hit[1]})`;
  }
  if (hit) {
    const en = hit[1];
    if (/^[A-Z0-9][A-Z0-9 /+-]*$/.test(en) && en.length <= 12) return en;
    return en.charAt(0).toUpperCase() + en.slice(1);
  }
  return raw;
}

const CLUSTER_ALIAS: Record<string, string> = {
  "human-centered ai": "ai",
  "human centered ai": "ai",
  "human-ai interaction": "ai",
  "human-ai": "ai",
  "information visualization": "vis",
  "data visualization": "vis",
  "visual analytics": "datascience",
  "virtual reality": "xr",
  "augmented reality": "xr",
  "mixed reality": "xr",
  "information retrieval": "search",
  "mobile computing": "mobile",
  "mobile hci": "mobile",
  "haptics": "haptics",
  "cscw": "cscw",
  "computer supported cooperative work": "cscw",
  "computer-supported cooperative work": "cscw",
  "social computing": "socialcomputing",
  "social media": "socialmedia",
  "ubiquitous computing": "ubicomp",
  "ubicomp": "ubicomp",
  "accessibility": "accessibility",
  "accessible computing": "accessibility",
  "data science": "datascience",
  "wearable": "wearable",
  "wearable computing": "wearable",
  "eye tracking": "gaze",
  "privacy": "privacy",
  "crowdsourcing": "crowdsourcing",
};

export function findClusterForTopic<T extends { id: string; label: string; labelEn?: string }>(
  topic: string,
  clusters: T[],
): T | undefined {
  const k = keyOf(topic);
  const aliasId = CLUSTER_ALIAS[k];
  if (aliasId) return clusters.find((c) => c.id === aliasId);
  const shown = keyOf(topicRu(topic));
  return clusters.find((c) => {
    const keys = [c.id, c.label, c.labelEn ?? "", topicRu(c.labelEn || c.label), topicRu(c.label)]
      .filter(Boolean)
      .map(keyOf);
    return keys.includes(k) || keys.includes(shown);
  });
}
