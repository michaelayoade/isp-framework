"""Search schemas for global search functionality."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime


class SearchResult(BaseModel):
    """Individual search result item."""
    id: int = Field(..., description="Entity ID")
    title: str = Field(..., description="Primary display text")
    subtitle: str = Field(..., description="Secondary display text (type/category)")
    description: str = Field(..., description="Additional context/details")
    category: str = Field(..., description="Result category (customers, services, devices, etc.)")
    url: str = Field(..., description="Frontend navigation URL")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional entity-specific data")

    class Config:
        from_attributes = True


class GlobalSearchResponse(BaseModel):
    """Global search response with categorized results."""
    query: str = Field(..., description="Original search query")
    total_results: int = Field(..., description="Total number of results across all categories")
    categories: List[str] = Field(..., description="Categories with results")
    results: Dict[str, List[SearchResult]] = Field(..., description="Results grouped by category")
    searched_at: datetime = Field(default_factory=datetime.utcnow, description="Search timestamp")

    class Config:
        from_attributes = True


class SearchSuggestion(BaseModel):
    """Search suggestion for autocomplete."""
    text: str = Field(..., description="Suggested search text")
    category: str = Field(..., description="Suggestion category")
    count: int = Field(..., description="Number of potential results")

    class Config:
        from_attributes = True


class SearchSuggestionsResponse(BaseModel):
    """Search suggestions response for autocomplete."""
    query: str = Field(..., description="Partial search query")
    suggestions: List[SearchSuggestion] = Field(..., description="Search suggestions")

    class Config:
        from_attributes = True
