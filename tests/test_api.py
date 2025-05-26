
import pytest
import asyncio
from httpx import AsyncClient
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api import app

class TestTradingAPI:
    """Test cases for Trading API"""
    
    @pytest.fixture
    async def client(self):
        """Create test client"""
        async with AsyncClient(app=app, base_url="http://test") as ac:
            yield ac
    
    @pytest.mark.asyncio
    async def test_root_endpoint(self, client):
        """Test root endpoint"""
        response = await client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "message" in data
        assert "version" in data
        assert "endpoints" in data
        assert data["message"] == "Trading Signals API"
    
    @pytest.mark.asyncio
    async def test_health_endpoint(self, client):
        """Test health check endpoint"""
        response = await client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "status" in data
        assert "timestamp" in data
        assert data["status"] in ["healthy", "degraded", "unhealthy"]
    
    @pytest.mark.asyncio
    async def test_status_endpoint(self, client):
        """Test status endpoint"""
        response = await client.get("/status")
        
        # Response should be either 200 (with data) or 500 (no data)
        assert response.status_code in [200, 500]
        
        if response.status_code == 200:
            data = response.json()
            assert "status" in data
            assert "pair" in data or "status" in data
    
    @pytest.mark.asyncio
    async def test_signal_endpoint(self, client):
        """Test signal endpoint"""
        response = await client.get("/signal")
        
        # Should return either signal data or error
        assert response.status_code in [200, 500, 503]
        
        if response.status_code == 200:
            data = response.json()
            
            # Check required fields
            required_fields = ["pair", "timeframe", "timestamp"]
            for field in required_fields:
                assert field in data, f"Missing required field: {field}"
            
            # Check signal type if present
            if data.get("signal"):
                assert data["signal"] in ["CALL", "PUT"], "Invalid signal type"
                
                # If signal exists, should have strength and reason
                assert "strength" in data, "Missing strength for signal"
                assert "reason" in data, "Missing reason for signal"
                assert 0 <= data["strength"] <= 1, "Invalid strength value"
    
    @pytest.mark.asyncio
    async def test_dashboard_endpoint(self, client):
        """Test dashboard endpoint"""
        response = await client.get("/dashboard")
        
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        
        # Check that it returns HTML content
        content = response.text
        assert "<html>" in content
        assert "Trading Signals Dashboard" in content
    
    @pytest.mark.asyncio
    async def test_signal_caching(self, client):
        """Test signal caching mechanism"""
        # Make two requests quickly
        response1 = await client.get("/signal")
        response2 = await client.get("/signal")
        
        # Both should succeed (or both fail)
        assert response1.status_code == response2.status_code
        
        if response1.status_code == 200 and response2.status_code == 200:
            data1 = response1.json()
            data2 = response2.json()
            
            # Should return same data due to caching
            assert data1["generated_at"] == data2["generated_at"]
    
    @pytest.mark.asyncio
    async def test_cors_headers(self, client):
        """Test CORS headers are present"""
        response = await client.get("/")
        
        # Should have CORS headers
        assert "access-control-allow-origin" in response.headers
        assert response.headers["access-control-allow-origin"] == "*"

if __name__ == "__main__":
    pytest.main([__file__])
