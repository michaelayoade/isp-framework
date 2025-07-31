"""
Knowledge Base Models
Knowledge base for common issues and solutions
"""

from sqlalchemy import (
    ARRAY,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class KnowledgeBaseArticle(Base):
    """Knowledge base for common issues and solutions"""

    __tablename__ = "knowledge_base_articles"

    id = Column(Integer, primary_key=True, index=True)

    # Article Content
    title = Column(String(255), nullable=False, index=True)
    summary = Column(String(500))
    content = Column(Text, nullable=False)
    content_format = Column(String(20), default="html")  # html, markdown, text

    # Classification
    category = Column(String(100), index=True)
    subcategory = Column(String(100))
    tags = Column(ARRAY(String), default=[])
    keywords = Column(ARRAY(String), default=[])

    # Applicability
    ticket_types = Column(
        ARRAY(String), default=[]
    )  # Which ticket types this helps with
    service_types = Column(ARRAY(String), default=[])  # Internet, Voice, etc.
    difficulty_level = Column(String(50))  # beginner, intermediate, advanced

    # Content Management
    author_id = Column(Integer, ForeignKey("administrators.id"))
    reviewer_id = Column(Integer, ForeignKey("administrators.id"))

    # Status
    status = Column(
        String(50), default="draft", index=True
    )  # draft, review, published, archived
    is_public = Column(Boolean, default=False)  # Visible to customers

    # Usage Statistics
    view_count = Column(Integer, default=0)
    helpful_votes = Column(Integer, default=0)
    not_helpful_votes = Column(Integer, default=0)

    # Versioning
    version = Column(String(20), default="1.0")
    previous_version_id = Column(Integer, ForeignKey("knowledge_base_articles.id"))

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    published_at = Column(DateTime(timezone=True))

    # Relationships
    author = relationship("Administrator", foreign_keys=[author_id])
    reviewer = relationship("Administrator", foreign_keys=[reviewer_id])
    previous_version = relationship("KnowledgeBaseArticle", remote_side=[id])

    @property
    def helpfulness_ratio(self):
        """Calculate how helpful this article is"""
        total_votes = self.helpful_votes + self.not_helpful_votes
        if total_votes == 0:
            return 0
        return round((self.helpful_votes / total_votes) * 100, 1)
