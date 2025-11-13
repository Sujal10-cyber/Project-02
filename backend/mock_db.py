"""
Mock Database Module - In-memory database for testing without MongoDB
This allows the app to run without requiring MongoDB to be installed or running
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
import json

class MockCursor:
    """Mock MongoDB cursor that supports to_list() and sort()"""
    def __init__(self, data: List[Dict]):
        self.data = data
    
    def sort(self, key_or_list, direction: int = 1):
        """Sort the cursor (chainable with to_list)"""
        if isinstance(key_or_list, str):
            # Single field sort
            reverse = direction < 0
            self.data = sorted(self.data, key=lambda x: x.get(key_or_list, ""), reverse=reverse)
        elif isinstance(key_or_list, list):
            # Multi-field sort
            for field, dir_val in reversed(key_or_list):
                reverse = dir_val < 0
                self.data = sorted(self.data, key=lambda x: x.get(field, ""), reverse=reverse)
        return self
    
    async def to_list(self, max_length: Optional[int] = None) -> List[Dict]:
        """Return all documents as a list (compatible with motor.motor_asyncio.AsyncCursor)"""
        if max_length is None:
            return self.data
        return self.data[:max_length]


class MockInsertOneResult:
    """Mock insert_one result"""
    def __init__(self, inserted_id):
        self.inserted_id = inserted_id


class MockInsertManyResult:
    """Mock insert_many result"""
    def __init__(self, inserted_ids):
        self.inserted_ids = inserted_ids


class MockUpdateResult:
    """Mock update result"""
    def __init__(self, modified_count):
        self.modified_count = modified_count


class MockDeleteResult:
    """Mock delete result"""
    def __init__(self, deleted_count):
        self.deleted_count = deleted_count


class MockCollection:
    """Mock MongoDB collection"""
    def __init__(self):
        self.data: Dict[str, Dict] = {}
        self.counter = 0
    
    async def insert_one(self, document: Dict[str, Any]) -> MockInsertOneResult:
        """Insert a single document"""
        if "_id" not in document:
            self.counter += 1
            document["_id"] = f"mock_id_{self.counter}"
        
        doc_id = str(document.get("_id", str(self.counter)))
        self.data[doc_id] = document.copy()
        
        return MockInsertOneResult(doc_id)
    
    async def insert_many(self, documents: List[Dict]) -> MockInsertManyResult:
        """Insert multiple documents"""
        ids = []
        for doc in documents:
            result = await self.insert_one(doc.copy())
            ids.append(result.inserted_id)
        
        return MockInsertManyResult(ids)
    
    async def find_one(self, query: Dict = None, projection: Dict = None) -> Optional[Dict]:
        """Find a single document"""
        if query is None:
            query = {}
        
        for doc in self.data.values():
            if self._matches_query(doc, query):
                result = dict(doc)
                if projection:
                    if "_id" in projection and projection["_id"] == 0:
                        result.pop("_id", None)
                return result
        return None
    
    def find(self, query: Dict = None, projection: Dict = None):
        """Find multiple documents - returns a MockCursor for compatibility with motor"""
        if query is None:
            query = {}
        
        results = []
        for doc in self.data.values():
            if self._matches_query(doc, query):
                result = dict(doc)
                if projection:
                    if "_id" in projection and projection["_id"] == 0:
                        result.pop("_id", None)
                results.append(result)
        return MockCursor(results)
    
    async def update_one(self, query: Dict, update: Dict) -> MockUpdateResult:
        """Update a single document"""
        for doc_id, doc in self.data.items():
            if self._matches_query(doc, query):
                if "$set" in update:
                    doc.update(update["$set"])
                else:
                    doc.update(update)
                
                return MockUpdateResult(1)
        
        return MockUpdateResult(0)
    
    async def delete_one(self, query: Dict) -> MockDeleteResult:
        """Delete a single document"""
        for doc_id, doc in list(self.data.items()):
            if self._matches_query(doc, query):
                del self.data[doc_id]
                return MockDeleteResult(1)
        
        return MockDeleteResult(0)
    
    async def count_documents(self, query: Dict = None) -> int:
        """Count documents matching query"""
        if query is None:
            query = {}
        
        count = 0
        for doc in self.data.values():
            if self._matches_query(doc, query):
                count += 1
        return count
    
    def _matches_query(self, doc: Dict, query: Dict) -> bool:
        """Check if document matches query - supports basic operators"""
        import re
        
        for key, value in query.items():
            # Handle special operators
            if key == "$or":
                # $or: at least one condition must match
                if not any(self._matches_query(doc, cond) for cond in value):
                    return False
                continue
            
            if key not in doc:
                return False
            
            # Handle complex queries with operators
            if isinstance(value, dict):
                doc_value = doc[key]
                for op, op_value in value.items():
                    if op == "$regex":
                        # Regex matching
                        pattern = re.compile(op_value, re.IGNORECASE)
                        if not isinstance(doc_value, str) or not pattern.search(doc_value):
                            return False
                    elif op == "$gte":
                        # Greater than or equal
                        if doc_value < op_value:
                            return False
                    elif op == "$lte":
                        # Less than or equal
                        if doc_value > op_value:
                            return False
                    elif op == "$gt":
                        # Greater than
                        if doc_value <= op_value:
                            return False
                    elif op == "$lt":
                        # Less than
                        if doc_value >= op_value:
                            return False
                    elif op == "$eq":
                        # Equal
                        if doc_value != op_value:
                            return False
                    elif op == "$ne":
                        # Not equal
                        if doc_value == op_value:
                            return False
                    elif op == "$in":
                        # In array
                        if doc_value not in op_value:
                            return False
            else:
                # Simple equality check
                if doc[key] != value:
                    return False
        
        return True


class MockDatabase:
    """Mock MongoDB database"""
    def __init__(self):
        self.collections: Dict[str, MockCollection] = {}
    
    def __getitem__(self, collection_name: str) -> MockCollection:
        """Get or create a collection"""
        if collection_name not in self.collections:
            self.collections[collection_name] = MockCollection()
        return self.collections[collection_name]
    
    def __getattr__(self, collection_name: str) -> MockCollection:
        """Get collection as attribute"""
        return self[collection_name]
    
    async def close(self):
        """Close database connection (no-op for mock)"""
        pass


# Export the mock database
def get_mock_db() -> MockDatabase:
    """Get mock database instance"""
    return MockDatabase()
