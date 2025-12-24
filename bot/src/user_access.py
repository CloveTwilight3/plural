from pathlib import Path
from typing import Literal
from asyncio import Lock
import json

from plural.otel import span


class UserAccessManager:
    def __init__(self, file_path: str = 'data/allowed_users.json'):
        self.file_path = Path(file_path)
        self.lock = Lock()
        self._ensure_file_exists()
    
    def _ensure_file_exists(self) -> None:
        """Create the file with default values if it doesn't exist"""
        if not self.file_path.exists():
            self.file_path.parent.mkdir(parents=True, exist_ok=True)
            self._write_data({
                'allowed_users': [],
                'mode': 'blacklist'
            })
    
    def _read_data(self) -> dict:
        """Read the JSON file"""
        with open(self.file_path, 'r') as f:
            return json.load(f)
    
    def _write_data(self, data: dict) -> None:
        """Write to the JSON file"""
        with open(self.file_path, 'w') as f:
            json.dump(data, f, indent=2)
    
    async def is_user_allowed(self, user_id: int) -> bool:
        """Check if a user is allowed to use the bot"""
        async with self.lock:
            data = self._read_data()
            mode = data.get('mode', 'blacklist')
            users = set(data.get('allowed_users', []))
            
            if mode == 'blacklist':
                # Everyone allowed except blacklisted users
                return user_id not in users
            else:  # whitelist
                # Only whitelisted users allowed
                return user_id in users
    
    async def add_user(self, user_id: int) -> bool:
        """Add a user to the list. Returns True if added, False if already exists"""
        async with self.lock:
            data = self._read_data()
            users = data.get('allowed_users', [])
            
            if user_id in users:
                return False
            
            users.append(user_id)
            data['allowed_users'] = users
            self._write_data(data)
            return True
    
    async def remove_user(self, user_id: int) -> bool:
        """Remove a user from the list. Returns True if removed, False if not found"""
        async with self.lock:
            data = self._read_data()
            users = data.get('allowed_users', [])
            
            if user_id not in users:
                return False
            
            users.remove(user_id)
            data['allowed_users'] = users
            self._write_data(data)
            return True
    
    async def get_mode(self) -> Literal['blacklist', 'whitelist']:
        """Get the current mode"""
        async with self.lock:
            data = self._read_data()
            return data.get('mode', 'blacklist')
    
    async def set_mode(self, mode: Literal['blacklist', 'whitelist']) -> None:
        """Set the mode"""
        async with self.lock:
            data = self._read_data()
            data['mode'] = mode
            self._write_data(data)
    
    async def list_users(self) -> list[int]:
        """Get the list of users"""
        async with self.lock:
            data = self._read_data()
            return data.get('allowed_users', [])
    
    async def clear_users(self) -> int:
        """Clear all users. Returns the count of removed users"""
        async with self.lock:
            data = self._read_data()
            count = len(data.get('allowed_users', []))
            data['allowed_users'] = []
            self._write_data(data)
            return count


# Global instance
user_access_manager = UserAccessManager()