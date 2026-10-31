from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from app.database.base import Base


class UserAccount(Base):
    __tablename__ = "user_accounts"

    id = Column(String(50), primary_key=True, index=True)
    client_id = Column(String(50), ForeignKey("clients.id", ondelete="SET NULL"), nullable=True, unique=True, index=True)

    email = Column(String(255), nullable=False, unique=True, index=True)
    hashed_password = Column(String(255), nullable=True)  # Null while PENDING_ACTIVATION

    role = Column(String(50), nullable=False, default="client")  # 'client' | 'staff' | 'admin'
    status = Column(String(50), nullable=False, default="PENDING_ACTIVATION")  # 'PENDING_ACTIVATION' | 'ACTIVE' | 'SUSPENDED'
    is_active = Column(Boolean, nullable=False, default=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    client = relationship("Client", backref="user_account")
    activation_tokens = relationship("ActivationToken", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<UserAccount {self.id}: {self.email} ({self.status})>"


class ActivationToken(Base):
    __tablename__ = "activation_tokens"

    id = Column(String(50), primary_key=True, index=True)
    user_id = Column(String(50), ForeignKey("user_accounts.id", ondelete="CASCADE"), nullable=False, index=True)

    # Cryptographically secure SHA-256 hash of the one-time activation token
    token_hash = Column(String(64), nullable=False, unique=True, index=True)

    expires_at = Column(DateTime(timezone=True), nullable=False)
    is_used = Column(Boolean, nullable=False, default=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    user = relationship("UserAccount", back_populates="activation_tokens")

    def __repr__(self):
        return f"<ActivationToken {self.id} for user {self.user_id}>"
