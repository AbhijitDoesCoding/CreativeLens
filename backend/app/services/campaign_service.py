from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.campaign import Campaign
from app.schemas.campaign import CampaignCreate

def create_campaign(db: Session, campaign_in: CampaignCreate) -> Campaign:
    campaign = Campaign(name=campaign_in.name)
    db.add(campaign)
    db.commit()
    db.refresh(campaign)
    return campaign

def get_campaigns(db: Session) -> List[Campaign]:
    return db.query(Campaign).order_by(Campaign.created_at.desc()).all()

def get_campaign(db: Session, campaign_id: str) -> Optional[Campaign]:
    return db.query(Campaign).filter(Campaign.id == campaign_id).first()
