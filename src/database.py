"""
Database Layer
Campaign tracking, performance analytics, A/B testing results
"""

import sqlite3
import json
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from contextlib import contextmanager


class TuneDatabase:
    """SQLite database for Tune campaign tracking and analytics"""

    def __init__(self, db_path: str = "tune_campaigns.db"):
        self.db_path = db_path
        self._create_tables()

    @contextmanager
    def get_connection(self):
        """Context manager for database connections"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    def _create_tables(self):
        """Create all database tables"""

        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Campaigns table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS campaigns (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    industry TEXT NOT NULL,
                    start_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    end_date TIMESTAMP,
                    status TEXT DEFAULT 'active',
                    total_prospects INTEGER DEFAULT 0,
                    total_emails_sent INTEGER DEFAULT 0,
                    total_opens INTEGER DEFAULT 0,
                    total_clicks INTEGER DEFAULT 0,
                    total_replies INTEGER DEFAULT 0,
                    total_meetings_booked INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Prospects table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS prospects (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    campaign_id INTEGER,
                    company_name TEXT NOT NULL,
                    domain TEXT,
                    industry TEXT,
                    employee_count INTEGER,
                    composite_score REAL,
                    priority_tier TEXT,
                    intent_score REAL,
                    technical_fit_score REAL,
                    urgency_score REAL,
                    annual_savings_potential REAL,
                    payback_months REAL,
                    sustainability_maturity INTEGER,
                    intent_signals_json TEXT,
                    personalization_points_json TEXT,
                    analysis_status TEXT DEFAULT 'pending',
                    outreach_status TEXT DEFAULT 'not_started',
                    analyzed_at TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (campaign_id) REFERENCES campaigns (id)
                )
            """)

            # Contacts table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS contacts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    prospect_id INTEGER,
                    full_name TEXT,
                    email TEXT,
                    title TEXT,
                    linkedin_url TEXT,
                    persona_type TEXT,
                    decision_authority TEXT,
                    priority_order INTEGER,
                    outreach_status TEXT DEFAULT 'not_contacted',
                    current_touch INTEGER DEFAULT 0,
                    last_contacted TIMESTAMP,
                    replied BOOLEAN DEFAULT 0,
                    meeting_booked BOOLEAN DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (prospect_id) REFERENCES prospects (id)
                )
            """)

            # Generated content table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS generated_content (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    prospect_id INTEGER,
                    contact_id INTEGER,
                    campaign_id INTEGER,
                    touch_number INTEGER,
                    subject_line TEXT,
                    email_body TEXT,
                    framework_used TEXT,
                    quality_score REAL,
                    personalization_depth INTEGER,
                    variant_id TEXT,
                    status TEXT DEFAULT 'draft',
                    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    sent_at TIMESTAMP,
                    opened_at TIMESTAMP,
                    clicked_at TIMESTAMP,
                    replied_at TIMESTAMP,
                    FOREIGN KEY (prospect_id) REFERENCES prospects (id),
                    FOREIGN KEY (contact_id) REFERENCES contacts (id),
                    FOREIGN KEY (campaign_id) REFERENCES campaigns (id)
                )
            """)

            # A/B test variants table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS ab_test_variants (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    campaign_id INTEGER,
                    test_name TEXT NOT NULL,
                    variant_name TEXT NOT NULL,
                    variant_type TEXT,
                    subject_line TEXT,
                    email_hook TEXT,
                    framework_type TEXT,
                    emails_sent INTEGER DEFAULT 0,
                    opens INTEGER DEFAULT 0,
                    clicks INTEGER DEFAULT 0,
                    replies INTEGER DEFAULT 0,
                    open_rate REAL DEFAULT 0,
                    reply_rate REAL DEFAULT 0,
                    is_winner BOOLEAN DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (campaign_id) REFERENCES campaigns (id)
                )
            """)

            # Email events table (for tracking)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS email_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    content_id INTEGER,
                    contact_id INTEGER,
                    event_type TEXT NOT NULL,
                    event_data TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (content_id) REFERENCES generated_content (id),
                    FOREIGN KEY (contact_id) REFERENCES contacts (id)
                )
            """)

            # Performance metrics table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS performance_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    campaign_id INTEGER,
                    metric_date DATE NOT NULL,
                    industry TEXT,
                    persona_type TEXT,
                    priority_tier TEXT,
                    emails_sent INTEGER DEFAULT 0,
                    emails_opened INTEGER DEFAULT 0,
                    emails_clicked INTEGER DEFAULT 0,
                    emails_replied INTEGER DEFAULT 0,
                    meetings_booked INTEGER DEFAULT 0,
                    open_rate REAL DEFAULT 0,
                    click_rate REAL DEFAULT 0,
                    reply_rate REAL DEFAULT 0,
                    meeting_rate REAL DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (campaign_id) REFERENCES campaigns (id)
                )
            """)

            conn.commit()

    # ==================== CAMPAIGNS ====================

    def create_campaign(self, name: str, industry: str) -> int:
        """Create new campaign"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO campaigns (name, industry) VALUES (?, ?)",
                (name, industry)
            )
            return cursor.lastrowid

    def get_campaign(self, campaign_id: int) -> Optional[Dict]:
        """Get campaign by ID"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM campaigns WHERE id = ?", (campaign_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def update_campaign_stats(self, campaign_id: int, stats: Dict):
        """Update campaign statistics"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE campaigns SET
                    total_prospects = ?,
                    total_emails_sent = ?,
                    total_opens = ?,
                    total_clicks = ?,
                    total_replies = ?,
                    total_meetings_booked = ?
                WHERE id = ?
            """, (
                stats.get('total_prospects', 0),
                stats.get('total_emails_sent', 0),
                stats.get('total_opens', 0),
                stats.get('total_clicks', 0),
                stats.get('total_replies', 0),
                stats.get('total_meetings_booked', 0),
                campaign_id
            ))

    # ==================== PROSPECTS ====================

    def insert_prospect(self, campaign_id: int, prospect_data: Dict, analysis: Dict) -> int:
        """Insert analyzed prospect"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO prospects (
                    campaign_id, company_name, domain, industry, employee_count,
                    composite_score, priority_tier, intent_score, technical_fit_score,
                    urgency_score, annual_savings_potential, payback_months,
                    sustainability_maturity, intent_signals_json, personalization_points_json,
                    analysis_status, analyzed_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                campaign_id,
                prospect_data['company_name'],
                prospect_data.get('domain'),
                prospect_data.get('industry'),
                prospect_data.get('employee_count'),
                analysis['composite_score'],
                analysis['priority_tier'],
                analysis['scores']['intent'],
                analysis['scores']['technical_fit'],
                analysis['scores']['urgency'],
                analysis['savings_projection']['annual_savings_dollars'],
                analysis['savings_projection']['payback_period_months'],
                analysis.get('sustainability_maturity', 2),
                json.dumps(analysis['intent_signals']),
                json.dumps(analysis['personalization_intel']['personalization_points']),
                'analyzed',
                datetime.now().isoformat()
            ))
            return cursor.lastrowid

    def get_prospects_by_tier(self, campaign_id: int, tier: str) -> List[Dict]:
        """Get prospects by priority tier"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM prospects
                WHERE campaign_id = ? AND priority_tier = ?
                ORDER BY composite_score DESC
            """, (campaign_id, tier))
            return [dict(row) for row in cursor.fetchall()]

    def get_high_value_prospects(self, campaign_id: int, min_savings: float = 50000) -> List[Dict]:
        """Get high-value prospects"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM prospects
                WHERE campaign_id = ? AND annual_savings_potential >= ?
                ORDER BY annual_savings_potential DESC
            """, (campaign_id, min_savings))
            return [dict(row) for row in cursor.fetchall()]

    # ==================== CONTACTS ====================

    def insert_contact(self, prospect_id: int, contact_data: Dict) -> int:
        """Insert contact/decision maker"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO contacts (
                    prospect_id, full_name, email, title, linkedin_url,
                    persona_type, decision_authority, priority_order
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                prospect_id,
                contact_data.get('full_name'),
                contact_data.get('email'),
                contact_data.get('title'),
                contact_data.get('linkedin_url'),
                contact_data.get('persona_type'),
                contact_data.get('decision_authority'),
                contact_data.get('priority_order', 1)
            ))
            return cursor.lastrowid

    # ==================== GENERATED CONTENT ====================

    def insert_generated_content(self, prospect_id: int, campaign_id: int,
                                 contact_id: Optional[int], email_data: Dict) -> int:
        """Insert generated email content"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO generated_content (
                    prospect_id, contact_id, campaign_id, touch_number,
                    subject_line, email_body, framework_used, quality_score,
                    personalization_depth, variant_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                prospect_id,
                contact_id,
                campaign_id,
                email_data['touch_number'],
                email_data['subject'],
                email_data['body'],
                email_data.get('framework_used'),
                email_data['quality_score'],
                len(email_data.get('personalization_used', [])),
                email_data.get('variant_id')
            ))
            return cursor.lastrowid

    def get_content_ready_to_send(self, campaign_id: int, min_quality: float = 7.0) -> List[Dict]:
        """Get content ready to send (high quality, not sent)"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM generated_content
                WHERE campaign_id = ?
                  AND quality_score >= ?
                  AND status IN ('draft', 'approved')
                  AND sent_at IS NULL
                ORDER BY quality_score DESC
            """, (campaign_id, min_quality))
            return [dict(row) for row in cursor.fetchall()]

    def mark_content_sent(self, content_id: int):
        """Mark content as sent"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE generated_content
                SET status = 'sent', sent_at = ?
                WHERE id = ?
            """, (datetime.now().isoformat(), content_id))

    # ==================== EMAIL EVENTS ====================

    def track_email_event(self, content_id: int, contact_id: int,
                         event_type: str, event_data: Optional[Dict] = None):
        """Track email event (open, click, reply)"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO email_events (content_id, contact_id, event_type, event_data)
                VALUES (?, ?, ?, ?)
            """, (
                content_id,
                contact_id,
                event_type,
                json.dumps(event_data) if event_data else None
            ))

            # Update content record
            if event_type == 'opened':
                cursor.execute(
                    "UPDATE generated_content SET opened_at = ? WHERE id = ?",
                    (datetime.now().isoformat(), content_id)
                )
            elif event_type == 'clicked':
                cursor.execute(
                    "UPDATE generated_content SET clicked_at = ? WHERE id = ?",
                    (datetime.now().isoformat(), content_id)
                )
            elif event_type == 'replied':
                cursor.execute(
                    "UPDATE generated_content SET replied_at = ?, status = 'replied' WHERE id = ?",
                    (datetime.now().isoformat(), content_id)
                )
                # Update contact
                cursor.execute(
                    "UPDATE contacts SET replied = 1 WHERE id = ?",
                    (contact_id,)
                )

    # ==================== A/B TESTING ====================

    def create_ab_test_variant(self, campaign_id: int, test_name: str,
                              variant_name: str, variant_data: Dict) -> int:
        """Create A/B test variant"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO ab_test_variants (
                    campaign_id, test_name, variant_name, variant_type,
                    subject_line, email_hook, framework_type
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                campaign_id,
                test_name,
                variant_name,
                variant_data.get('variant_type'),
                variant_data.get('subject_line'),
                variant_data.get('email_hook'),
                variant_data.get('framework_type')
            ))
            return cursor.lastrowid

    def update_variant_metrics(self, variant_id: int, metrics: Dict):
        """Update A/B test variant metrics"""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            emails_sent = metrics.get('emails_sent', 0)
            opens = metrics.get('opens', 0)
            clicks = metrics.get('clicks', 0)
            replies = metrics.get('replies', 0)

            open_rate = (opens / emails_sent * 100) if emails_sent > 0 else 0
            reply_rate = (replies / emails_sent * 100) if emails_sent > 0 else 0

            cursor.execute("""
                UPDATE ab_test_variants SET
                    emails_sent = ?,
                    opens = ?,
                    clicks = ?,
                    replies = ?,
                    open_rate = ?,
                    reply_rate = ?
                WHERE id = ?
            """, (emails_sent, opens, clicks, replies, open_rate, reply_rate, variant_id))

    def get_ab_test_results(self, campaign_id: int, test_name: str) -> List[Dict]:
        """Get A/B test results"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM ab_test_variants
                WHERE campaign_id = ? AND test_name = ?
                ORDER BY reply_rate DESC
            """, (campaign_id, test_name))
            return [dict(row) for row in cursor.fetchall()]

    # ==================== ANALYTICS ====================

    def record_daily_metrics(self, campaign_id: int, metrics: Dict):
        """Record daily performance metrics"""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            emails_sent = metrics.get('emails_sent', 0)
            emails_opened = metrics.get('emails_opened', 0)
            emails_clicked = metrics.get('emails_clicked', 0)
            emails_replied = metrics.get('emails_replied', 0)
            meetings_booked = metrics.get('meetings_booked', 0)

            cursor.execute("""
                INSERT INTO performance_metrics (
                    campaign_id, metric_date, industry, persona_type, priority_tier,
                    emails_sent, emails_opened, emails_clicked, emails_replied, meetings_booked,
                    open_rate, click_rate, reply_rate, meeting_rate
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                campaign_id,
                datetime.now().date().isoformat(),
                metrics.get('industry'),
                metrics.get('persona_type'),
                metrics.get('priority_tier'),
                emails_sent,
                emails_opened,
                emails_clicked,
                emails_replied,
                meetings_booked,
                (emails_opened / emails_sent * 100) if emails_sent > 0 else 0,
                (emails_clicked / emails_sent * 100) if emails_sent > 0 else 0,
                (emails_replied / emails_sent * 100) if emails_sent > 0 else 0,
                (meetings_booked / emails_sent * 100) if emails_sent > 0 else 0
            ))

    def get_campaign_performance(self, campaign_id: int, days: int = 30) -> Dict:
        """Get campaign performance over time"""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            start_date = (datetime.now() - timedelta(days=days)).date().isoformat()

            cursor.execute("""
                SELECT
                    SUM(emails_sent) as total_sent,
                    SUM(emails_opened) as total_opened,
                    SUM(emails_clicked) as total_clicked,
                    SUM(emails_replied) as total_replied,
                    SUM(meetings_booked) as total_meetings,
                    AVG(open_rate) as avg_open_rate,
                    AVG(click_rate) as avg_click_rate,
                    AVG(reply_rate) as avg_reply_rate,
                    AVG(meeting_rate) as avg_meeting_rate
                FROM performance_metrics
                WHERE campaign_id = ? AND metric_date >= ?
            """, (campaign_id, start_date))

            row = cursor.fetchone()
            return dict(row) if row else {}

    def get_performance_by_persona(self, campaign_id: int) -> List[Dict]:
        """Get performance breakdown by persona"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT
                    persona_type,
                    SUM(emails_sent) as emails_sent,
                    AVG(open_rate) as avg_open_rate,
                    AVG(reply_rate) as avg_reply_rate
                FROM performance_metrics
                WHERE campaign_id = ? AND persona_type IS NOT NULL
                GROUP BY persona_type
                ORDER BY avg_reply_rate DESC
            """, (campaign_id,))
            return [dict(row) for row in cursor.fetchall()]

    def get_performance_by_tier(self, campaign_id: int) -> List[Dict]:
        """Get performance breakdown by priority tier"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT
                    priority_tier,
                    SUM(emails_sent) as emails_sent,
                    AVG(open_rate) as avg_open_rate,
                    AVG(reply_rate) as avg_reply_rate
                FROM performance_metrics
                WHERE campaign_id = ? AND priority_tier IS NOT NULL
                GROUP BY priority_tier
                ORDER BY priority_tier
            """, (campaign_id,))
            return [dict(row) for row in cursor.fetchall()]


