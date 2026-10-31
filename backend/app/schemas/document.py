from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class DocumentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: str
    enquiry_id: str = Field(..., alias="enquiryId")
    client_id: Optional[str] = Field(None, alias="clientId")
    document_type: str = Field(..., alias="documentType")
    original_filename: str = Field(..., alias="originalFilename")
    file_size: int = Field(..., alias="fileSize")
    mime_type: str = Field(..., alias="mimeType")
    uploaded_by: str = Field(..., alias="uploadedBy")
    is_reviewed: bool = Field(False, alias="isReviewed")
    reviewed_by: Optional[str] = Field(None, alias="reviewedBy")
    reviewed_at: Optional[datetime] = Field(None, alias="reviewedAt")
    created_at: datetime = Field(..., alias="createdAt")
    download_url: Optional[str] = Field(None, alias="downloadUrl")


class DocumentListResponse(BaseModel):
    total: int
    items: List[DocumentResponse]
