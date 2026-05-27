from datetime import datetime, timezone
import os
import time
from typing import Optional
from fastapi import Depends, Form, UploadFile, File, HTTPException, status
from pydantic_core import ValidationError
from app.auth.schema import Branch

from app.contact.contact_service import ContactService, get_contact_service
from app.contact.schema import Contact
from app.contact.utils import handle_upload
from app.utils import env
from . import router


@router.put(
    "/{id}",
    response_model=Contact,
)
async def update_contact(
    id: str,
    name: str = Form(...),
    personal_number: str = Form(...),
    office_number: Optional[str] = Form(default=""),
    gstin: Optional[str] = Form(default=""),
    email: Optional[str] = Form(default=""),
    address: Optional[str] = Form(default=""),
    pincode: Optional[str] = Form(default=""),
    company_name: Optional[str] = Form(default=""),
    address_proof: Optional[str] = Form(default=""),
    remarks: str = Form(default=""),
    branch: Branch = Form(default=Branch.PADUR),
    file: Optional[UploadFile] = File(None),
    svc: ContactService = Depends(get_contact_service),
):
    unix_time = int(time.time())
    if file:
        _, ext = os.path.splitext(file.filename)
        filename = f"image_{unix_time}{ext}"
        handle_upload(new_filename=filename, file=file)
    else:
        filename = os.path.basename(address_proof) if address_proof else ""

    payload = Contact(
        name=name,
        personal_number=personal_number,
        office_number=office_number,
        gstin=gstin,
        email=email,
        address=address,
        pincode=pincode,
        company_name=company_name,
        address_proof=filename,
        remarks=remarks,
        branch=branch,
        created_at=datetime.fromtimestamp(timestamp=unix_time, tz=timezone.utc),
    )

    contact_data = svc.repository.update_contact(contact_id=id, contact=payload)
    svc.order_repository.update_rental_orders_contact_info(
        contact_id=id, customer=payload
    )

    if not contact_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="The Contact was not created"
        )

    try:
        if contact_data.get("address_proof"):
            contact_data["address_proof"] = (
                f"{env.image_domain}/public/contact/{contact_data['address_proof']}"
            )
        contact_data = Contact(**contact_data)
        return contact_data
    except ValidationError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Pydantic Validation Error. Please contact the developer.",
        )
