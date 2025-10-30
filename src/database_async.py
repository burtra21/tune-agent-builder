"""
Production-Grade Async Database Layer with Connection Pooling
Replaces database.py with SQLAlchemy async for 10x better scale performance
"""

import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, Text, DateTime, ForeignKey,
    Index, CheckConstraint, select, func, and_, or_, text
)
from typing import Dict, List, Any, Optional, AsyncGenerator
from datetime import datetime, timedelta
from contextlib import asynccontextmanager
import json
import structlog

logger = structlog.get_logger()

Base = declarative_base()


# ==================== MODELS ====================

class Campaign(Base):
    __tablename__ = "campaigns"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    industry = Column(String(100), nullable=False, index=True)
    start_date = Column(DateTime, default=datetime.now)
    end_date = Column(DateTime, nullable=True)
    status = Column(String(50), default='active', index=True)
    total_prospects = Column(Integer, default=0)
    total_emails_sent = Column(Integer, default=0)
    total_opens = Column(Integer, default=0)
    total_clicks = Column(Integer, default=0)
    total_replies = Column(Integer, default=0)
    total_meetings_booked = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.now, index=True)

    # Relationships
    prospects = relationship("Prospect", back_populates="campaign", cascade="all, delete-orphan")
    content = relationship("GeneratedContent", back_populates="campaign")
    ab_variants = relationship("ABTestVariant", back_populates="campaign")
    metrics = relationship("PerformanceMetric", back_populates="campaign")


class Prospect(Base):
    __tablename__ = "prospects"

    id = Column(Integer, primary_key=True, autoincrement=True)
    campaign_id = Column(Integer, ForeignKey('campaigns.id'), nullable=False, index=True)
    company_name = Column(String(255), nullable=False, index=True)
    domain = Column(String(255), index=True)
    industry = Column(String(100), index=True)
    employee_count = Column(Integer)
    composite_score = Column(Float, index=True)
    priority_tier = Column(String(1), index=True)  # A, B, C
    intent_score = Column(Float)
    technical_fit_score = Column(Float)
    urgency_score = Column(Float)
    annual_savings_potential = Column(Float, index=True)
    payback_months = Column(Float)
    sustainability_maturity = Column(Integer)
    intent_signals_json = Column(Text)
    personalization_points_json = Column(Text)
    analysis_status = Column(String(50), default='pending', index=True)
    outreach_status = Column(String(50), default='not_started', index=True)
    analyzed_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.now, index=True)

    # Relationships
    campaign = relationship("Campaign", back_populates="prospects")
    contacts = relationship("Contact", back_populates="prospect", cascade="all, delete-orphan")
    content = relationship("GeneratedContent", back_populates="prospect")

    __table_args__ = (
        Index('idx_campaign_tier', 'campaign_id', 'priority_tier'),
        Index('idx_campaign_score', 'campaign_id', 'composite_score'),
        Index('idx_savings', 'annual_savings_potential'),
    )


class Contact(Base):
    __tablename__ = "contacts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    prospect_id = Column(Integer, ForeignKey('prospects.id'), nullable=False, index=True)
    full_name = Column(String(255))
    email = Column(String(255), index=True)
    title = Column(String(255))
    linkedin_url = Column(String(500))
    persona_type = Column(String(100), index=True)
    decision_authority = Column(String(50))
    priority_order = Column(Integer, default=1)
    outreach_status = Column(String(50), default='not_contacted', index=True)
    current_touch = Column(Integer, default=0)
    last_contacted = Column(DateTime)
    replied = Column(Boolean, default=False, index=True)
    meeting_booked = Column(Boolean, default=False, index=True)
    created_at = Column(DateTime, default=datetime.now)

    # Relationships
    prospect = relationship("Prospect", back_populates="contacts")
    content = relationship("GeneratedContent", back_populates="contact")
    events = relationship("EmailEvent", back_populates="contact")


