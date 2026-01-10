"""
Автоматический поиск микро-инфлюенсеров для тестирования креативов.

Интеграции:
- Modash API (рекомендуется)
- HypeAuditor API
- Сохранение в traffic_sources с автогенерацией UTM

Стратегия:
1. Находим микро-инфлюенсеров (5K-50K подписчиков)
2. Фильтруем по engagement rate (>3%)
3. Генерируем персональную UTM ссылку для каждого
4. Готовим draft outreach письма
"""

import os
import requests
from typing import List, Dict, Optional
from datetime import datetime
import uuid

# Для EdTech: основные "боли" аудитории
EDTECH_PAINS = {
    "no_time": "Нет времени учиться",
    "too_expensive": "Слишком дорого",
    "fear_failure": "Боязнь провала",
    "no_progress": "Нет прогресса в обучении",
    "need_career_switch": "Нужна смена карьеры",
    "imposter_syndrome": "Синдром самозванца",
    "info_overload": "Перегрузка информацией"
}


class InfluencerFinder:
    """
    Поиск микро-инфлюенсеров через API агрегаторов.
    """

    def __init__(self, api_key: str = None, provider: str = "modash"):
        """
        Args:
            api_key: API ключ от Modash/HypeAuditor
            provider: "modash" или "hypeauditor"
        """
        self.api_key = api_key or os.getenv("INFLUENCER_API_KEY")
        self.provider = provider

        if provider == "modash":
            self.base_url = "https://api.modash.io/v1"
        elif provider == "hypeauditor":
            self.base_url = "https://api.hypeauditor.com/v1"
        else:
            raise ValueError(f"Unsupported provider: {provider}")

        if not self.api_key:
            raise ValueError("INFLUENCER_API_KEY not set")

    def search_edtech_micro_influencers(
        self,
        niche: str = "programming",
        geo: List[str] = ["RU", "KZ", "BY"],
        language: str = "ru",
        min_followers: int = 5000,
        max_followers: int = 50000,
        min_engagement: float = 0.03,
        limit: int = 100
    ) -> List[Dict]:
        """
        Поиск микро-инфлюенсеров в EdTech нише.

        Args:
            niche: Ниша (programming, design, english, career)
            geo: Гео аудитории
            language: Язык контента
            min_followers: Минимум подписчиков
            max_followers: Максимум подписчиков
            min_engagement: Минимальный engagement rate (0.03 = 3%)
            limit: Сколько найти

        Returns:
            Список инфлюенсеров с метаданными
        """

        # Ключевые слова по нишам EdTech
        niche_keywords = {
            "programming": ["программирование", "разработка", "python", "javascript", "код"],
            "design": ["дизайн", "фигма", "ui/ux", "веб-дизайн"],
            "english": ["английский", "english", "разговорный", "грамматика"],
            "career": ["карьера", "резюме", "собеседование", "удаленка"],
            "general": ["обучение", "курсы", "образование", "скилл"]
        }

        keywords = niche_keywords.get(niche, niche_keywords["general"])

        # Формируем запрос
        search_payload = {
            "filters": {
                # Гео и язык
                "audience_locations": geo,
                "languages": [language],

                # Размер (микро-инфлюенсеры)
                "follower_count": {
                    "from": min_followers,
                    "to": max_followers
                },

                # Ниша
                "keywords": keywords,
                "categories": ["Education", "Technology", "Business"],

                # Качество
                "engagement_rate": {"from": min_engagement},
                "is_verified": False,  # Не селебрити
                "has_contact_email": True  # Должна быть почта
            },
            "sort": {"field": "engagement_rate", "direction": "desc"},
            "limit": limit
        }

        # API запрос
        try:
            response = requests.post(
                f"{self.base_url}/search/instagram",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json=search_payload,
                timeout=30
            )

            if response.status_code == 200:
                data = response.json()
                influencers = data.get("data", [])

                print(f"✅ Найдено {len(influencers)} микро-инфлюенсеров в нише '{niche}'")
                return influencers

            else:
                print(f"❌ API error: {response.status_code}")
                print(response.text)
                return []

        except Exception as e:
            print(f"❌ Error searching influencers: {e}")
            return []

    def create_traffic_sources_for_influencers(
        self,
        influencers: List[Dict],
        creative_id: str,
        campaign_tag: str,
        db
    ) -> List[Dict]:
        """
        Создает traffic_sources записи для каждого инфлюенсера.

        Автоматически генерирует UTM ссылки вида:
        utm_id = f"inf_{influencer_handle}_{random_id}"

        Args:
            influencers: Список инфлюенсеров от API
            creative_id: ID креатива для тестирования
            campaign_tag: Тег кампании
            db: Database session

        Returns:
            Список созданных traffic sources с UTM ссылками
        """

        from database.models import TrafficSource

        created = []

        for inf in influencers:
            # Извлекаем данные инфлюенсера
            handle = inf.get("username") or inf.get("handle")
            email = inf.get("contact_email")
            followers = inf.get("follower_count", 0)
            engagement_rate = inf.get("engagement_rate", 0)

            # Генерируем UTM ID
            utm_id = f"inf_{handle}_{uuid.uuid4().hex[:6]}"

            # Создаем traffic_source
            traffic_source = TrafficSource(
                id=uuid.uuid4(),
                user_id=uuid.UUID('00000000-0000-0000-0000-000000000001'),  # Test user
                creative_id=uuid.UUID(creative_id),

                # UTM параметры
                utm_source="instagram",
                utm_medium="influencer",
                utm_campaign=campaign_tag,
                utm_content=handle,
                utm_id=utm_id,

                # Инфлюенсер данные
                influencer_handle=handle,
                influencer_email=email,
                influencer_followers=followers,
                influencer_engagement_rate=int(engagement_rate * 10000),
                influencer_status="potential",

                # Инициализация метрик
                clicks=0,
                conversions=0,
                revenue=0,
                first_click=datetime.utcnow()
            )

            db.add(traffic_source)

            created.append({
                "utm_id": utm_id,
                "handle": handle,
                "email": email,
                "followers": followers,
                "engagement_rate": f"{engagement_rate*100:.1f}%"
            })

        db.commit()

        print(f"✅ Создано {len(created)} traffic sources для инфлюенсеров")
        return created

    def generate_outreach_email(
        self,
        influencer_handle: str,
        influencer_email: str,
        utm_link: str,
        creative_name: str,
        product_category: str,
        target_audience_pain: str,
        budget_usd: int = 50
    ) -> Dict[str, str]:
        """
        Генерирует персональное письмо инфлюенсеру.

        Структура:
        - Персонализация (почему именно он/она)
        - Боль аудитории (которую решаем)
        - Простое предложение
        - Прозрачные условия

        Args:
            influencer_handle: Username инфлюенсера
            influencer_email: Email для отправки
            utm_link: Персональная UTM ссылка
            creative_name: Название креатива
            product_category: Категория продукта
            target_audience_pain: Боль ЦА
            budget_usd: Бюджет на пост

        Returns:
            {"subject": "...", "body": "..."}
        """

        # Карта болей → описание для письма
        pain_descriptions = {
            "no_time": "нехватку времени на обучение",
            "too_expensive": "высокую стоимость образования",
            "fear_failure": "страх не справиться с новой профессией",
            "no_progress": "отсутствие видимого прогресса",
            "need_career_switch": "желание сменить карьеру",
            "imposter_syndrome": "синдром самозванца",
            "info_overload": "перегрузку информацией"
        }

        pain_text = pain_descriptions.get(target_audience_pain, "проблемы с обучением")

        subject = f"Коллаб для @{influencer_handle} | {product_category.title()} | ${budget_usd}"

        body = f"""Привет, @{influencer_handle}!

Меня зовут [Твое имя], я тестирую новый EdTech продукт в нише {product_category}.

Почему пишу тебе:
• Твоя аудитория сталкивается с проблемой: {pain_text}
• Я вижу у тебя хороший engagement ({influencer_handle} - один из немногих, кто реально взаимодействует с подписчиками)
• Хочу протестировать гипотезу - поможет ли наше решение

Что предлагаю:
1. Я даю тебе готовый контент (креатив "{creative_name}")
2. Ты публикуешь пост со ссылкой (добавляю твою персональную ссылку)
3. Я плачу ${budget_usd} за публикацию (PayPal/карта)

Важно:
→ Это НЕ массовая реклама. Я тестирую 5-7 блогеров, чтобы понять работает ли продукт
→ Если твоя аудитория отзовется - предложу долгосрочное сотрудничество (x3-5 цена)
→ Полная прозрачность: я делюсь статистикой кликов/конверсий

Твоя персональная ссылка для трекинга:
{utm_link}

Интересно? Ответь "Да" и я вышлю детали + креатив.

P.S. Если не подходит - без обид, может порекомендуешь кого-то из коллег? 🙂

---
[Твое имя]
[Контакты]
"""

        return {
            "subject": subject,
            "body": body,
            "to": influencer_email
        }


