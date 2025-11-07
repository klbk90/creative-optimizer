"""
Creative Clustering Module

Группирует креативы по визуальным и паттерновым признакам.
Помогает найти выстреливающие кластеры и масштабировать победителей.

Методы:
1. CLIP-based clustering (визуальное сходство)
2. Pattern-based clustering (hook, emotion, pacing)
3. Hybrid clustering (комбинация)
"""

import numpy as np
from typing import List, Dict, Optional, Tuple
from sqlalchemy.orm import Session
from sklearn.cluster import KMeans, DBSCAN
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
import json

from database.models import Creative, CreativePattern, PatternPerformance


class CreativeClustering:
    """
    Кластеризация креативов для поиска выстреливающих паттернов.
    """

    def __init__(self, db: Session, user_id: str):
        self.db = db
        self.user_id = user_id

    def cluster_by_visual_similarity(
        self,
        n_clusters: int = 5,
        min_samples: int = 10
    ) -> Dict:
        """
        Кластеризация по визуальному сходству (CLIP embeddings).

        Args:
            n_clusters: Количество кластеров (для K-means)
            min_samples: Минимум семплов для DBSCAN

        Returns:
            {
                "clusters": [
                    {
                        "cluster_id": 0,
                        "size": 15,
                        "avg_cvr": 0.125,
                        "avg_roas": 3.5,
                        "top_creative_ids": [...],
                        "representative_creative": {...}
                    }
                ],
                "method": "kmeans",
                "silhouette_score": 0.65
            }
        """

        # Получить все креативы с CLIP embeddings
        creatives = self.db.query(Creative).filter(
            Creative.user_id == self.user_id,
            Creative.clip_embedding.isnot(None),
            Creative.status.in_(['testing', 'active'])
        ).all()

        if len(creatives) < min_samples:
            return {
                "error": f"Недостаточно креативов с embeddings. Нужно минимум {min_samples}, есть {len(creatives)}",
                "clusters": []
            }

        # Подготовить embeddings
        embeddings = []
        creative_ids = []

        for creative in creatives:
            if creative.clip_embedding:
                embeddings.append(creative.clip_embedding)
                creative_ids.append(str(creative.id))

        X = np.array(embeddings)

        # K-means кластеризация
        from sklearn.metrics import silhouette_score

        kmeans = KMeans(n_clusters=min(n_clusters, len(creatives) // 2), random_state=42)
        cluster_labels = kmeans.fit_predict(X)

        # Рассчитать silhouette score
        silhouette = silhouette_score(X, cluster_labels) if len(set(cluster_labels)) > 1 else 0

        # Группировать креативы по кластерам
        clusters = {}
        for idx, label in enumerate(cluster_labels):
            if label not in clusters:
                clusters[label] = []
            clusters[label].append(creatives[idx])

        # Подготовить результат
        cluster_results = []

        for cluster_id, cluster_creatives in clusters.items():
            # Рассчитать метрики кластера
            cvrs = [c.cvr / 10000 for c in cluster_creatives if c.cvr > 0]
            roas_list = [c.roas / 100 for c in cluster_creatives if c.roas > 0]

            avg_cvr = np.mean(cvrs) if cvrs else 0
            avg_roas = np.mean(roas_list) if roas_list else 0

            # Топ креатив (лучший по CVR)
            top_creative = max(cluster_creatives, key=lambda c: c.cvr)

            cluster_results.append({
                "cluster_id": int(cluster_id),
                "size": len(cluster_creatives),
                "avg_cvr": round(avg_cvr, 4),
                "avg_roas": round(avg_roas, 2),
                "avg_ctr": round(np.mean([c.ctr / 10000 for c in cluster_creatives]), 4),
                "top_creative_ids": [str(c.id) for c in sorted(cluster_creatives, key=lambda c: c.cvr, reverse=True)[:5]],
                "representative_creative": {
                    "id": str(top_creative.id),
                    "name": top_creative.name,
                    "cvr": top_creative.cvr / 10000,
                    "roas": top_creative.roas / 100,
                    "video_url": top_creative.video_url
                },
                # Паттерны кластера (наиболее частые)
                "common_patterns": self._extract_common_patterns(cluster_creatives)
            })

        # Сортировать по производительности
        cluster_results.sort(key=lambda x: x['avg_cvr'], reverse=True)

        return {
            "clusters": cluster_results,
            "method": "kmeans",
            "silhouette_score": round(silhouette, 3),
            "total_creatives": len(creatives)
        }

    def cluster_by_patterns(
        self,
        n_clusters: int = 5
    ) -> Dict:
        """
        Кластеризация по паттернам (hook, emotion, pacing, CTA).

        Это быстрее чем CLIP, но менее точно визуально.
        """

        # Получить все креативы с паттернами
        creatives = self.db.query(Creative).filter(
            Creative.user_id == self.user_id,
            Creative.status.in_(['testing', 'active']),
            Creative.hook_type.isnot(None)
        ).all()

        if len(creatives) < 10:
            return {
                "error": "Недостаточно креативов с паттернами",
                "clusters": []
            }

        # One-hot encoding паттернов
        pattern_features = []

        all_hooks = list(set(c.hook_type for c in creatives if c.hook_type))
        all_emotions = list(set(c.emotion for c in creatives if c.emotion))
        all_pacing = list(set(c.pacing for c in creatives if c.pacing))
        all_ctas = list(set(c.cta_type for c in creatives if c.cta_type))

        for creative in creatives:
            features = []

            # Hook encoding
            features.extend([1 if creative.hook_type == h else 0 for h in all_hooks])

            # Emotion encoding
            features.extend([1 if creative.emotion == e else 0 for e in all_emotions])

            # Pacing encoding
            features.extend([1 if creative.pacing == p else 0 for p in all_pacing])

            # CTA encoding
            features.extend([1 if creative.cta_type == c else 0 for c in all_ctas])

            # Добавить численные метрики
            features.append(creative.ctr / 10000 if creative.ctr else 0)
            features.append(1 if creative.has_text_overlay else 0)
            features.append(1 if creative.has_voiceover else 0)

            pattern_features.append(features)

        X = np.array(pattern_features)

        # Нормализация
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)

        # K-means
        kmeans = KMeans(n_clusters=min(n_clusters, len(creatives) // 2), random_state=42)
        cluster_labels = kmeans.fit_predict(X_scaled)

        # Группировать
        clusters = {}
        for idx, label in enumerate(cluster_labels):
            if label not in clusters:
                clusters[label] = []
            clusters[label].append(creatives[idx])

        # Результаты
        cluster_results = []

        for cluster_id, cluster_creatives in clusters.items():
            cvrs = [c.cvr / 10000 for c in cluster_creatives if c.cvr > 0]
            avg_cvr = np.mean(cvrs) if cvrs else 0

            cluster_results.append({
                "cluster_id": int(cluster_id),
                "size": len(cluster_creatives),
                "avg_cvr": round(avg_cvr, 4),
                "dominant_patterns": self._extract_common_patterns(cluster_creatives),
                "top_creative_ids": [str(c.id) for c in sorted(cluster_creatives, key=lambda c: c.cvr, reverse=True)[:5]]
            })

        cluster_results.sort(key=lambda x: x['avg_cvr'], reverse=True)

        return {
            "clusters": cluster_results,
            "method": "pattern_kmeans",
            "total_creatives": len(creatives)
        }

    def find_winning_cluster(self, min_cvr: float = 0.10) -> Optional[Dict]:
        """
        Найти выстреливающий кластер (CVR > threshold).

        Returns:
            Лучший кластер или None
        """

        visual_clusters = self.cluster_by_visual_similarity()

        if not visual_clusters.get('clusters'):
            return None

        # Найти кластеры с CVR > min_cvr
        winning_clusters = [
            c for c in visual_clusters['clusters']
            if c['avg_cvr'] >= min_cvr
        ]

        if not winning_clusters:
            return None

        # Вернуть лучший
        return winning_clusters[0]

    def recommend_scaling_creatives(
        self,
        budget: int = 5000,
        min_cvr: float = 0.10
    ) -> Dict:
        """
        Рекомендовать креативы для масштабирования.

        Args:
            budget: Бюджет в центах ($50 = 5000)
            min_cvr: Минимальный CVR для отбора

        Returns:
            {
                "recommended_creatives": [...],
                "total_budget": 5000,
                "budget_per_creative": 1000,
                "expected_roi": 3.5,
                "confidence": 0.85
            }
        """

        winning_cluster = self.find_winning_cluster(min_cvr=min_cvr)

        if not winning_cluster:
            return {
                "error": f"Нет кластеров с CVR > {min_cvr*100}%",
                "recommended_creatives": []
            }

        # Топ креативы из выстреливающего кластера
        top_creative_ids = winning_cluster['top_creative_ids']

        # Получить детали
        creatives = self.db.query(Creative).filter(
            Creative.id.in_(top_creative_ids)
        ).all()

        # Распределить бюджет
        budget_per_creative = budget // len(creatives)

        # Рассчитать ожидаемый ROI
        avg_roas = winning_cluster['avg_roas']
        expected_revenue = budget * avg_roas
        expected_roi = avg_roas

        return {
            "recommended_creatives": [
                {
                    "id": str(c.id),
                    "name": c.name,
                    "cvr": c.cvr / 10000,
                    "roas": c.roas / 100,
                    "video_url": c.video_url,
                    "recommended_budget": budget_per_creative,
                    "expected_conversions": int((budget_per_creative / 100) * (c.cvr / 10000))
                }
                for c in creatives
            ],
            "cluster_info": {
                "cluster_id": winning_cluster['cluster_id'],
                "cluster_size": winning_cluster['size'],
                "avg_cvr": winning_cluster['avg_cvr'],
                "avg_roas": winning_cluster['avg_roas']
            },
            "total_budget": budget,
            "budget_per_creative": budget_per_creative,
            "expected_revenue": int(expected_revenue),
            "expected_roi": round(expected_roi, 2),
            "confidence": 0.85 if len(creatives) >= 10 else 0.60
        }

    def _extract_common_patterns(self, creatives: List[Creative]) -> Dict:
        """
        Извлечь наиболее частые паттерны в кластере.
        """

        from collections import Counter

        hooks = Counter(c.hook_type for c in creatives if c.hook_type)
        emotions = Counter(c.emotion for c in creatives if c.emotion)
        pacing = Counter(c.pacing for c in creatives if c.pacing)
        ctas = Counter(c.cta_type for c in creatives if c.cta_type)

        return {
            "hook_type": hooks.most_common(1)[0][0] if hooks else None,
            "emotion": emotions.most_common(1)[0][0] if emotions else None,
            "pacing": pacing.most_common(1)[0][0] if pacing else None,
            "cta_type": ctas.most_common(1)[0][0] if ctas else None,
            "has_text_overlay": sum(1 for c in creatives if c.has_text_overlay) / len(creatives),
            "has_voiceover": sum(1 for c in creatives if c.has_voiceover) / len(creatives)
        }

    def visualize_clusters(self, method: str = "visual") -> Dict:
        """
        Визуализировать кластеры в 2D (PCA).

        Returns:
            Координаты для графика
        """

        if method == "visual":
            clustering_result = self.cluster_by_visual_similarity()
        else:
            clustering_result = self.cluster_by_patterns()

        # TODO: Реализовать PCA + координаты для фронтенда
        # Это будет использоваться в Grafana или custom dashboard

        return clustering_result
