"""Opt-in live Step 4 verification: python -m scripts.verify_step4."""
import asyncio
import json

from fastapi.testclient import TestClient

from app.core.config import MODEL_NAME
from app.main import app
from app.services.repair import repair_skill, validate_draft
from app.models import GeneratedSkillDraft


def main():
    if MODEL_NAME != "qwen2.5:3b":
        raise RuntimeError("Step 4 verification requires local qwen2.5:3b.")
    client = TestClient(app)
    workflow = {"workflow": "Read meeting notes and extract decisions, action items, owners, and deadlines."}
    generated = client.post("/api/generate", json=workflow)
    generated.raise_for_status()
    skill = GeneratedSkillDraft.model_validate(generated.json())
    validation = validate_draft(skill)
    print(json.dumps({"generated_name": skill.name, "validation": validation.model_dump()}), flush=True)
    assert validation.valid

    invalid = skill.model_copy(update={"name": "meeting_action_extractor"})
    before_validation = validate_draft(invalid)
    assert not before_validation.valid
    result = asyncio.run(repair_skill(invalid))
    print(json.dumps({
        "before_name": invalid.name,
        "errors_before": [e.model_dump() for e in before_validation.errors],
        "repaired_name": result.final_skill.name,
        "attempts": len(result.repair_attempts),
        "final_validation": result.final_validation.model_dump(),
    }), flush=True)
    assert result.final_valid

    response = client.post("/api/generate-and-repair", json=workflow)
    response.raise_for_status()
    body = response.json()
    print(json.dumps({"endpoint_status": response.status_code, "final_valid": body["final_valid"],
                      "attempts": len(body["repair_attempts"])}), flush=True)
    assert body["final_valid"] and body["skill_md"]
    assert client.get("/health").status_code == 200
    assembled = client.post("/api/assemble", json=skill.model_dump())
    assert assembled.status_code == 200 and assembled.json()["validation"]["valid"]
    print("Existing endpoints: health, generate, assemble passed with real generated data.", flush=True)


if __name__ == "__main__":
    main()