def find_and_assign_influencers(
    creative_id: str,
    campaign_tag: str,
    niche: str,
    target_audience_pain: str,
    n_influencers: int = 20,
    db = None
):
    """
    Полный флоу: найти инфлюенсеров → создать UTM → сгенерировать письма.

    Usage:
    ```python
    from utils.influencer_finder import find_and_assign_influencers
    from database.base import SessionLocal

    db = SessionLocal()

    results = find_and_assign_influencers(
        creative_id="your-creative-uuid",
        campaign_tag="edtech_jan_2025",
        niche="programming",
        target_audience_pain="no_time",
        n_influencers=20,
        db=db
    )

    print(f"Найдено: {len(results['influencers'])}")
    print(f"Создано UTM: {len(results['traffic_sources'])}")
    print(f"Писем готово: {len(results['outreach_drafts'])}")
    ```
    """

    if not db:
        raise ValueError("Database session required")

    # 1. Поиск инфлюенсеров
    finder = InfluencerFinder()

    print(f"🔍 Ищу {n_influencers} микро-инфлюенсеров...")
    print(f"   Ниша: {niche}")
    print(f"   Боль ЦА: {target_audience_pain}")

    influencers = finder.search_edtech_micro_influencers(
        niche=niche,
        limit=n_influencers
    )

    if not influencers:
        print("❌ Инфлюенсеры не найдены")
        return {"error": "No influencers found"}

    # 2. Создать traffic sources
    print(f"\n📊 Создаю traffic sources...")

    traffic_sources = finder.create_traffic_sources_for_influencers(
        influencers=influencers,
        creative_id=creative_id,
        campaign_tag=campaign_tag,
        db=db
    )

    # 3. Сгенерировать outreach письма
    print(f"\n✉️ Генерирую outreach письма...")

    outreach_drafts = []

    for ts in traffic_sources:
        email_draft = finder.generate_outreach_email(
            influencer_handle=ts["handle"],
            influencer_email=ts["email"],
            utm_link=f"https://your-domain.com/l/{ts['utm_id']}",
            creative_name="Test Creative",
            product_category=niche,
            target_audience_pain=target_audience_pain,
            budget_usd=50
        )

        outreach_drafts.append(email_draft)

    print(f"\n✅ Готово!")
    print(f"   Найдено инфлюенсеров: {len(influencers)}")
    print(f"   Создано UTM ссылок: {len(traffic_sources)}")
    print(f"   Писем к отправке: {len(outreach_drafts)}")

    return {
        "influencers": influencers,
        "traffic_sources": traffic_sources,
        "outreach_drafts": outreach_drafts
    }


if __name__ == "__main__":
    # Тестовый запуск
    print("🚀 Influencer Finder - EdTech Edition")
    print("\nДля работы нужен API ключ от Modash/HypeAuditor")
    print("Установи: export INFLUENCER_API_KEY=your_key")
    print("\nИспользование:")
    print("  from utils.influencer_finder import find_and_assign_influencers")