class GeneratedContent(Base):
    __tablename__ = "generated_content"

    id = Column(Integer, primary_key=True, autoincrement=True)
    prospect_id = Column(Integer, ForeignKey('prospects.id'), nullable=False, index=True)
    contact_id = Column(Integer, ForeignKey('contacts.id'), index=True)
    campaign_id = Column(Integer, ForeignKey('campaigns.id'), nullable=False, index=True)
    touch_number = Column(Integer, index=True)
    subject_line = Column(Text)
    email_body = Column(Text)
    framework_used = Column(String(100))
    quality_score = Column(Float, index=True)
    personalization_depth = Column(Integer)
    variant_id = Column(String(100), index=True)
    status = Column(String(50), default='draft', index=True)
    generated_at = Column(DateTime, default=datetime.now, index=True)
    sent_at = Column(DateTime, index=True)
    opened_at = Column(DateTime)
    clicked_at = Column(DateTime)
    replied_at = Column(DateTime)

    # Relationships
    prospect = relationship("Prospect", back_populates="content")
    contact = relationship("Contact", back_populates="content")
    campaign = relationship("Campaign", back_populates="content")
    events = relationship("EmailEvent", back_populates="content")

    __table_args__ = (
        Index('idx_campaign_status', 'campaign_id', 'status'),
        Index('idx_quality', 'quality_score'),
    )


class ABTestVariant(Base):
    __tablename__ = "ab_test_variants"

    id = Column(Integer, primary_key=True, autoincrement=True)
    campaign_id = Column(Integer, ForeignKey('campaigns.id'), nullable=False, index=True)
    test_name = Column(String(255), nullable=False, index=True)
    variant_name = Column(String(255), nullable=False)
    variant_type = Column(String(100))
    subject_line = Column(Text)
    email_hook = Column(Text)
    framework_type = Column(String(100))
    emails_sent = Column(Integer, default=0)
    opens = Column(Integer, default=0)
    clicks = Column(Integer, default=0)
    replies = Column(Integer, default=0)
    open_rate = Column(Float, default=0)
    reply_rate = Column(Float, default=0)
    is_winner = Column(Boolean, default=False, index=True)
    created_at = Column(DateTime, default=datetime.now)

    # Relationships
    campaign = relationship("Campaign", back_populates="ab_variants")

    __table_args__ = (
        Index('idx_test_name', 'campaign_id', 'test_name'),
    )


class EmailEvent(Base):
    __tablename__ = "email_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    content_id = Column(Integer, ForeignKey('generated_content.id'), nullable=False, index=True)
    contact_id = Column(Integer, ForeignKey('contacts.id'), nullable=False, index=True)
    event_type = Column(String(50), nullable=False, index=True)  # opened, clicked, replied
    event_data = Column(Text)
    timestamp = Column(DateTime, default=datetime.now, index=True)

    # Relationships
    content = relationship("GeneratedContent", back_populates="events")
    contact = relationship("Contact", back_populates="events")

    __table_args__ = (
        Index('idx_content_event', 'content_id', 'event_type'),
    )


class PerformanceMetric(Base):
    __tablename__ = "performance_metrics"

    id = Column(Integer, primary_key=True, autoincrement=True)
    campaign_id = Column(Integer, ForeignKey('campaigns.id'), nullable=False, index=True)
    metric_date = Column(DateTime, nullable=False, index=True)
    industry = Column(String(100), index=True)
    persona_type = Column(String(100), index=True)
    priority_tier = Column(String(1), index=True)
    emails_sent = Column(Integer, default=0)
    emails_opened = Column(Integer, default=0)
    emails_clicked = Column(Integer, default=0)
    emails_replied = Column(Integer, default=0)
    meetings_booked = Column(Integer, default=0)
    open_rate = Column(Float, default=0)
    click_rate = Column(Float, default=0)
    reply_rate = Column(Float, default=0)
    meeting_rate = Column(Float, default=0)
    created_at = Column(DateTime, default=datetime.now)

    # Relationships
    campaign = relationship("Campaign", back_populates="metrics")

    __table_args__ = (
        Index('idx_campaign_date', 'campaign_id', 'metric_date'),
        Index('idx_persona', 'persona_type', 'metric_date'),
    )


