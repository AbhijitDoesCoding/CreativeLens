from datetime import datetime, timezone
import pytest
from app.models.campaign import Campaign
from app.models.asset import Asset
from app.models.model import Model
from app.models.inference_run import InferenceRun
from app.schemas.inference_run import InferenceRunResponse

def test_create_inference_run_db_record(db_session):
    """Test creating an InferenceRun model in SQLite with foreign keys and telemetry."""
    campaign = Campaign(name="Inference Test Campaign")
    db_session.add(campaign)
    db_session.commit()

    asset = Asset(
        campaign_id=campaign.id,
        filename="creative_ad.png",
        file_path="data/campaigns/c1/assets/creative_ad.png",
        media_type="image",
        mime_type="image/png",
        file_size=10240,
    )
    db_session.add(asset)

    model = Model(
        name="Mock Vision v1",
        provider="mock",
        model_key="mock-vision-v1",
        enabled=True,
    )
    db_session.add(model)
    db_session.commit()

    run = InferenceRun(
        asset_id=asset.id,
        model_id=model.id,
        status="completed",
        response_text="Save 20% on Colgate SBW",
        context_json={"brand": "Colgate", "offer": "20% Off"},
        started_at=datetime.now(timezone.utc),
        completed_at=datetime.now(timezone.utc),
        latency_ms=850,
        ttft_ms=320,
        input_tokens=400,
        output_tokens=65,
        estimated_cost_usd=0.0003,
        raw_output={"mock": True},
    )
    db_session.add(run)
    db_session.commit()
    db_session.refresh(run)

    assert run.id is not None
    assert len(run.id) == 36
    assert run.status == "completed"
    assert run.latency_ms == 850
    assert run.input_tokens == 400
    assert run.context_json["brand"] == "Colgate"
    assert run.response_text == "Save 20% on Colgate SBW"

    # Relationships
    assert run.asset.id == asset.id
    assert run.model.id == model.id
    assert len(asset.inference_runs) == 1
    assert asset.inference_runs[0].id == run.id
    assert len(model.inference_runs) == 1
    assert model.inference_runs[0].id == run.id

def test_inference_run_defaults_and_status_transitions(db_session):
    """Test default values and updating status."""
    campaign = Campaign(name="Status Campaign")
    db_session.add(campaign)
    db_session.commit()

    asset = Asset(
        campaign_id=campaign.id,
        filename="video.mp4",
        file_path="data/campaigns/c1/assets/video.mp4",
        media_type="video",
        mime_type="video/mp4",
        file_size=500000,
    )
    model = Model(name="Test Model", provider="test", model_key="t-1")
    db_session.add_all([asset, model])
    db_session.commit()

    run = InferenceRun(asset_id=asset.id, model_id=model.id)
    db_session.add(run)
    db_session.commit()
    db_session.refresh(run)

    assert run.status == "pending"
    assert run.latency_ms is None
    assert run.response_text is None

    # Transition to running
    run.status = "running"
    run.started_at = datetime.now(timezone.utc)
    db_session.commit()
    db_session.refresh(run)
    assert run.status == "running"

    # Transition to failed
    run.status = "failed"
    run.error_message = "Simulated adapter timeout"
    db_session.commit()
    db_session.refresh(run)
    assert run.status == "failed"
    assert run.error_message == "Simulated adapter timeout"

def test_inference_run_cascade_delete(db_session):
    """Deleting an asset or model cascades and deletes associated inference runs."""
    campaign = Campaign(name="Cascade Campaign")
    db_session.add(campaign)
    db_session.commit()

    asset = Asset(
        campaign_id=campaign.id,
        filename="img.png",
        file_path="data/img.png",
        media_type="image",
        mime_type="image/png",
        file_size=100,
    )
    model = Model(name="Cascade Model", provider="test", model_key="c-1")
    db_session.add_all([asset, model])
    db_session.commit()

    run = InferenceRun(asset_id=asset.id, model_id=model.id)
    db_session.add(run)
    db_session.commit()

    run_id = run.id

    # Delete asset -> run should be deleted
    db_session.delete(asset)
    db_session.commit()

    assert db_session.query(InferenceRun).filter(InferenceRun.id == run_id).first() is None
