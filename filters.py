import os

from aiogram import types
from aiogram.filters import BaseFilter
from dotenv import load_dotenv

load_dotenv()

ADMIN_IDS_STR = os.getenv("ADMIN_IDS")
ADMIN_IDS = {int(admin_id.strip()) for admin_id in ADMIN_IDS_STR.split(',')}


class IsAdmin(BaseFilter):
    """
    Custom filter to check if the user is an administrator.
    """
    def __init__(self):
        admin_ids = ADMIN_IDS.copy()
        self.admin_ids = admin_ids

    async def __call__(self, message: types.Message) -> bool:
        return message.from_user.id in self.admin_ids
