from pydantic import BaseModel, ConfigDict


class BaseDTO(BaseModel):
    model_config = ConfigDict(
        extra="ignore",
        validate_default=True,
        from_attributes=True,
        validate_assignment=True,
        arbitrary_types_allowed=True
    )
