from fastapi import APIRouter, HTTPException

from app.auth.session import create_session
from app.config import DEMO_MODE
from app.data.store import store
from app.models.persona import ACTIVE_UI_PERSONA_ID, PERSONAS
from app.models.schemas import DevLoginRequest, LoginResponse, PersonaOut

router = APIRouter(tags=["auth"])


@router.post("/login", response_model=LoginResponse)
def login() -> LoginResponse:
    """The app has a single customer POV: this always logs in as that
    persona, regardless of any input — there is no persona picker."""
    persona = store.get(ACTIVE_UI_PERSONA_ID).persona
    token = create_session(persona.customer_id)
    return LoginResponse(
        session_token=token,
        customer_id=persona.customer_id,
        persona=PersonaOut(
            name=persona.name, age=persona.age,
            job_title=persona.job_title, city=persona.city,
        ),
    )


@router.post("/dev/login-as", response_model=LoginResponse)
def dev_login_as(body: DevLoginRequest) -> LoginResponse:
    """Demo/test-only backdoor, gated behind DEMO_MODE, used exclusively to
    mint a session for the hidden second customer so the security tests and
    scripts/demo_security_check.sh can prove cross-customer isolation. Never
    part of the real product surface — keep DEMO_MODE=false outside demos."""
    if not DEMO_MODE:
        raise HTTPException(status_code=404, detail="Not found")
    if body.customer_id not in PERSONAS:
        raise HTTPException(status_code=404, detail="Onbekende customer_id")

    persona = PERSONAS[body.customer_id]
    token = create_session(persona.customer_id)
    return LoginResponse(
        session_token=token,
        customer_id=persona.customer_id,
        persona=PersonaOut(
            name=persona.name, age=persona.age,
            job_title=persona.job_title, city=persona.city,
        ),
    )
