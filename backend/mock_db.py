"""
Mock Database Module - In-memory database for testing without MongoDB
This allows the app to run without requiring MongoDB to be installed or running
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
import json

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
    
    async def find(self, query: Dict = None, projection: Dict = None) -> List[Dict]:
        """Find multiple documents"""
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
        return results
    
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
        """Check if document matches query"""
        for key, value in query.items():
            if key not in doc:
                return False
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
