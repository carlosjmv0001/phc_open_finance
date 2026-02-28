from pydantic import BaseModel, Field, field_validator  
from typing import Optional  
import time  
  
class CredentialAttributes(BaseModel):  
    person_hash: str = Field(..., min_length=8, max_length=128)  
    biometric_score: str = Field(..., pattern=r'^\d{1,3}(\.\d)?$')  
    timestamp: str = Field(default_factory=lambda: str(int(time.time())))  
    controller_did: str = Field(..., pattern=r'^did:sov:[a-zA-Z0-9]+$')  
  
    @field_validator('biometric_score')  
    @classmethod  
    def validate_score(cls, v):  
        score = float(v)  
        if not 0 <= score <= 100:  
            raise ValueError('Score must be between 0 and 100')  
        return v  
  
class ProofRequest(BaseModel):  
    connection_id: str  
    presentation_request: dict  
  
    @field_validator('connection_id')  
    @classmethod  
    def validate_connection_id(cls, v):  
        if not v or len(v) < 10:  
            raise ValueError('Invalid connection ID')  
        return v