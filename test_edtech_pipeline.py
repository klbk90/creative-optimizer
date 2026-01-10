"""
Integration Test for EdTech Creative Optimizer Pipeline

This test demonstrates the full flow:
1. Upload creative
2. Find micro-influencers via Modash
3. Create traffic sources with UTM links
4. Simulate traffic (Page Viewed events)
5. Simulate conversions (Order Completed events)
6. Verify Bayesian updates in pattern_performance
7. Get Thompson Sampling recommendations
"""

import os
import sys
import uuid
from datetime import datetime
from sqlalchemy.orm import Session

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database.base import SessionLocal, engine
from database.models import (
    User, Creative, TrafficSource, Conversion,
    PatternPerformance, UserSession
)
from utils.modash_client import ModashClient
from utils.influencer_finder import InfluencerFinder
from utils.creative_analyzer import CreativeAnalyzer


class EdTechPipelineTest:
    """
    End-to-end test for EdTech creative optimizer.
    """

    def __init__(self, db: Session):
        self.db = db
        self.test_user_id = None
        self.creative_id = None
        self.traffic_sources = []

    def setup_test_user(self):
        """Create test user"""
        print("\n=== STEP 1: Setup Test User ===")

        user = User(
            id=uuid.uuid4(),
            email="test@edtech.com",
            password_hash="test_hash",
            subscription_tier="pro",
            is_active=True
        )

        self.db.add(user)
        self.db.commit()

        self.test_user_id = user.id
        print(f"✅ Created test user: {user.id}")

        return user

    def create_test_creative(self):
        """Create a test creative with EdTech pain point"""
        print("\n=== STEP 2: Create Test Creative ===")

        creative = Creative(
            id=uuid.uuid4(),
            user_id=self.test_user_id,
            name="EdTech Creative - Python Course",
            creative_type="ugc",
            source_platform="tiktok",
            video_url="https://example.com/video.mp4",
            duration_seconds=15,

            # EdTech-specific
            product_category="language_learning",
            target_audience_pain="no_time",  # Key pain point

            # Patterns (would be extracted by creative_analyzer in production)
            hook_type="question",
            emotion="curiosity",
            pacing="fast",
            cta_type="urgency",
            has_text_overlay=True,
            has_voiceover=True,

            test_phase="micro_test",
            status="testing"
        )

        self.db.add(creative)
        self.db.commit()

        self.creative_id = creative.id
        print(f"✅ Created creative: {creative.name}")
        print(f"   Pain point: {creative.target_audience_pain}")
        print(f"   Patterns: hook={creative.hook_type}, emotion={creative.emotion}")

        return creative

    def find_micro_influencers(self, n_influencers: int = 5):
        """Find micro-influencers via Modash (mocked for test)"""
        print(f"\n=== STEP 3: Find {n_influencers} Micro-Influencers ===")

        # For testing, create mock influencers
        mock_influencers = []

        for i in range(n_influencers):
            mock_influencers.append({
                "username": f"edutech_creator_{i+1}",
                "fullname": f"EdTech Creator {i+1}",
                "follower_count": 10000 + (i * 5000),
                "engagement_rate": 0.035 + (i * 0.005),
                "contact_email": f"creator{i+1}@example.com"
            })

        print(f"✅ Found {len(mock_influencers)} micro-influencers")

        for inf in mock_influencers:
            print(f"   @{inf['username']}: {inf['follower_count']} followers, ER={inf['engagement_rate']*100:.1f}%")

        return mock_influencers

    def create_traffic_sources(self, influencers: list):
        """Create traffic sources for each influencer"""
        print("\n=== STEP 4: Create Traffic Sources with UTM Links ===")

        for inf in influencers:
            utm_id = f"inf_{inf['username']}_{uuid.uuid4().hex[:6]}"

            traffic_source = TrafficSource(
                id=uuid.uuid4(),
                user_id=self.test_user_id,
                creative_id=self.creative_id,

                # UTM params
                utm_source="instagram",
                utm_medium="influencer",
                utm_campaign="edtech_jan_2026",
                utm_content=inf['username'],
                utm_id=utm_id,

                # Influencer data
                influencer_handle=inf['username'],
                influencer_email=inf['contact_email'],
                influencer_followers=inf['follower_count'],
                influencer_engagement_rate=int(inf['engagement_rate'] * 10000),
                influencer_status="agreed",

                clicks=0,
                conversions=0,
                revenue=0
            )

            self.db.add(traffic_source)
            self.traffic_sources.append(traffic_source)

        self.db.commit()

        print(f"✅ Created {len(self.traffic_sources)} traffic sources")

        for ts in self.traffic_sources:
            print(f"   {ts.utm_id}: @{ts.influencer_handle}")

        return self.traffic_sources

    def simulate_traffic(self, n_clicks_per_source: int = 10):
        """Simulate Page Viewed events"""
        print(f"\n=== STEP 5: Simulate Traffic ({n_clicks_per_source} clicks per source) ===")

        sessions_created = 0

        for traffic_source in self.traffic_sources:
            for i in range(n_clicks_per_source):
                customer_id = f"customer_{traffic_source.utm_id}_{i}"

                # Create user session
                session = UserSession(
                    id=uuid.uuid4(),
                    customer_id=customer_id,
                    external_id=f"anon_{uuid.uuid4().hex[:8]}",
                    utm_id=traffic_source.utm_id,
                    traffic_source_id=traffic_source.id,
                    creative_id=self.creative_id,
                    first_interaction=datetime.utcnow(),
                    touch_count=1
                )

                self.db.add(session)

                # Update traffic source
                traffic_source.clicks += 1

                sessions_created += 1

        self.db.commit()

        print(f"✅ Created {sessions_created} user sessions")
        print(f"   Total clicks: {sum(ts.clicks for ts in self.traffic_sources)}")

        return sessions_created

    def simulate_conversions(self, conversion_rate: float = 0.15):
        """Simulate Order Completed events"""
        print(f"\n=== STEP 6: Simulate Conversions (CVR={conversion_rate*100:.0f}%) ===")

        # Get all sessions
        sessions = self.db.query(UserSession).filter(
            UserSession.creative_id == self.creative_id
        ).all()

        conversions_created = 0
        total_revenue = 0

        for session in sessions:
            # Simulate conversion with probability
            import random
            if random.random() < conversion_rate:
                amount_cents = 4900  # $49 course

                conversion = Conversion(
                    id=uuid.uuid4(),
                    traffic_source_id=session.traffic_source_id,
                    user_id=self.test_user_id,
                    conversion_type="purchase",
                    customer_id=session.customer_id,
                    amount=amount_cents,
                    currency="USD",
                    product_name="Python Course",
                    time_to_conversion=300,  # 5 minutes
                    external_id=session.external_id
                )

                self.db.add(conversion)

                # Update traffic source
                traffic_source = self.db.query(TrafficSource).filter(
                    TrafficSource.id == session.traffic_source_id
                ).first()

                traffic_source.conversions += 1
                traffic_source.revenue += amount_cents

                conversions_created += 1
                total_revenue += amount_cents

        self.db.commit()

        print(f"✅ Created {conversions_created} conversions")
        print(f"   Total revenue: ${total_revenue/100:.2f}")
        print(f"   Actual CVR: {conversions_created/len(sessions)*100:.1f}%")

        return conversions_created

    def update_pattern_performance(self):
        """Update pattern performance with Bayesian method"""
        print("\n=== STEP 7: Update Pattern Performance (Bayesian) ===")

        # Get creative
        creative = self.db.query(Creative).filter(
            Creative.id == self.creative_id
        ).first()

        # Calculate pattern hash
        pattern_hash = (
            f"hook:{creative.hook_type or 'unknown'}"
            f"|emo:{creative.emotion or 'unknown'}"
            f"|pace:{creative.pacing or 'medium'}"
            f"|pain:{creative.target_audience_pain or 'unknown'}"
            f"|cta:{creative.cta_type or 'unknown'}"
        )

        # Get total stats
        total_clicks = sum(ts.clicks for ts in self.traffic_sources)
        total_conversions = sum(ts.conversions for ts in self.traffic_sources)

        # Bayesian update
        from api.routers.rudderstack import bayesian_update_cvr

        mean_cvr, lower_ci, upper_ci = bayesian_update_cvr(
            total_conversions=total_conversions,
            total_clicks=total_clicks,
            alpha_prior=1.0,
            beta_prior=1.0
        )

        # Create or update pattern performance
        pattern_perf = self.db.query(PatternPerformance).filter(
            PatternPerformance.pattern_hash == pattern_hash,
            PatternPerformance.product_category == creative.product_category
        ).first()

        if not pattern_perf:
            pattern_perf = PatternPerformance(
                id=uuid.uuid4(),
                user_id=self.test_user_id,
                pattern_hash=pattern_hash,
                hook_type=creative.hook_type,
                emotion=creative.emotion,
                pacing=creative.pacing,
                cta_type=creative.cta_type,
                target_audience_pain=creative.target_audience_pain,
                product_category=creative.product_category,
                sample_size=1,
                total_clicks=total_clicks,
                total_conversions=total_conversions,
                avg_cvr=int(mean_cvr * 10000),
                confidence_interval_lower=int(lower_ci * 10000),
                confidence_interval_upper=int(upper_ci * 10000)
            )
            self.db.add(pattern_perf)
        else:
            pattern_perf.sample_size += 1
            pattern_perf.total_clicks += total_clicks
            pattern_perf.total_conversions += total_conversions
            pattern_perf.avg_cvr = int(mean_cvr * 10000)
            pattern_perf.confidence_interval_lower = int(lower_ci * 10000)
            pattern_perf.confidence_interval_upper = int(upper_ci * 10000)

        self.db.commit()

        print(f"✅ Updated pattern performance")
        print(f"   Pattern: {pattern_hash}")
        print(f"   Mean CVR: {mean_cvr*100:.2f}%")
        print(f"   95% CI: [{lower_ci*100:.1f}%, {upper_ci*100:.1f}%]")
        print(f"   Sample size: {pattern_perf.sample_size}")

        return pattern_perf

    def get_thompson_sampling_recommendations(self):
        """Get Thompson Sampling recommendations"""
        print("\n=== STEP 8: Thompson Sampling Recommendations ===")

        from api.routers.rudderstack import thompson_sampling

        patterns = self.db.query(PatternPerformance).filter(
            PatternPerformance.product_category == "language_learning"
        ).all()

        recommendations = thompson_sampling(patterns, n_samples=3)

        print(f"✅ Top 3 pattern recommendations:")

        for i, rec in enumerate(recommendations, 1):
            print(f"\n   {i}. {rec['hook_type']} + {rec['emotion']}")
            print(f"      Mean CVR: {rec['mean_cvr']*100:.2f}%")
            print(f"      Thompson Score: {rec['thompson_score']:.3f}")
            print(f"      Sample size: {rec['sample_size']}")
            print(f"      Reasoning: {rec['reasoning']}")

        return recommendations

    def cleanup(self):
        """Clean up test data"""
        print("\n=== CLEANUP ===")

        # Delete in correct order (foreign keys)
        self.db.query(Conversion).filter(
            Conversion.user_id == self.test_user_id
        ).delete()

        self.db.query(UserSession).filter(
            UserSession.creative_id == self.creative_id
        ).delete()

        self.db.query(TrafficSource).filter(
            TrafficSource.user_id == self.test_user_id
        ).delete()

        self.db.query(PatternPerformance).filter(
            PatternPerformance.user_id == self.test_user_id
        ).delete()

        self.db.query(Creative).filter(
            Creative.user_id == self.test_user_id
        ).delete()

        self.db.query(User).filter(
            User.id == self.test_user_id
        ).delete()

        self.db.commit()

        print("✅ Cleaned up test data")

    def run(self):
        """Run full pipeline test"""
        print("\n" + "="*60)
        print("EdTech Creative Optimizer - Full Pipeline Test")
        print("="*60)

        try:
            # Setup
            self.setup_test_user()
            creative = self.create_test_creative()

            # Discovery
            influencers = self.find_micro_influencers(n_influencers=5)
            self.create_traffic_sources(influencers)

            # Testing
            self.simulate_traffic(n_clicks_per_source=20)
            self.simulate_conversions(conversion_rate=0.15)

            # Analysis
            self.update_pattern_performance()
            self.get_thompson_sampling_recommendations()

            print("\n" + "="*60)
            print("✅ PIPELINE TEST COMPLETED SUCCESSFULLY")
            print("="*60)

        except Exception as e:
            print(f"\n❌ ERROR: {e}")
            import traceback
            traceback.print_exc()

        finally:
            # Clean up
            self.cleanup()


def main():
    """
    Run EdTech pipeline test.

    Requirements:
    1. Database must be running (PostgreSQL)
    2. Tables must be created (run migrations first)
    3. Environment variables must be set (.env file)

    Usage:
        python test_edtech_pipeline.py
    """

    # Load environment
    from dotenv import load_dotenv
    load_dotenv()

    # Create database session
    db = SessionLocal()

    try:
        # Run test
        test = EdTechPipelineTest(db)
        test.run()

    finally:
        db.close()


if __name__ == "__main__":
    main()
