#!/usr/bin/env python3
"""
FortunaMind Subscription Management System

This script provides subscription management capabilities for the
FortunaMind Persistent MCP Server, including key generation,
user registration, and subscription administration.
"""

import asyncio
import os
import sys
import json
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import argparse
import logging

# Add src to Python path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from fortunamind_persistence.identity import EmailIdentity
from fortunamind_persistence.subscription import SubscriptionValidator, SubscriptionTier
from fortunamind_persistence.storage import SupabaseStorage

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(name)s: %(message)s')
logger = logging.getLogger(__name__)


class SubscriptionManager:
    """
    Complete subscription management system for FortunaMind Persistent MCP.
    
    Handles user registration, subscription key generation, tier management,
    and administrative operations.
    """
    
    def __init__(self):
        self.identity = EmailIdentity()
        self.storage = SupabaseStorage()
        self.validator = SubscriptionValidator()
        self.initialized = False
    
    async def initialize(self):
        """Initialize all components"""
        try:
            await self.storage.initialize()
            logger.info("Subscription manager initialized successfully")
            self.initialized = True
        except Exception as e:
            logger.error(f"Failed to initialize subscription manager: {e}")
            raise
    
    async def create_user_subscription(
        self,
        email: str,
        tier: SubscriptionTier = SubscriptionTier.FREE,
        duration_days: int = 365
    ) -> Dict[str, Any]:
        """
        Create a new user subscription with generated key.
        
        Args:
            email: User's email address
            tier: Subscription tier
            duration_days: Subscription duration in days
            
        Returns:
            Dict with subscription details and generated key
        """
        if not self.initialized:
            await self.initialize()
        
        try:
            # Generate user ID from email
            user_id = self.identity.generate_user_id(email)
            logger.info(f"Creating subscription for user {user_id[:16]}... (email: {email[:20]}...)")
            
            # Generate subscription key
            subscription_key = await self.validator.generate_subscription_key(email, tier)
            
            # Calculate expiration
            expires_at = datetime.utcnow() + timedelta(days=duration_days)
            
            logger.info(f"Subscription created successfully:")
            logger.info(f"  User ID: {user_id}")
            logger.info(f"  Email: {email}")
            logger.info(f"  Tier: {tier.value}")
            logger.info(f"  Key: {subscription_key}")
            logger.info(f"  Expires: {expires_at.isoformat()}")
            
            return {
                "success": True,
                "user_id": user_id,
                "email": email,
                "subscription_key": subscription_key,
                "tier": tier.value,
                "expires_at": expires_at.isoformat(),
                "duration_days": duration_days
            }
            
        except Exception as e:
            logger.error(f"Failed to create subscription: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def validate_subscription(self, email: str, subscription_key: str) -> Dict[str, Any]:
        """
        Validate an existing subscription.
        
        Args:
            email: User's email address
            subscription_key: Subscription key to validate
            
        Returns:
            Dict with validation result
        """
        if not self.initialized:
            await self.initialize()
        
        try:
            result = await self.validator.validate(email, subscription_key)
            
            logger.info(f"Subscription validation for {email[:20]}...: {result.is_valid}")
            
            return {
                "success": True,
                "valid": result.is_valid,
                "tier": result.tier.value if result.tier else None,
                "user_id": result.user_id,
                "reason": result.reason
            }
            
        except Exception as e:
            logger.error(f"Subscription validation failed: {e}")
            return {
                "success": False,
                "valid": False,
                "error": str(e)
            }
    
    async def list_user_subscriptions(self, limit: int = 50) -> Dict[str, Any]:
        """
        List all user subscriptions (admin function).
        
        Args:
            limit: Maximum number of subscriptions to return
            
        Returns:
            Dict with list of subscriptions
        """
        if not self.initialized:
            await self.initialize()
        
        try:
            # Query database directly
            result = self.storage.client.table('user_subscriptions').select('*').limit(limit).execute()
            
            subscriptions = []
            for sub in result.data:
                subscriptions.append({
                    "user_id_hash": sub.get("user_id_hash", "")[:16] + "...",
                    "email_hash": sub.get("email_hash", "")[:16] + "...",
                    "tier": sub.get("tier"),
                    "status": sub.get("status", "active"),
                    "created_at": sub.get("created_at"),
                    "expires_at": sub.get("expires_at"),
                    "last_accessed": sub.get("last_accessed")
                })
            
            logger.info(f"Retrieved {len(subscriptions)} subscriptions")
            
            return {
                "success": True,
                "subscriptions": subscriptions,
                "count": len(subscriptions)
            }
            
        except Exception as e:
            logger.error(f"Failed to list subscriptions: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def update_subscription_tier(
        self,
        email: str,
        new_tier: SubscriptionTier
    ) -> Dict[str, Any]:
        """
        Update a user's subscription tier.
        
        Args:
            email: User's email address
            new_tier: New subscription tier
            
        Returns:
            Dict with update result
        """
        if not self.initialized:
            await self.initialize()
        
        try:
            user_id = self.identity.generate_user_id(email)
            email_hash = self.identity.hash_email(email)
            
            # Update in database
            result = self.storage.client.table('user_subscriptions').update({
                'tier': new_tier.value,
                'updated_at': datetime.utcnow().isoformat()
            }).eq('user_id_hash', user_id).execute()
            
            if result.data:
                logger.info(f"Updated subscription tier for {email[:20]}... to {new_tier.value}")
                return {
                    "success": True,
                    "message": f"Tier updated to {new_tier.value}"
                }
            else:
                logger.warning(f"No subscription found for {email[:20]}...")
                return {
                    "success": False,
                    "error": "Subscription not found"
                }
                
        except Exception as e:
            logger.error(f"Failed to update subscription tier: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def deactivate_subscription(self, email: str) -> Dict[str, Any]:
        """
        Deactivate a user's subscription.
        
        Args:
            email: User's email address
            
        Returns:
            Dict with deactivation result
        """
        if not self.initialized:
            await self.initialize()
        
        try:
            user_id = self.identity.generate_user_id(email)
            
            # Update status in database
            result = self.storage.client.table('user_subscriptions').update({
                'status': 'inactive',
                'deactivated_at': datetime.utcnow().isoformat()
            }).eq('user_id_hash', user_id).execute()
            
            if result.data:
                logger.info(f"Deactivated subscription for {email[:20]}...")
                return {
                    "success": True,
                    "message": "Subscription deactivated"
                }
            else:
                logger.warning(f"No subscription found for {email[:20]}...")
                return {
                    "success": False,
                    "error": "Subscription not found"
                }
                
        except Exception as e:
            logger.error(f"Failed to deactivate subscription: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_subscription_stats(self) -> Dict[str, Any]:
        """
        Get overall subscription statistics.
        
        Returns:
            Dict with subscription statistics
        """
        if not self.initialized:
            await self.initialize()
        
        try:
            # Get total counts by tier
            free_count = self.storage.client.table('user_subscriptions').select('count').eq('tier', 'free').execute()
            premium_count = self.storage.client.table('user_subscriptions').select('count').eq('tier', 'premium').execute()
            pro_count = self.storage.client.table('user_subscriptions').select('count').eq('tier', 'pro').execute()
            
            # Get active subscriptions
            active_count = self.storage.client.table('user_subscriptions').select('count').eq('status', 'active').execute()
            
            stats = {
                "total_subscriptions": len(free_count.data) + len(premium_count.data) + len(pro_count.data),
                "active_subscriptions": len(active_count.data),
                "by_tier": {
                    "free": len(free_count.data),
                    "premium": len(premium_count.data),
                    "pro": len(pro_count.data)
                },
                "timestamp": datetime.utcnow().isoformat()
            }
            
            logger.info(f"Subscription stats: {stats['total_subscriptions']} total, {stats['active_subscriptions']} active")
            
            return {
                "success": True,
                "stats": stats
            }
            
        except Exception as e:
            logger.error(f"Failed to get subscription stats: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def cleanup(self):
        """Cleanup resources"""
        if self.storage:
            await self.storage.cleanup()


async def main():
    """Command-line interface for subscription management"""
    parser = argparse.ArgumentParser(description="FortunaMind Subscription Manager")
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Create subscription command
    create_parser = subparsers.add_parser('create', help='Create new subscription')
    create_parser.add_argument('email', help='User email address')
    create_parser.add_argument('--tier', choices=['free', 'starter', 'premium', 'enterprise'], default='free', help='Subscription tier')
    create_parser.add_argument('--days', type=int, default=365, help='Subscription duration in days')
    
    # Validate subscription command
    validate_parser = subparsers.add_parser('validate', help='Validate subscription')
    validate_parser.add_argument('email', help='User email address')
    validate_parser.add_argument('key', help='Subscription key')
    
    # List subscriptions command
    list_parser = subparsers.add_parser('list', help='List all subscriptions')
    list_parser.add_argument('--limit', type=int, default=50, help='Maximum subscriptions to show')
    
    # Update tier command
    update_parser = subparsers.add_parser('update', help='Update subscription tier')
    update_parser.add_argument('email', help='User email address')
    update_parser.add_argument('tier', choices=['free', 'starter', 'premium', 'enterprise'], help='New tier')
    
    # Deactivate subscription command
    deactivate_parser = subparsers.add_parser('deactivate', help='Deactivate subscription')
    deactivate_parser.add_argument('email', help='User email address')
    
    # Stats command
    stats_parser = subparsers.add_parser('stats', help='Show subscription statistics')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    manager = SubscriptionManager()
    
    try:
        if args.command == 'create':
            tier = SubscriptionTier(args.tier.upper())
            result = await manager.create_user_subscription(args.email, tier, args.days)
            print(json.dumps(result, indent=2))
        
        elif args.command == 'validate':
            result = await manager.validate_subscription(args.email, args.key)
            print(json.dumps(result, indent=2))
        
        elif args.command == 'list':
            result = await manager.list_user_subscriptions(args.limit)
            print(json.dumps(result, indent=2))
        
        elif args.command == 'update':
            tier = SubscriptionTier(args.tier.upper())
            result = await manager.update_subscription_tier(args.email, tier)
            print(json.dumps(result, indent=2))
        
        elif args.command == 'deactivate':
            result = await manager.deactivate_subscription(args.email)
            print(json.dumps(result, indent=2))
        
        elif args.command == 'stats':
            result = await manager.get_subscription_stats()
            print(json.dumps(result, indent=2))
    
    except Exception as e:
        logger.error(f"Command execution failed: {e}")
        print(json.dumps({"success": False, "error": str(e)}, indent=2))
    
    finally:
        await manager.cleanup()


if __name__ == "__main__":
    asyncio.run(main())