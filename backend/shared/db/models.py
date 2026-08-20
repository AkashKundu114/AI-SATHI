from __future__ import annotations 

import uuid 
from datetime import datetime 

from sqlalchemy import (
ForeignKey ,
String ,
Numeric ,
Boolean ,
Text ,
Integer ,
ARRAY ,
JSON ,
DateTime ,
UniqueConstraint ,
)

from sqlalchemy .orm import DeclarativeBase ,Mapped ,mapped_column 

class Base (DeclarativeBase ):
    pass 

class SHGGroup (Base ):
    __tablename__ ="shg_groups"

    id :Mapped [uuid .UUID ]=mapped_column (primary_key =True ,default =uuid .uuid4 )
    name :Mapped [str ]=mapped_column (String (255 ),nullable =False )
    district :Mapped [str |None ]=mapped_column (String (100 ))
    block :Mapped [str |None ]=mapped_column (String (100 ))
    grade_level :Mapped [int |None ]=mapped_column (Integer )
    total_members :Mapped [int |None ]=mapped_column (Integer )
    bank_linkage_status :Mapped [str |None ]=mapped_column (String (50 ))
    created_at :Mapped [datetime ]=mapped_column (
    DateTime (timezone =True ),default =datetime .utcnow 
    )

class User (Base ):
    __tablename__ ="users"

    id :Mapped [uuid .UUID ]=mapped_column (primary_key =True ,default =uuid .uuid4 )
    whatsapp_number :Mapped [str ]=mapped_column (
    String (20 ),unique =True ,nullable =False 
    )
    name :Mapped [str |None ]=mapped_column (String (255 ))
    shg_id :Mapped [uuid .UUID |None ]=mapped_column (ForeignKey ("shg_groups.id"))
    district :Mapped [str |None ]=mapped_column (String (100 ))
    block :Mapped [str |None ]=mapped_column (String (100 ))
    consent_given :Mapped [bool ]=mapped_column (Boolean ,default =False )
    consent_given_at :Mapped [datetime |None ]=mapped_column (DateTime (timezone =True ))
    onboarded_at :Mapped [datetime ]=mapped_column (
    DateTime (timezone =True ),default =datetime .utcnow 
    )
    last_active_at :Mapped [datetime |None ]=mapped_column (DateTime (timezone =True ))

    business_categories :Mapped [list [str ]|None ]=mapped_column (ARRAY (String ).with_variant (JSON ,"sqlite"))

    self_reported_literacy :Mapped [str |None ]=mapped_column (String (30 ))
    preferred_modality :Mapped [str ]=mapped_column (String (10 ),default ="voice")
    dialect_hint :Mapped [str |None ]=mapped_column (String (30 ))
    ledger_correction_rate :Mapped [float ]=mapped_column (Numeric (4 ,3 ),default =0.0 )
    sessions_count :Mapped [int ]=mapped_column (Integer ,default =0 )
    trust_stage :Mapped [str ]=mapped_column (String (15 ),default ="new")

    verification_status :Mapped [str ]=mapped_column (String (20 ),default ="unverified")
    user_type :Mapped [str |None ]=mapped_column (String (30 ))
    plan_tier :Mapped [str |None ]=mapped_column (String (20 ),default ="free")
    plan_expires :Mapped [datetime |None ]=mapped_column (DateTime (timezone =True ))

class UserVerification (Base ):
    __tablename__ ="user_verifications"

    id :Mapped [uuid .UUID ]=mapped_column (primary_key =True ,default =uuid .uuid4 )
    user_id :Mapped [uuid .UUID ]=mapped_column (ForeignKey ("users.id"),nullable =False )
    doc_type :Mapped [str ]=mapped_column (String (100 ),nullable =False )
    doc_id_number :Mapped [str |None ]=mapped_column (String (100 ))
    doc_image_s3_key :Mapped [str |None ]=mapped_column (String (500 ))
    status :Mapped [str ]=mapped_column (String (20 ),default ="pending")
    submitted_at :Mapped [datetime ]=mapped_column (
    DateTime (timezone =True ),default =datetime .utcnow 
    )
    reviewed_at :Mapped [datetime |None ]=mapped_column (DateTime (timezone =True ))
    reviewer_notes :Mapped [str |None ]=mapped_column (Text )

class LedgerEntry (Base ):
    __tablename__ ="ledger_entries"

    id :Mapped [uuid .UUID ]=mapped_column (primary_key =True ,default =uuid .uuid4 )
    user_id :Mapped [uuid .UUID ]=mapped_column (ForeignKey ("users.id"),nullable =False )
    entry_date :Mapped [datetime ]=mapped_column (
    DateTime (timezone =True ),default =datetime .utcnow 
    )
    entry_type :Mapped [str ]=mapped_column (String (10 ))
    amount_inr :Mapped [float ]=mapped_column (Numeric (10 ,2 ),nullable =False )
    category :Mapped [str |None ]=mapped_column (String (100 ))
    description_bengali :Mapped [str |None ]=mapped_column (Text )
    quantity :Mapped [float |None ]=mapped_column (Numeric (10 ,2 ))
    unit :Mapped [str |None ]=mapped_column (String (20 ))
    raw_transcript :Mapped [str |None ]=mapped_column (Text )
    is_corrected :Mapped [bool ]=mapped_column (Boolean ,default =False )
    correction_of :Mapped [uuid .UUID |None ]=mapped_column (
    ForeignKey ("ledger_entries.id")
    )
    extracted_by :Mapped [str |None ]=mapped_column (String (20 ))
    created_at :Mapped [datetime ]=mapped_column (
    DateTime (timezone =True ),default =datetime .utcnow 
    )

