"""
Tests for EmailIdentity class

Tests email normalization, user ID generation, and API key compatibility.
"""

import pytest
from unittest.mock import patch
from fortunamind_persistence.identity.email_identity import EmailIdentity


class TestEmailIdentity:
    """Test cases for EmailIdentity functionality"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.identity = EmailIdentity()
    
    def test_normalize_email_basic(self):
        """Test basic email normalization"""
        # Standard email
        assert self.identity.normalize_email("test@example.com") == "test@example.com"
        
        # Uppercase
        assert self.identity.normalize_email("TEST@EXAMPLE.COM") == "test@example.com"
        
        # Mixed case
        assert self.identity.normalize_email("TeSt@ExAmPlE.CoM") == "test@example.com"
    
    def test_normalize_email_whitespace(self):
        """Test email normalization with whitespace"""
        assert self.identity.normalize_email("  test@example.com  ") == "test@example.com"
        assert self.identity.normalize_email("test@example.com\n") == "test@example.com"
        assert self.identity.normalize_email("\ttest@example.com\t") == "test@example.com"
    
    def test_normalize_email_gmail_dots(self):
        """Test Gmail dot removal"""
        # Gmail dots should be removed from local part
        assert self.identity.normalize_email("test.user@gmail.com") == "testuser@gmail.com"
        assert self.identity.normalize_email("t.e.s.t@gmail.com") == "test@gmail.com"
        
        # But not for other domains
        assert self.identity.normalize_email("test.user@yahoo.com") == "test.user@yahoo.com"
        assert self.identity.normalize_email("test.user@example.com") == "test.user@example.com"
    
    def test_normalize_email_gmail_plus(self):
        """Test Gmail plus addressing"""
        # Gmail plus addressing should be removed
        assert self.identity.normalize_email("test+label@gmail.com") == "test@gmail.com"
        assert self.identity.normalize_email("test+multiple+labels@gmail.com") == "test@gmail.com"
        
        # But not for other domains
        assert self.identity.normalize_email("test+label@yahoo.com") == "test+label@yahoo.com"
    
    def test_normalize_email_invalid(self):
        """Test normalization with invalid emails"""
        with pytest.raises(ValueError, match="Invalid email"):
            self.identity.normalize_email("not-an-email")
        
        with pytest.raises(ValueError, match="Invalid email"):
            self.identity.normalize_email("@example.com")
        
        with pytest.raises(ValueError, match="Invalid email"):
            self.identity.normalize_email("test@")
        
        with pytest.raises(ValueError, match="Invalid email"):
            self.identity.normalize_email("")
    
    def test_generate_user_id_consistency(self):
        """Test that user ID generation is consistent"""
        email = "test@example.com"
        
        # Same email should generate same ID
        id1 = self.identity.generate_user_id(email)
        id2 = self.identity.generate_user_id(email)
        assert id1 == id2
        
        # Different emails should generate different IDs
        id3 = self.identity.generate_user_id("different@example.com")
        assert id1 != id3
    
    def test_generate_user_id_normalized(self):
        """Test that normalized emails generate same ID"""
        # These should all generate the same ID after normalization
        emails = [
            "test@example.com",
            "TEST@EXAMPLE.COM", 
            "  test@example.com  ",
            "Test@Example.Com"
        ]
        
        ids = [self.identity.generate_user_id(email) for email in emails]
        
        # All IDs should be the same
        assert len(set(ids)) == 1, f"Expected same ID for all emails, got: {ids}"
    
    def test_generate_user_id_gmail_normalization(self):
        """Test Gmail normalization affects user ID"""
        # These Gmail addresses should generate the same ID
        gmail_variants = [
            "test.user@gmail.com",
            "testuser@gmail.com",
            "test.user+label@gmail.com",
            "testuser+otherlabel@gmail.com"
        ]
        
        ids = [self.identity.generate_user_id(email) for email in gmail_variants]
        assert len(set(ids)) == 1, f"Gmail variants should have same ID: {ids}"
        
        # But different from non-Gmail
        yahoo_id = self.identity.generate_user_id("test.user@yahoo.com")
        assert yahoo_id != ids[0]
    
    def test_generate_user_id_properties(self):
        """Test properties of generated user IDs"""
        user_id = self.identity.generate_user_id("test@example.com")
        
        # Should be a hex string (SHA-256 = 64 hex chars)
        assert isinstance(user_id, str)
        assert len(user_id) == 64
        assert all(c in '0123456789abcdef' for c in user_id)
    
    def test_generate_user_id_from_api_key(self):
        """Test user ID generation from API key (legacy compatibility)"""
        api_key = "organizations/test-org/apiKeys/test-key-12345"
        
        user_id = self.identity.generate_user_id_from_api_key(api_key)
        
        # Should be consistent
        user_id2 = self.identity.generate_user_id_from_api_key(api_key)
        assert user_id == user_id2
        
        # Should be different from email-based ID
        email_id = self.identity.generate_user_id("test@example.com")
        assert user_id != email_id
        
        # Should handle different API key formats
        simple_key = "simple-api-key"
        simple_id = self.identity.generate_user_id_from_api_key(simple_key)
        assert simple_id != user_id
    
    def test_extract_from_auth_context_email(self):
        """Test extracting email from auth context signature"""
        # Mock auth context with email in signature
        class MockAuthContext:
            def __init__(self, signature):
                self.signature = signature
        
        auth_context = MockAuthContext("test@example.com")
        email = self.identity.extract_from_auth_context(auth_context)
        assert email == "test@example.com"
    
    def test_extract_from_auth_context_no_signature(self):
        """Test extracting from auth context without signature"""
        class MockAuthContext:
            def __init__(self):
                self.signature = None
        
        auth_context = MockAuthContext()
        email = self.identity.extract_from_auth_context(auth_context)
        assert email is None
    
    def test_extract_from_auth_context_invalid_email(self):
        """Test extracting invalid email from auth context"""
        class MockAuthContext:
            def __init__(self, signature):
                self.signature = signature
        
        auth_context = MockAuthContext("not-an-email")
        email = self.identity.extract_from_auth_context(auth_context)
        assert email is None
    
    def test_class_constants(self):
        """Test that class constants are properly set"""
        # These constants are used in ID generation and should not change
        assert EmailIdentity.NAMESPACE == "fortunamind"
        assert EmailIdentity.VERSION == "v1"
        assert isinstance(EmailIdentity.GMAIL_DOMAINS, set)
        assert "gmail.com" in EmailIdentity.GMAIL_DOMAINS
        assert "googlemail.com" in EmailIdentity.GMAIL_DOMAINS
    
    @pytest.mark.parametrize("email,expected", [
        ("test@example.com", "test@example.com"),
        ("Test@Example.Com", "test@example.com"),  
        ("test.dots@gmail.com", "testdots@gmail.com"),
        ("test+plus@gmail.com", "test@gmail.com"),
        ("Test.Dots+Plus@Gmail.Com", "testdots@gmail.com"),
        ("normal@yahoo.com", "normal@yahoo.com"),
        ("dots.kept@yahoo.com", "dots.kept@yahoo.com"),
    ])
    def test_normalize_email_parametrized(self, email, expected):
        """Parametrized test for various email normalization cases"""
        assert self.identity.normalize_email(email) == expected
    
    def test_thread_safety(self):
        """Test that EmailIdentity is thread-safe (stateless)"""
        import threading
        import time
        
        emails = [f"test{i}@example.com" for i in range(100)]
        results = {}
        
        def generate_ids():
            for email in emails:
                results[email] = self.identity.generate_user_id(email)
        
        # Run in multiple threads
        threads = [threading.Thread(target=generate_ids) for _ in range(5)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        
        # All results should be consistent
        for email in emails:
            expected_id = self.identity.generate_user_id(email)
            assert results[email] == expected_id