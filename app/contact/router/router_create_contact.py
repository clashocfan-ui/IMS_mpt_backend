import os
from typing import Optional
from fastapi import Depends, HTTPException, status, Form, File, UploadFile
from datetime import datetime, timezone
from pydantic_core import ValidationError
from app.auth.schema import Branch
import time
from app.contact.contact_service import ContactService, get_contact_service
from app.contact.schema import Contact
from app.contact.utils import delete_file, handle_upload
from app.utils import env
from . import router


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=Contact,
)
def create_contact(
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
) -> Contact:
    new_filename = ""
    unix_time = int(time.time())

    if file:
        _, ext = os.path.splitext(file.filename)
        new_filename = f"image_{unix_time}{ext}"
        handle_upload(new_filename=new_filename, file=file)
    try:
        payload = Contact(
            name=name,
            personal_number=personal_number,
            office_number=office_number,
            gstin=gstin,
            email=email,
            address=address,
            pincode=pincode,
            company_name=company_name,
            address_proof=new_filename,
            remarks=remarks,
            branch=branch,
            created_at=datetime.fromtimestamp(timestamp=unix_time, tz=timezone.utc),
        )
    except ValidationError as e:
        print(e)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Pydantic Validation Error. Please contact the developer. ${e}",
        )
    contact_data = svc.repository.create_contact(contact=payload)

    if not contact_data:
        delete_file(filename=new_filename)
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
        delete_file(filename=new_filename)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Pydantic Validation Error. Please contact the developer.",
        )