# ==================== ASYNC DATABASE ====================

class TuneDatabaseAsync:
    """Production-grade async database with connection pooling"""

    def __init__(self, db_url: Optional[str] = None):
        """
        Initialize async database with connection pooling

        Args:
            db_url: Database URL. If None, uses env var or defaults to SQLite
        """
        if db_url is None:
            db_url = os.getenv(
                "DATABASE_URL",
                "sqlite+aiosqlite:///tune_campaigns.db"
            )

        # Configure engine with connection pooling
        engine_kwargs = {
            "echo": os.getenv("DB_ECHO", "false").lower() == "true",
            "future": True,
        }

        # Add pooling config for non-SQLite databases
        if not db_url.startswith("sqlite"):
            engine_kwargs.update({
                "pool_size": int(os.getenv("DB_POOL_SIZE", "20")),
                "max_overflow": int(os.getenv("DB_MAX_OVERFLOW", "10")),
                "pool_timeout": int(os.getenv("DB_POOL_TIMEOUT", "30")),
                "pool_recycle": int(os.getenv("DB_POOL_RECYCLE", "3600")),
                "pool_pre_ping": True,  # Verify connections before using
            })
        else:
            # SQLite-specific optimizations
            engine_kwargs.update({
                "connect_args": {
                    "check_same_thread": False,
                    "timeout": 30,
                }
            })

        self.engine = create_async_engine(db_url, **engine_kwargs)
        self.async_session_maker = async_sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

        logger.info("database_initialized", url=db_url.split("@")[-1])  # Hide credentials

    async def init_db(self):
        """Create all tables"""
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        # Enable WAL mode for SQLite (allows concurrent reads/writes)
        if "sqlite" in str(self.engine.url):
            async with self.engine.connect() as conn:
                await conn.execute(text("PRAGMA journal_mode=WAL"))
                await conn.execute(text("PRAGMA foreign_keys=ON"))
                await conn.commit()

        logger.info("database_tables_created")

    @asynccontextmanager
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get async database session (context manager)"""
        async with self.async_session_maker() as session:
            try:
                yield session
                await session.commit()
            except Exception as e:
                await session.rollback()
                logger.error("database_session_error", error=str(e))
                raise

    async def close(self):
        """Close all connections"""
        await self.engine.dispose()
        logger.info("database_connections_closed")

    # ==================== CAMPAIGNS ====================

    async def create_campaign(self, name: str, industry: str) -> int:
        """Create new campaign"""
        async with self.get_session() as session:
            campaign = Campaign(name=name, industry=industry)
            session.add(campaign)
            await session.flush()
            campaign_id = campaign.id
            logger.info("campaign_created", campaign_id=campaign_id, name=name)
            return campaign_id

    async def get_campaign(self, campaign_id: int) -> Optional[Dict]:
        """Get campaign by ID"""
        async with self.get_session() as session:
            result = await session.execute(
                select(Campaign).where(Campaign.id == campaign_id)
            )
            campaign = result.scalar_one_or_none()

            if campaign:
                return {
                    "id": campaign.id,
                    "name": campaign.name,
                    "industry": campaign.industry,
                    "status": campaign.status,
                    "total_prospects": campaign.total_prospects,
                    "total_emails_sent": campaign.total_emails_sent,
                    "total_opens": campaign.total_opens,
                    "total_clicks": campaign.total_clicks,
                    "total_replies": campaign.total_replies,
                    "total_meetings_booked": campaign.total_meetings_booked,
                    "created_at": campaign.created_at.isoformat() if campaign.created_at else None,
                }
            return None

    async def update_campaign_stats(self, campaign_id: int, stats: Dict):
        """Update campaign statistics"""
        async with self.get_session() as session:
            result = await session.execute(
                select(Campaign).where(Campaign.id == campaign_id)
            )
            campaign = result.scalar_one_or_none()

            if campaign:
                campaign.total_prospects = stats.get('total_prospects', 0)
                campaign.total_emails_sent = stats.get('total_emails_sent', 0)
                campaign.total_opens = stats.get('total_opens', 0)
                campaign.total_clicks = stats.get('total_clicks', 0)
                campaign.total_replies = stats.get('total_replies', 0)
                campaign.total_meetings_booked = stats.get('total_meetings_booked', 0)

                logger.info("campaign_stats_updated", campaign_id=campaign_id)

    # ==================== PROSPECTS ====================

    async def insert_prospect(self, campaign_id: int, prospect_data: Dict, analysis: Dict) -> int:
        """Insert analyzed prospect"""
        async with self.get_session() as session:
            prospect = Prospect(
                campaign_id=campaign_id,
                company_name=prospect_data['company_name'],
                domain=prospect_data.get('domain'),
                industry=prospect_data.get('industry'),
                employee_count=prospect_data.get('employee_count'),
                composite_score=analysis['composite_score'],
                priority_tier=analysis['priority_tier'],
                intent_score=analysis['scores']['intent'],
                technical_fit_score=analysis['scores']['technical_fit'],
                urgency_score=analysis['scores']['urgency'],
                annual_savings_potential=analysis['savings_projection']['annual_savings_dollars'],
                payback_months=analysis['savings_projection']['payback_period_months'],
                sustainability_maturity=analysis.get('sustainability_maturity', 2),
                intent_signals_json=json.dumps(analysis['intent_signals']),
                personalization_points_json=json.dumps(analysis['personalization_intel']['personalization_points']),
                analysis_status='analyzed',
                analyzed_at=datetime.now()
            )
            session.add(prospect)
            await session.flush()
            prospect_id = prospect.id

            logger.info("prospect_inserted",
                       prospect_id=prospect_id,
                       company=prospect_data['company_name'],
                       tier=analysis['priority_tier'])
            return prospect_id

    async def get_prospects_by_tier(self, campaign_id: int, tier: str) -> List[Dict]:
        """Get prospects by priority tier"""
        async with self.get_session() as session:
            result = await session.execute(
                select(Prospect)
                .where(and_(Prospect.campaign_id == campaign_id, Prospect.priority_tier == tier))
                .order_by(Prospect.composite_score.desc())
            )
            prospects = result.scalars().all()

            return [
                {
                    "id": p.id,
                    "company_name": p.company_name,
                    "composite_score": p.composite_score,
                    "annual_savings_potential": p.annual_savings_potential,
                }
                for p in prospects
            ]

    async def get_high_value_prospects(self, campaign_id: int, min_savings: float = 50000) -> List[Dict]:
        """Get high-value prospects"""
        async with self.get_session() as session:
            result = await session.execute(
                select(Prospect)
                .where(and_(
                    Prospect.campaign_id == campaign_id,
                    Prospect.annual_savings_potential >= min_savings
                ))
                .order_by(Prospect.annual_savings_potential.desc())
            )
            prospects = result.scalars().all()

            return [
                {
                    "id": p.id,
                    "company_name": p.company_name,
                    "annual_savings_potential": p.annual_savings_potential,
                    "priority_tier": p.priority_tier,
                }
                for p in prospects
            ]

    # ==================== EMAIL TRACKING ====================

    async def track_email_event(self, content_id: int, contact_id: int,
                               event_type: str, event_data: Optional[Dict] = None):
        """Track email event (open, click, reply)"""
        async with self.get_session() as session:
            # Create event
            event = EmailEvent(
                content_id=content_id,
                contact_id=contact_id,
                event_type=event_type,
                event_data=json.dumps(event_data) if event_data else None,
                timestamp=datetime.now()
            )
            session.add(event)

            # Update content record
            result = await session.execute(
                select(GeneratedContent).where(GeneratedContent.id == content_id)
            )
            content = result.scalar_one_or_none()

            if content:
                if event_type == 'opened':
                    content.opened_at = datetime.now()
                elif event_type == 'clicked':
                    content.clicked_at = datetime.now()
                elif event_type == 'replied':
                    content.replied_at = datetime.now()
                    content.status = 'replied'

                    # Update contact
                    contact_result = await session.execute(
                        select(Contact).where(Contact.id == contact_id)
                    )
                    contact = contact_result.scalar_one_or_none()
                    if contact:
                        contact.replied = True

            logger.info("email_event_tracked",
                       content_id=content_id,
                       event_type=event_type)

    # ==================== ANALYTICS ====================

    async def get_campaign_performance(self, campaign_id: int, days: int = 30) -> Dict:
        """Get campaign performance over time"""
        async with self.get_session() as session:
            start_date = datetime.now() - timedelta(days=days)

            result = await session.execute(
                select(
                    func.sum(PerformanceMetric.emails_sent).label('total_sent'),
                    func.sum(PerformanceMetric.emails_opened).label('total_opened'),
                    func.sum(PerformanceMetric.emails_clicked).label('total_clicked'),
                    func.sum(PerformanceMetric.emails_replied).label('total_replied'),
                    func.sum(PerformanceMetric.meetings_booked).label('total_meetings'),
                    func.avg(PerformanceMetric.open_rate).label('avg_open_rate'),
                    func.avg(PerformanceMetric.click_rate).label('avg_click_rate'),
                    func.avg(PerformanceMetric.reply_rate).label('avg_reply_rate'),
                    func.avg(PerformanceMetric.meeting_rate).label('avg_meeting_rate'),
                ).where(and_(
                    PerformanceMetric.campaign_id == campaign_id,
                    PerformanceMetric.metric_date >= start_date
                ))
            )

            row = result.one_or_none()
            if row:
                return {
                    "total_sent": row.total_sent or 0,
                    "total_opened": row.total_opened or 0,
                    "total_clicked": row.total_clicked or 0,
                    "total_replied": row.total_replied or 0,
                    "total_meetings": row.total_meetings or 0,
                    "avg_open_rate": row.avg_open_rate or 0,
                    "avg_click_rate": row.avg_click_rate or 0,
                    "avg_reply_rate": row.avg_reply_rate or 0,
                    "avg_meeting_rate": row.avg_meeting_rate or 0,
                }
            return {}


# ==================== BACKWARD COMPATIBILITY ====================

class TuneDatabase:
    """
    Backward-compatible wrapper that provides sync interface to async database
    WARNING: Only use for migration. Production code should use TuneDatabaseAsync directly.
    """

    def __init__(self, db_path: str = "tune_campaigns.db"):
        import asyncio
        self.async_db = TuneDatabaseAsync(f"sqlite+aiosqlite:///{db_path}")
        self.loop = asyncio.get_event_loop()
        self.loop.run_until_complete(self.async_db.init_db())

    def create_campaign(self, name: str, industry: str) -> int:
        return self.loop.run_until_complete(self.async_db.create_campaign(name, industry))

    def get_campaign(self, campaign_id: int) -> Optional[Dict]:
        return self.loop.run_until_complete(self.async_db.get_campaign(campaign_id))

    def track_email_event(self, content_id: int, contact_id: int, event_type: str, event_data: Optional[Dict] = None):
        return self.loop.run_until_complete(
            self.async_db.track_email_event(content_id, contact_id, event_type, event_data)
        )

    def get_campaign_performance(self, campaign_id: int, days: int = 30) -> Dict:
        return self.loop.run_until_complete(self.async_db.get_campaign_performance(campaign_id, days))

    # Add other methods as needed for compatibility...
    def get_prospects_by_tier(self, campaign_id: int, tier: str) -> List[Dict]:
        return self.loop.run_until_complete(self.async_db.get_prospects_by_tier(campaign_id, tier))
