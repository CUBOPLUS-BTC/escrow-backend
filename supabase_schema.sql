-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Table for contracts
CREATE TABLE contracts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    buyer_pubkey TEXT NOT NULL,
    seller_pubkey TEXT NOT NULL,
    arbiter_pubkey TEXT NOT NULL,
    amount BIGINT NOT NULL,
    p2wsh_address TEXT NOT NULL,
    redeem_script TEXT NOT NULL,
    timelock_blocks INTEGER NOT NULL,
    status VARCHAR(50) DEFAULT 'pending', -- pending, funded, shipped, disputed, completed, refunded
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now())
);

-- Table for logistical documents
CREATE TABLE documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    contract_id UUID REFERENCES contracts(id) ON DELETE CASCADE,
    document_url TEXT NOT NULL,
    document_type VARCHAR(50) NOT NULL, -- e.g. proof_of_shipment
    uploaded_by VARCHAR(50) NOT NULL, -- e.g. seller
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now())
);

-- Table for storing PSBTs before combining
CREATE TABLE psbt_signatures (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    contract_id UUID REFERENCES contracts(id) ON DELETE CASCADE,
    psbt_base64 TEXT NOT NULL,
    signer_role VARCHAR(50) NOT NULL, -- buyer, seller, arbiter
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now())
);
