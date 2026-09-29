from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models import Address, User
from app.schemas import AddressIn, AddressOut, UserOut, UserUpdate

router = APIRouter(prefix="/api/users/me", tags=["users"])


@router.get("", response_model=UserOut)
def profile(user: User = Depends(get_current_user)):
    return user


@router.put("", response_model=UserOut)
def update_profile(payload: UserUpdate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if payload.full_name:
        user.full_name = payload.full_name
        db.commit()
        db.refresh(user)
    return user


@router.get("/addresses", response_model=list[AddressOut])
def list_addresses(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.query(Address).filter(Address.user_id == user.id).all()


@router.post("/addresses", response_model=AddressOut)
def add_address(payload: AddressIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if payload.is_default:
        db.query(Address).filter(Address.user_id == user.id).update({"is_default": False})
    addr = Address(user_id=user.id, **payload.model_dump())
    db.add(addr)
    db.commit()
    db.refresh(addr)
    return addr


@router.delete("/addresses/{address_id}")
def delete_address(address_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    addr = db.query(Address).filter(Address.id == address_id, Address.user_id == user.id).first()
    if not addr:
        raise HTTPException(status_code=404, detail="Address not found")
    db.delete(addr)
    db.commit()
    return {"ok": True}