class CatalogCreation (Base ):
    __tablename__ ="catalog_creations"

    id :Mapped [uuid .UUID ]=mapped_column (primary_key =True ,default =uuid .uuid4 )
    user_id :Mapped [uuid .UUID ]=mapped_column (ForeignKey ("users.id"),nullable =False )
    raw_image_s3_key :Mapped [str ]=mapped_column (String (500 ),nullable =False )
    processed_image_s3_key :Mapped [str |None ]=mapped_column (String (500 ))
    product_type :Mapped [str |None ]=mapped_column (String (100 ))
    caption_bengali :Mapped [str |None ]=mapped_column (Text )
    ad_caption_bengali :Mapped [str |None ]=mapped_column (Text )
    price_suggestion_min :Mapped [float |None ]=mapped_column (Numeric (10 ,2 ))
    price_suggestion_max :Mapped [float |None ]=mapped_column (Numeric (10 ,2 ))
    vision_model_used :Mapped [str |None ]=mapped_column (String (30 ))

    user_reported_shared :Mapped [bool |None ]=mapped_column (Boolean )
    user_reported_sale_resulted :Mapped [bool |None ]=mapped_column (Boolean )
    created_at :Mapped [datetime ]=mapped_column (
    DateTime (timezone =True ),default =datetime .utcnow 
    )

class MarketPrice (Base ):
    __tablename__ ="market_prices"

    time :Mapped [datetime ]=mapped_column (DateTime (timezone =True ),primary_key =True )
    block :Mapped [str ]=mapped_column (String (100 ),primary_key =True )
    district :Mapped [str |None ]=mapped_column (String (100 ))
    product_category :Mapped [str ]=mapped_column (String (100 ),primary_key =True )
    avg_price_inr_per_unit :Mapped [float |None ]=mapped_column (Numeric (8 ,2 ))
    unit :Mapped [str |None ]=mapped_column (String (20 ))
    data_source :Mapped [str ]=mapped_column (String (20 ),primary_key =True )
    sample_count :Mapped [int |None ]=mapped_column (Integer )
    demand_score :Mapped [float |None ]=mapped_column (Numeric (3 ,2 ))

class SellerProfile (Base ):

    __tablename__ ="seller_profiles"

    user_id :Mapped [uuid .UUID ]=mapped_column (ForeignKey ("users.id"),primary_key =True )
    product_type :Mapped [str |None ]=mapped_column (String (100 ))
    production_cost :Mapped [float |None ]=mapped_column (Numeric (10 ,2 ))
    preferred_margin :Mapped [float ]=mapped_column (Numeric (4 ,3 ),default =0.30 )
    minimum_price :Mapped [float |None ]=mapped_column (Numeric (10 ,2 ))
    monthly_sales :Mapped [int ]=mapped_column (Integer ,default =0 )
    inventory :Mapped [int ]=mapped_column (Integer ,default =0 )
    updated_at :Mapped [datetime ]=mapped_column (
    DateTime (timezone =True ),default =datetime .utcnow 
    )

class ApiUsageMonthly (Base ):
    __tablename__ ="api_usage_monthly"

    user_id :Mapped [uuid .UUID ]=mapped_column (primary_key =True )
    provider :Mapped [str ]=mapped_column (String (30 ),primary_key =True )
    month_bucket :Mapped [str ]=mapped_column (String (7 ),primary_key =True )
    call_count :Mapped [int ]=mapped_column (Integer ,default =1 )

class UserPlan (Base ):
    __tablename__ ="user_plans"

    user_id :Mapped [uuid .UUID ]=mapped_column (ForeignKey ("users.id"),primary_key =True )
    plan_tier :Mapped [str ]=mapped_column (String (20 ),default ="free")
    plan_expires :Mapped [datetime |None ]=mapped_column (DateTime (timezone =True ))
    upgraded_at :Mapped [datetime |None ]=mapped_column (DateTime (timezone =True ))
    payment_ref :Mapped [str |None ]=mapped_column (String (255 ))
    created_at :Mapped [datetime ]=mapped_column (
    DateTime (timezone =True ),default =datetime .utcnow 
    )

class UserOTP (Base ):
    __tablename__ ="user_otps"

    phone :Mapped [str ]=mapped_column (String (20 ),primary_key =True )
    otp :Mapped [str ]=mapped_column (String (6 ),nullable =False )
    expires_at :Mapped [datetime ]=mapped_column (DateTime (timezone =True ),nullable =False )
    created_at :Mapped [datetime ]=mapped_column (
    DateTime (timezone =True ),default =datetime .utcnow 
    )

class UploadedDocument (Base ):
    __tablename__ ="uploaded_documents"
    __table_args__ =(
    UniqueConstraint ('user_phone','filename',name ='_user_filename_uc'),
    )

    id :Mapped [uuid .UUID ]=mapped_column (primary_key =True ,default =uuid .uuid4 )
    user_phone :Mapped [str ]=mapped_column (String (20 ),nullable =False )
    filename :Mapped [str ]=mapped_column (String (255 ),nullable =False )
    title :Mapped [str |None ]=mapped_column (String (255 ))
    size_bytes :Mapped [int |None ]=mapped_column (Integer )
    text_content :Mapped [str |None ]=mapped_column (Text )
    blob_url :Mapped [str |None ]=mapped_column (String (500 ))
    created_at :Mapped [datetime ]=mapped_column (
    DateTime (timezone =True ),default =datetime .utcnow 
    )

