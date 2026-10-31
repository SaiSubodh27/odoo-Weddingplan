from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class EmailAttachmentResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

    id: str
    email_message_id: str = Field(..., alias="emailMessageId")
    original_filename: str = Field(..., alias="originalFilename")
    file_size: int = Field(..., alias="fileSize")
    mime_type: str = Field(..., alias="mimeType")
    created_at: datetime = Field(..., alias="createdAt")
    download_url: Optional[str] = Field(None, alias="downloadUrl")


class EmailMessageResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

    id: str
    enquiry_id: Optional[str] = Field(None, alias="enquiryId")
    direction: str
    sender_name: Optional[str] = Field(None, alias="senderName")
    sender_email: str = Field(..., alias="senderEmail")
    recipient_email: str = Field(..., alias="recipientEmail")
    subject: str
    body_text: Optional[str] = Field(None, alias="bodyText")
    body_html: Optional[str] = Field(None, alias="bodyHtml")
    message_id: Optional[str] = Field(None, alias="messageId")
    thread_id: Optional[str] = Field(None, alias="threadId")
    in_reply_to: Optional[str] = Field(None, alias="inReplyTo")
    status: str
    error_message: Optional[str] = Field(None, alias="errorMessage")
    received_at: Optional[datetime] = Field(None, alias="receivedAt")
    sent_at: Optional[datetime] = Field(None, alias="sentAt")
    created_at: datetime = Field(..., alias="createdAt")
    attachments: List[EmailAttachmentResponse] = []


class EmailListResponse(BaseModel):
    total: int
    items: List[EmailMessageResponse]


class EmailReplyRequest(BaseModel):
    subject: Optional[str] = None
    body: str = Field(..., min_length=1, description="Email reply text content")
    attach_registration_document: bool = Field(False, alias="attachRegistrationDocument")
    in_reply_to: Optional[str] = Field(None, alias="inReplyTo")


class EmailComposeRequest(BaseModel):
    to_email: str = Field(..., alias="toEmail")
    subject: str = Field(..., min_length=1)
    body: str = Field(..., min_length=1)
    enquiry_id: Optional[str] = Field(None, alias="enquiryId")
    attach_registration_document: bool = Field(False, alias="attachRegistrationDocument")


class EmailAssociateRequest(BaseModel):
    enquiry_id: str = Field(..., alias="enquiryId")


class EmailConvertToEnquiryRequest(BaseModel):
    client_name: Optional[str] = Field(None, alias="clientName")
    phone: Optional[str] = None
    wedding_date: Optional[str] = Field(None, alias="weddingDate")
    wedding_location: Optional[str] = Field(None, alias="weddingLocation")
    expected_guest_count: Optional[int] = Field(None, alias="expectedGuestCount")
    estimated_budget: Optional[str] = Field(None, alias="estimatedBudget")


class EmailSyncResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    success: bool
    status: str
    configured: bool
    messages_found: int = Field(0, alias="messagesFound")
    messages_processed: int = Field(0, alias="messagesProcessed")
    enquiries_created: int = Field(0, alias="enquiriesCreated")
    documents_received: int = Field(0, alias="documentsReceived")
    message: str
    errors: List[str] = []


class EmailStatusResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    imap_configured: bool = Field(..., alias="imapConfigured")
    smtp_configured: bool = Field(..., alias="smtpConfigured")
    agency_email: str = Field(..., alias="agencyEmail")
    imap_host: str = Field(..., alias="imapHost")
    smtp_host: Optional[str] = Field(None, alias="smtpHost")
    last_sync_at: Optional[datetime] = Field(None, alias="lastSyncAt")
    total_messages_received: int = Field(0, alias="totalMessagesReceived")
    total_unclassified: int = Field(0, alias="totalUnclassified")