# Example usage
def example_database_usage():
    """Example database operations"""

    db = TuneDatabase("tune_campaigns.db")

    # Create campaign
    campaign_id = db.create_campaign("Casino Q1 2025", "casino")
    print(f"Created campaign: {campaign_id}")

    # Insert prospect analysis
    prospect_data = {
        "company_name": "MGM Grand",
        "domain": "mgmgrand.com",
        "industry": "casino",
        "employee_count": 5000
    }

    analysis = {
        "composite_score": 82.5,
        "priority_tier": "A",
        "scores": {
            "intent": 75.0,
            "technical_fit": 90.0,
            "urgency": 80.0
        },
        "savings_projection": {
            "annual_savings_dollars": 125000,
            "payback_period_months": 14
        },
        "sustainability_maturity": 4,
        "intent_signals": {"sustainability_commitments": ["Net zero by 2030"]},
        "personalization_intel": {
            "personalization_points": ["Published ESG report", "Recent expansion"]
        }
    }

    prospect_id = db.insert_prospect(campaign_id, prospect_data, analysis)
    print(f"Inserted prospect: {prospect_id}")

    # Track email event
    content_id = 1  # Example
    contact_id = 1  # Example
    db.track_email_event(content_id, contact_id, "opened")
    print("Tracked email open")

    # Get campaign performance
    performance = db.get_campaign_performance(campaign_id, days=7)
    print(f"Campaign performance: {performance}")


if __name__ == "__main__":
    example_database_usage()
