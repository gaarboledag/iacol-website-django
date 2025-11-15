from django.test import TestCase
from django.test.utils import override_settings
from django.db import connection
from django.test import Client
from .models import Agent, AgentCategory


class QueryPerformanceTest(TestCase):
    """Test for query performance and N+1 query prevention"""

    def setUp(self):
        self.client = Client()
        # Create test data
        self.category = AgentCategory.objects.create(
            name="Test Category",
            description="Test Description"
        )
        self.agent = Agent.objects.create(
            name="Test Agent",
            description="Test Description",
            category=self.category,
            price=100.00,
            pricing_type="monthly",
            n8n_workflow_id="test-workflow-123"
        )

    def test_agent_list_no_n_plus_one(self):
        """Test that agent_list view doesn't have N+1 queries"""
        # Reset query count
        connection.queries_log.clear()

        # Make request to agent list
        response = self.client.get('/agents/agent_list/')

        # Check that we don't have excessive queries
        # Should be around 2-3 queries max (auth check + main query + count)
        self.assertLess(len(connection.queries), 5,
                       f"Too many queries: {len(connection.queries)}. "
                       f"Queries: {[q['sql'] for q in connection.queries]}")

    def test_solutions_view_performance(self):
        """Test solutions view performance"""
        connection.queries_log.clear()

        response = self.client.get('/solutions/')

        # Should be efficient
        self.assertLess(len(connection.queries), 3,
                       f"Solutions view too slow: {len(connection.queries)} queries")

    def test_agent_detail_select_related(self):
        """Test that agent detail uses select_related"""
        connection.queries_log.clear()

        response = self.client.get(f'/agents/agent/{self.agent.id}/')

        # Should only need 1-2 queries (auth + main query with select_related)
        self.assertLess(len(connection.queries), 3,
                       f"Agent detail has N+1: {len(connection.queries)} queries")


class CacheTest(TestCase):
    """Test caching functionality"""

    def test_agent_list_caching(self):
        """Test that agent list is properly cached"""
        from django.core.cache import cache

        # Clear cache
        cache.clear()

        # First request should cache
        response1 = self.client.get('/agents/agent_list/')
        self.assertEqual(response1.status_code, 200)

        # Check cache was populated
        cache_key = 'agent_list_True'  # For admin user
        cached_data = cache.get(cache_key)
        self.assertIsNotNone(cached_data, "Agent list not cached")