"""
Analytics & Reporting
Performance insights, A/B test analysis, optimization recommendations
"""

from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
import json


@dataclass
class CampaignInsights:
    """Campaign performance insights"""
    campaign_id: int
    overall_metrics: Dict
    persona_performance: List[Dict]
    tier_performance: List[Dict]
    best_performing_content: List[Dict]
    recommendations: List[str]
    ab_test_winners: List[Dict]


class AnalyticsEngine:
    """Analytics and insights engine"""

    def __init__(self, database):
        self.db = database

    def get_campaign_insights(self, campaign_id: int, days: int = 30) -> CampaignInsights:
        """Get comprehensive campaign insights"""

        # Overall metrics
        overall = self.db.get_campaign_performance(campaign_id, days)

        # Persona breakdown
        persona_perf = self.db.get_performance_by_persona(campaign_id)

        # Tier breakdown
        tier_perf = self.db.get_performance_by_tier(campaign_id)

        # Best content
        best_content = self._get_best_performing_content(campaign_id)

        # Generate recommendations
        recommendations = self._generate_recommendations(
            overall, persona_perf, tier_perf
        )

        # A/B test winners (placeholder - would query actual tests)
        ab_winners = []

        return CampaignInsights(
            campaign_id=campaign_id,
            overall_metrics=overall,
            persona_performance=persona_perf,
            tier_performance=tier_perf,
            best_performing_content=best_content,
            recommendations=recommendations,
            ab_test_winners=ab_winners
        )

    def _get_best_performing_content(self, campaign_id: int, limit: int = 10) -> List[Dict]:
        """Get best performing email content"""

        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT
                    id, subject_line, framework_used, quality_score,
                    touch_number,
                    (CASE WHEN sent_at IS NOT NULL THEN 1 ELSE 0 END) as sent,
                    (CASE WHEN opened_at IS NOT NULL THEN 1 ELSE 0 END) as opened,
                    (CASE WHEN replied_at IS NOT NULL THEN 1 ELSE 0 END) as replied
                FROM generated_content
                WHERE campaign_id = ? AND sent_at IS NOT NULL
                ORDER BY replied DESC, opened DESC, quality_score DESC
                LIMIT ?
            """, (campaign_id, limit))

            return [dict(row) for row in cursor.fetchall()]

    def _generate_recommendations(self, overall: Dict, persona_perf: List[Dict],
                                  tier_perf: List[Dict]) -> List[str]:
        """Generate optimization recommendations"""

        recommendations = []

        # Check overall reply rate
        avg_reply_rate = overall.get('avg_reply_rate', 0) or 0

        if avg_reply_rate < 5:
            recommendations.append(
                "Reply rate is below 5% - Consider improving personalization depth and value proposition clarity"
            )
        elif avg_reply_rate < 10:
            recommendations.append(
                "Reply rate is solid but can improve - Test different email frameworks and subject lines"
            )
        else:
            recommendations.append(
                f"Excellent reply rate ({avg_reply_rate:.1f}%) - Double down on current approach and scale volume"
            )

        # Check persona performance
        if persona_perf:
            best_persona = max(persona_perf, key=lambda x: x.get('avg_reply_rate', 0) or 0)
            worst_persona = min(persona_perf, key=lambda x: x.get('avg_reply_rate', 0) or 0)

            recommendations.append(
                f"Best performing persona: {best_persona.get('persona_type')} "
                f"({best_persona.get('avg_reply_rate', 0):.1f}% reply rate) - Allocate more volume here"
            )

            if worst_persona.get('avg_reply_rate', 0) < 3:
                recommendations.append(
                    f"Consider pausing outreach to {worst_persona.get('persona_type')} "
                    f"({worst_persona.get('avg_reply_rate', 0):.1f}% reply rate) and refine messaging"
                )

        # Check tier performance
        if tier_perf:
            for tier in tier_perf:
                tier_name = tier.get('priority_tier')
                reply_rate = tier.get('avg_reply_rate', 0) or 0

                if tier_name == 'A' and reply_rate < 15:
                    recommendations.append(
                        "A-tier prospects underperforming - Review intent signals and personalization quality"
                    )
                elif tier_name == 'C' and reply_rate > 8:
                    recommendations.append(
                        "C-tier prospects performing well - Consider loosening scoring criteria to find more"
                    )

        # Volume recommendations
        total_sent = overall.get('total_sent', 0) or 0
        if total_sent < 50:
            recommendations.append(
                "Sample size is small - Continue testing to gather more data before making major changes"
            )

        return recommendations

    def get_persona_roi_analysis(self, campaign_id: int) -> List[Dict]:
        """Analyze ROI by persona type"""

        with self.db.get_connection() as conn:
            cursor = conn.cursor()

            # Get prospects by persona with meeting conversion
            cursor.execute("""
                SELECT
                    c.persona_type,
                    COUNT(DISTINCT c.id) as contacts_reached,
                    SUM(CASE WHEN c.replied = 1 THEN 1 ELSE 0 END) as replies,
                    SUM(CASE WHEN c.meeting_booked = 1 THEN 1 ELSE 0 END) as meetings,
                    AVG(p.annual_savings_potential) as avg_deal_size
                FROM contacts c
                JOIN prospects p ON c.prospect_id = p.id
                WHERE p.campaign_id = ?
                GROUP BY c.persona_type
            """, (campaign_id,))

            results = []
            for row in cursor.fetchall():
                row_dict = dict(row)
                contacts = row_dict['contacts_reached']
                meetings = row_dict['meetings_booked']

                row_dict['reply_rate'] = (row_dict['replies'] / contacts * 100) if contacts > 0 else 0
                row_dict['meeting_rate'] = (meetings / contacts * 100) if contacts > 0 else 0
                row_dict['estimated_pipeline_value'] = meetings * row_dict['avg_deal_size'] if row_dict['avg_deal_size'] else 0

                results.append(row_dict)

            return sorted(results, key=lambda x: x['estimated_pipeline_value'], reverse=True)

    def get_content_quality_analysis(self, campaign_id: int) -> Dict:
        """Analyze content quality vs performance"""

        with self.db.get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                SELECT
                    CASE
                        WHEN quality_score >= 9 THEN '9-10 (Excellent)'
                        WHEN quality_score >= 7 THEN '7-8 (Good)'
                        WHEN quality_score >= 5 THEN '5-6 (Fair)'
                        ELSE '<5 (Poor)'
                    END as quality_bucket,
                    COUNT(*) as count,
                    SUM(CASE WHEN sent_at IS NOT NULL THEN 1 ELSE 0 END) as sent,
                    SUM(CASE WHEN opened_at IS NOT NULL THEN 1 ELSE 0 END) as opened,
                    SUM(CASE WHEN replied_at IS NOT NULL THEN 1 ELSE 0 END) as replied
                FROM generated_content
                WHERE campaign_id = ?
                GROUP BY quality_bucket
                ORDER BY quality_score DESC
            """, (campaign_id,))

            results = []
            for row in cursor.fetchall():
                row_dict = dict(row)
                sent = row_dict['sent']

                row_dict['open_rate'] = (row_dict['opened'] / sent * 100) if sent > 0 else 0
                row_dict['reply_rate'] = (row_dict['replied'] / sent * 100) if sent > 0 else 0

                results.append(row_dict)

            return {
                "quality_buckets": results,
                "insight": self._quality_insight(results)
            }

    def _quality_insight(self, quality_results: List[Dict]) -> str:
        """Generate insight from quality analysis"""

        if not quality_results:
            return "No data available"

        # Find highest performing bucket
        best_bucket = max(quality_results, key=lambda x: x.get('reply_rate', 0))

        return (
            f"Content in '{best_bucket['quality_bucket']}' range performs best "
            f"with {best_bucket['reply_rate']:.1f}% reply rate. "
            f"Maintain quality gate at this level."
        )

    def get_timing_analysis(self, campaign_id: int) -> Dict:
        """Analyze best send times (day of week, time of day)"""

        with self.db.get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                SELECT
                    strftime('%w', sent_at) as day_of_week,
                    strftime('%H', sent_at) as hour_of_day,
                    COUNT(*) as sent,
                    SUM(CASE WHEN opened_at IS NOT NULL THEN 1 ELSE 0 END) as opened,
                    SUM(CASE WHEN replied_at IS NOT NULL THEN 1 ELSE 0 END) as replied
                FROM generated_content
                WHERE campaign_id = ? AND sent_at IS NOT NULL
                GROUP BY day_of_week, hour_of_day
            """, (campaign_id,))

            results = []
            for row in cursor.fetchall():
                row_dict = dict(row)
                sent = row_dict['sent']

                row_dict['open_rate'] = (row_dict['opened'] / sent * 100) if sent > 0 else 0
                row_dict['reply_rate'] = (row_dict['replied'] / sent * 100) if sent > 0 else 0

                # Convert day/hour to readable format
                days = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
                row_dict['day_name'] = days[int(row_dict['day_of_week'])]

                results.append(row_dict)

            return {
                "timing_data": results,
                "best_day": max(results, key=lambda x: x['reply_rate']) if results else None,
                "best_hour": max(results, key=lambda x: x['reply_rate']) if results else None
            }

    def print_campaign_report(self, campaign_id: int, days: int = 30):
        """Print formatted campaign report"""

        insights = self.get_campaign_insights(campaign_id, days)

        print(f"\n{'='*80}")
        print(f"📊 CAMPAIGN PERFORMANCE REPORT")
        print(f"{'='*80}\n")

        # Overall metrics
        print("OVERALL METRICS (Last {days} days):")
        print(f"  Emails Sent: {insights.overall_metrics.get('total_sent', 0):,}")
        print(f"  Open Rate: {insights.overall_metrics.get('avg_open_rate', 0):.1f}%")
        print(f"  Click Rate: {insights.overall_metrics.get('avg_click_rate', 0):.1f}%")
        print(f"  Reply Rate: {insights.overall_metrics.get('avg_reply_rate', 0):.1f}%")
        print(f"  Meetings Booked: {insights.overall_metrics.get('total_meetings', 0):,}")

        # Persona performance
        if insights.persona_performance:
            print(f"\n📋 PERFORMANCE BY PERSONA:")
            for persona in insights.persona_performance:
                print(f"  {persona.get('persona_type', 'Unknown')}:")
                print(f"    Sent: {persona.get('emails_sent', 0):,}")
                print(f"    Reply Rate: {persona.get('avg_reply_rate', 0):.1f}%")

        # Tier performance
        if insights.tier_performance:
            print(f"\n🎯 PERFORMANCE BY PRIORITY TIER:")
            for tier in insights.tier_performance:
                print(f"  Tier {tier.get('priority_tier', '?')}:")
                print(f"    Sent: {tier.get('emails_sent', 0):,}")
                print(f"    Reply Rate: {tier.get('avg_reply_rate', 0):.1f}%")

        # Recommendations
        if insights.recommendations:
            print(f"\n💡 RECOMMENDATIONS:")
            for i, rec in enumerate(insights.recommendations, 1):
                print(f"  {i}. {rec}")

        # Best content
        if insights.best_performing_content:
            print(f"\n🏆 TOP PERFORMING EMAILS:")
            for email in insights.best_performing_content[:5]:
                print(f"  • {email['subject_line']}")
                print(f"    Framework: {email.get('framework_used', 'Unknown')} | Quality: {email['quality_score']}/10")
                print(f"    Replied: {'✅' if email['replied'] else '❌'}")

        print(f"\n{'='*80}\n")


class ABTestAnalyzer:
    """A/B test analysis and winner selection"""

    def __init__(self, database):
        self.db = database

    def analyze_test(self, campaign_id: int, test_name: str,
                    min_sample_size: int = 30) -> Dict:
        """Analyze A/B test and determine winner"""

        variants = self.db.get_ab_test_results(campaign_id, test_name)

        if not variants:
            return {"status": "no_data", "message": "No variants found"}

        # Check sample size
        for variant in variants:
            if variant['emails_sent'] < min_sample_size:
                return {
                    "status": "insufficient_data",
                    "message": f"Need {min_sample_size} emails per variant, currently at {variant['emails_sent']}",
                    "variants": variants
                }

        # Find winner (highest reply rate with statistical significance)
        winner = max(variants, key=lambda x: x['reply_rate'])

        # Calculate lift
        baseline = min(variants, key=lambda x: x['reply_rate'])
        lift = ((winner['reply_rate'] - baseline['reply_rate']) / baseline['reply_rate'] * 100) if baseline['reply_rate'] > 0 else 0

        # Check statistical significance (simplified)
        is_significant = self._is_statistically_significant(winner, baseline)

        return {
            "status": "complete",
            "winner": winner,
            "lift_percentage": lift,
            "is_significant": is_significant,
            "all_variants": variants,
            "recommendation": self._get_test_recommendation(winner, lift, is_significant)
        }

    def _is_statistically_significant(self, variant_a: Dict, variant_b: Dict,
                                     confidence_level: float = 0.95) -> bool:
        """Check statistical significance (simplified z-test)"""

        # This is a simplified version
        # In production, use proper statistical test (scipy.stats.proportions_ztest)

        n_a = variant_a['emails_sent']
        n_b = variant_b['emails_sent']
        p_a = variant_a['reply_rate'] / 100
        p_b = variant_b['reply_rate'] / 100

        if n_a < 30 or n_b < 30:
            return False

        # Simple heuristic: if difference is > 2% and sample size > 50, likely significant
        diff = abs(p_a - p_b)
        return diff > 0.02 and min(n_a, n_b) > 50

    def _get_test_recommendation(self, winner: Dict, lift: float, is_significant: bool) -> str:
        """Get recommendation based on test results"""

        if not is_significant:
            return "Results not statistically significant yet. Continue testing or try a different variant."

        if lift > 20:
            return f"Strong winner! '{winner['variant_name']}' shows {lift:.1f}% lift. Roll out to all traffic immediately."
        elif lift > 10:
            return f"Clear winner. '{winner['variant_name']}' shows {lift:.1f}% lift. Proceed with rollout."
        else:
            return f"Modest improvement ({lift:.1f}% lift). Consider testing more aggressive variants."


# Example usage
def example_analytics():
    """Example analytics usage"""

    from database import TuneDatabase

    db = TuneDatabase("tune_campaigns.db")
    analytics = AnalyticsEngine(db)

    # Get campaign insights
    campaign_id = 1
    analytics.print_campaign_report(campaign_id, days=30)

    # ROI analysis
    roi_analysis = analytics.get_persona_roi_analysis(campaign_id)
    print("\n💰 PERSONA ROI ANALYSIS:")
    for persona in roi_analysis:
        print(f"  {persona['persona_type']}:")
        print(f"    Pipeline Value: ${persona['estimated_pipeline_value']:,.0f}")
        print(f"    Meeting Rate: {persona['meeting_rate']:.1f}%")

    # A/B test analysis
    ab_analyzer = ABTestAnalyzer(db)
    test_results = ab_analyzer.analyze_test(campaign_id, "subject_line_test_1")
    print(f"\n🧪 A/B TEST RESULTS:")
    print(f"  Status: {test_results['status']}")
    if test_results.get('winner'):
        print(f"  Winner: {test_results['winner']['variant_name']}")
        print(f"  Lift: {test_results['lift_percentage']:.1f}%")
        print(f"  Recommendation: {test_results['recommendation']}")


if __name__ == "__main__":
    example_analytics()
