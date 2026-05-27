from pydantic_core import ValidationError
from app.contact.contact_service import ContactService, get_contact_service
from app.contact.schema import Contact
from app.utils import env
from . import router
from fastapi import Depends, HTTPException, status


@router.get("/{id}", status_code=status.HTTP_200_OK, response_model=Contact)
def get_contact_by_id(
    id: str, svc: ContactService = Depends(get_contact_service)
) -> Contact:
    contact_data = svc.repository.get_contact_by_id(contact_id=id)
    if not contact_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="The Contact is not found"
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
            detail="Pydantic Validation Error. Please Contact Admin or Developer.",
        )
