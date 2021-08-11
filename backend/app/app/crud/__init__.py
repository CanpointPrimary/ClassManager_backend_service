from .crud_class import class_, class_member
from .crud_page import homepage_menu, slideshow
from .crud_sys import region, sys_config
from .crud_subject import subject
from .crud_user import user

# For a new basic set of CRUD operations you could just do

# from .base import CRUDBase
# from app.models.item import Item
# from app.schemas.item import ItemCreate, ItemUpdate

# item = CRUDBase[Item, ItemCreate, ItemUpdate](Item)
