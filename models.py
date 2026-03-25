from pydantic import BaseModel
from typing import Optional

class IssueBase(BaseModel):
    title: str
    description: str
    area: str
    latitude: Optional[str] = None
    longitude: Optional[str] = None

class IssueCreate(IssueBase):
    pass

class Issue(IssueBase):
    id: int
    status: str
    image_filename: Optional[str] = None
    resolved_image_filename: Optional[str] = None
    upvote_count: int
    created_at: str

    class Config:
        from_attributes = True

class Admin(BaseModel):
    username: str
