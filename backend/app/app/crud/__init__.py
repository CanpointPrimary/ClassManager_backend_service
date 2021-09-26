from .crud_class import apply4class, class_, class_member, \
    group, group_member
from .crud_feedback import feedback
from .crud_page import homepage_menu, entrance_page
from .crud_school import school
from .crud_sys import region, sys_config
from .crud_subject import subject
from .crud_user import user

# For a new basic set of CRUD operations you could just do

# from .base import CRUDBase
# from app.models.item import Item
# from app.schemas.item import ItemCreate, ItemUpdate

# item = CRUDBase[Item, ItemCreate, ItemUpdate](Item)
