"""
User Management Service Module

This module provides user management services including CRUD operations,
user information updates and queries, and user permission management functionality.
"""

import logging
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple

from sqlalchemy import or_, and_
from sqlalchemy.exc import IntegrityError

from app.extensions import db
from app.models.user import User

logger = logging.getLogger(__name__)


class UserServiceError(Exception):
    """Custom exception for user service errors."""
    
    def __init__(self, message: str, code: str = None, status_code: int = 400):
        self.message = message
        self.code = code or 'USER_SERVICE_ERROR'
        self.status_code = status_code
        super().__init__(self.message)


class UserService:
    """
    User management service class providing user CRUD and management functionality.
    
    This service handles:
    - User CRUD operations (Create, Read, Update, Delete)
    - User information queries and updates
    - User permission and role management
    - User account management (activation, deactivation, etc.)
    - User search and filtering
    """
    
    @staticmethod
    def get_user_by_id(user_id: int, include_inactive: bool = False) -> Optional[User]:
        """
        Get user by ID.
        
        Args:
            user_id (int): User ID
            include_inactive (bool): Whether to include inactive users
            
        Returns:
            Optional[User]: User instance if found, None otherwise
        """
        logger.debug(f"Getting user by ID: {user_id}")
        
        try:
            query = User.query.filter_by(id=user_id)
            
            if not include_inactive:
                query = query.filter_by(is_active=True)
            
            user = query.first()
            
            if user:
                logger.debug(f"User found: {user.username}")
            else:
                logger.debug(f"User not found with ID: {user_id}")
            
            return user
            
        except Exception as e:
            logger.error(f"Error getting user by ID {user_id}: {e}")
            return None
    
    @staticmethod
    def get_user_by_username(username: str, include_inactive: bool = False) -> Optional[User]:
        """
        Get user by username.
        
        Args:
            username (str): Username
            include_inactive (bool): Whether to include inactive users
            
        Returns:
            Optional[User]: User instance if found, None otherwise
        """
        logger.debug(f"Getting user by username: {username}")
        
        try:
            query = User.query.filter_by(username=username.lower().strip())
            
            if not include_inactive:
                query = query.filter_by(is_active=True)
            
            user = query.first()
            
            if user:
                logger.debug(f"User found: {user.username}")
            else:
                logger.debug(f"User not found with username: {username}")
            
            return user
            
        except Exception as e:
            logger.error(f"Error getting user by username {username}: {e}")
            return None
    
    @staticmethod
    def get_user_by_email(email: str, include_inactive: bool = False) -> Optional[User]:
        """
        Get user by email.
        
        Args:
            email (str): Email address
            include_inactive (bool): Whether to include inactive users
            
        Returns:
            Optional[User]: User instance if found, None otherwise
        """
        logger.debug(f"Getting user by email: {email}")
        
        try:
            query = User.query.filter_by(email=email.lower().strip())
            
            if not include_inactive:
                query = query.filter_by(is_active=True)
            
            user = query.first()
            
            if user:
                logger.debug(f"User found: {user.username}")
            else:
                logger.debug(f"User not found with email: {email}")
            
            return user
            
        except Exception as e:
            logger.error(f"Error getting user by email {email}: {e}")
            return None
    
    @staticmethod
    def get_users(page: int = 1, per_page: int = 20, include_inactive: bool = False,
                  search: str = None, sort_by: str = 'created_at', 
                  sort_order: str = 'desc') -> Dict[str, Any]:
        """
        Get paginated list of users with optional filtering and sorting.
        
        Args:
            page (int): Page number (1-based)
            per_page (int): Number of users per page
            include_inactive (bool): Whether to include inactive users
            search (str, optional): Search term for username, email, or name
            sort_by (str): Field to sort by (default: 'created_at')
            sort_order (str): Sort order 'asc' or 'desc' (default: 'desc')
            
        Returns:
            Dict[str, Any]: Paginated user data with metadata
        """
        logger.debug(f"Getting users - page: {page}, per_page: {per_page}, search: {search}")
        
        try:
            # Build base query
            query = User.query
            
            # Filter by active status
            if not include_inactive:
                query = query.filter_by(is_active=True)
            
            # Apply search filter
            if search:
                search_term = f"%{search.lower()}%"
                query = query.filter(
                    or_(
                        User.username.ilike(search_term),
                        User.email.ilike(search_term),
                        User.first_name.ilike(search_term),
                        User.last_name.ilike(search_term)
                    )
                )
            
            # Apply sorting
            sort_column = getattr(User, sort_by, User.created_at)
            if sort_order.lower() == 'asc':
                query = query.order_by(sort_column.asc())
            else:
                query = query.order_by(sort_column.desc())
            
            # Execute paginated query
            pagination = query.paginate(
                page=page,
                per_page=per_page,
                error_out=False
            )
            
            # Convert users to dictionaries
            users_data = [
                user.to_dict(exclude_fields=['password_hash'])
                for user in pagination.items
            ]
            
            result = {
                'users': users_data,
                'pagination': {
                    'page': pagination.page,
                    'per_page': pagination.per_page,
                    'total': pagination.total,
                    'pages': pagination.pages,
                    'has_prev': pagination.has_prev,
                    'has_next': pagination.has_next,
                    'prev_num': pagination.prev_num,
                    'next_num': pagination.next_num
                }
            }
            
            logger.debug(f"Retrieved {len(users_data)} users (page {page} of {pagination.pages})")
            return result
            
        except Exception as e:
            logger.error(f"Error getting users: {e}")
            raise UserServiceError(
                "Failed to retrieve users",
                code="GET_USERS_ERROR",
                status_code=500
            )
    
    @staticmethod
    def create_user(username: str, email: str, password: str = None, 
                   first_name: str = None, last_name: str = None,
                   is_admin: bool = False, is_verified: bool = False,
                   created_by_user: User = None) -> User:
        """
        Create a new user.
        
        Args:
            username (str): Username
            email (str): Email address
            password (str, optional): Password (if None, user must reset password)
            first_name (str, optional): First name
            last_name (str, optional): Last name
            is_admin (bool): Whether user should be admin
            is_verified (bool): Whether email should be pre-verified
            created_by_user (User, optional): User who created this account
            
        Returns:
            User: Created user instance
            
        Raises:
            UserServiceError: If creation fails
        """
        logger.info(f"Creating user: {username}, email: {email}")
        
        # Input validation
        if not username or not email:
            raise UserServiceError(
                "Username and email are required",
                code="MISSING_REQUIRED_FIELDS",
                status_code=400
            )
        
        # Check for existing users
        if User.get_by_username(username):
            raise UserServiceError(
                "Username already exists",
                code="USERNAME_EXISTS",
                status_code=409
            )
        
        if User.get_by_email(email):
            raise UserServiceError(
                "Email address already exists",
                code="EMAIL_EXISTS",
                status_code=409
            )
        
        try:
            # Create user instance
            user_data = {
                'username': username,
                'email': email,
                'first_name': first_name,
                'last_name': last_name,
                'is_admin': is_admin,
                'is_verified': is_verified,
                'is_active': True
            }
            
            if password:
                user_data['password'] = password
            
            user = User(**user_data)
            
            # Add to database
            db.session.add(user)
            db.session.commit()
            
            logger.info(f"User created successfully: {user.username} (ID: {user.id})")
            
            if created_by_user:
                logger.info(f"User {user.username} created by {created_by_user.username}")
            
            return user
            
        except IntegrityError as e:
            db.session.rollback()
            logger.error(f"Integrity error creating user {username}: {e}")
            raise UserServiceError(
                "User creation failed due to data conflict",
                code="DATA_INTEGRITY_ERROR",
                status_code=409
            )
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error creating user {username}: {e}")
            raise UserServiceError(
                "User creation failed",
                code="CREATE_USER_ERROR",
                status_code=500
            )
    
    @staticmethod
    def update_user(user_id: int, update_data: Dict[str, Any], 
                   updated_by_user: User = None) -> User:
        """
        Update user information.
        
        Args:
            user_id (int): User ID to update
            update_data (Dict[str, Any]): Fields to update
            updated_by_user (User, optional): User performing the update
            
        Returns:
            User: Updated user instance
            
        Raises:
            UserServiceError: If update fails
        """
        logger.info(f"Updating user ID: {user_id}")
        
        # Get user
        user = UserService.get_user_by_id(user_id, include_inactive=True)
        if not user:
            raise UserServiceError(
                "User not found",
                code="USER_NOT_FOUND",
                status_code=404
            )
        
        # Define allowed update fields
        allowed_fields = {
            'first_name', 'last_name', 'bio', 'is_active', 'is_verified', 'is_admin'
        }
        
        # Filter update data to only allowed fields
        filtered_data = {
            key: value for key, value in update_data.items()
            if key in allowed_fields
        }
        
        if not filtered_data:
            raise UserServiceError(
                "No valid fields to update",
                code="NO_UPDATE_FIELDS",
                status_code=400
            )
        
        try:
            # Check for username/email uniqueness if being updated
            if 'username' in update_data:
                new_username = update_data['username']
                existing_user = User.get_by_username(new_username)
                if existing_user and existing_user.id != user_id:
                    raise UserServiceError(
                        "Username already exists",
                        code="USERNAME_EXISTS",
                        status_code=409
                    )
                filtered_data['username'] = new_username
            
            if 'email' in update_data:
                new_email = update_data['email']
                existing_user = User.get_by_email(new_email)
                if existing_user and existing_user.id != user_id:
                    raise UserServiceError(
                        "Email address already exists",
                        code="EMAIL_EXISTS",
                        status_code=409
                    )
                filtered_data['email'] = new_email
            
            # Apply updates
            for field, value in filtered_data.items():
                setattr(user, field, value)
            
            # Update timestamp
            user.updated_at = datetime.utcnow()
            
            db.session.commit()
            
            logger.info(f"User updated successfully: {user.username} (ID: {user.id})")
            
            if updated_by_user:
                logger.info(f"User {user.username} updated by {updated_by_user.username}")
            
            return user
            
        except IntegrityError as e:
            db.session.rollback()
            logger.error(f"Integrity error updating user {user_id}: {e}")
            raise UserServiceError(
                "User update failed due to data conflict",
                code="DATA_INTEGRITY_ERROR",
                status_code=409
            )
        except UserServiceError:
            db.session.rollback()
            raise
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error updating user {user_id}: {e}")
            raise UserServiceError(
                "User update failed",
                code="UPDATE_USER_ERROR",
                status_code=500
            )
    
    @staticmethod
    def delete_user(user_id: int, deleted_by_user: User = None, 
                   soft_delete: bool = True) -> Dict[str, Any]:
        """
        Delete user (soft delete by default).
        
        Args:
            user_id (int): User ID to delete
            deleted_by_user (User, optional): User performing the deletion
            soft_delete (bool): Whether to soft delete (deactivate) or hard delete
            
        Returns:
            Dict[str, Any]: Deletion result
            
        Raises:
            UserServiceError: If deletion fails
        """
        logger.info(f"Deleting user ID: {user_id} (soft_delete: {soft_delete})")
        
        # Get user
        user = UserService.get_user_by_id(user_id, include_inactive=True)
        if not user:
            raise UserServiceError(
                "User not found",
                code="USER_NOT_FOUND",
                status_code=404
            )
        
        # Prevent self-deletion if deleted_by_user is provided
        if deleted_by_user and deleted_by_user.id == user_id:
            raise UserServiceError(
                "Cannot delete your own account",
                code="CANNOT_DELETE_SELF",
                status_code=400
            )
        
        try:
            if soft_delete:
                # Soft delete - deactivate user
                user.is_active = False
                user.updated_at = datetime.utcnow()
                db.session.commit()
                
                logger.info(f"User soft deleted: {user.username} (ID: {user.id})")
                message = "User deactivated successfully"
            else:
                # Hard delete - remove from database
                username = user.username
                db.session.delete(user)
                db.session.commit()
                
                logger.info(f"User hard deleted: {username} (ID: {user_id})")
                message = "User deleted permanently"
            
            if deleted_by_user:
                logger.info(f"User {user.username} deleted by {deleted_by_user.username}")
            
            return {
                'message': message,
                'user_id': user_id,
                'soft_delete': soft_delete
            }
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error deleting user {user_id}: {e}")
            raise UserServiceError(
                "User deletion failed",
                code="DELETE_USER_ERROR",
                status_code=500
            )
    
    @staticmethod
    def activate_user(user_id: int, activated_by_user: User = None) -> User:
        """
        Activate user account.
        
        Args:
            user_id (int): User ID to activate
            activated_by_user (User, optional): User performing the activation
            
        Returns:
            User: Activated user instance
            
        Raises:
            UserServiceError: If activation fails
        """
        logger.info(f"Activating user ID: {user_id}")
        
        user = UserService.get_user_by_id(user_id, include_inactive=True)
        if not user:
            raise UserServiceError(
                "User not found",
                code="USER_NOT_FOUND",
                status_code=404
            )
        
        if user.is_active:
            logger.info(f"User {user.username} is already active")
            return user
        
        try:
            user.activate()
            user.updated_at = datetime.utcnow()
            db.session.commit()
            
            logger.info(f"User activated: {user.username} (ID: {user.id})")
            
            if activated_by_user:
                logger.info(f"User {user.username} activated by {activated_by_user.username}")
            
            return user
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error activating user {user_id}: {e}")
            raise UserServiceError(
                "User activation failed",
                code="ACTIVATE_USER_ERROR",
                status_code=500
            )
    
    @staticmethod
    def deactivate_user(user_id: int, deactivated_by_user: User = None) -> User:
        """
        Deactivate user account.
        
        Args:
            user_id (int): User ID to deactivate
            deactivated_by_user (User, optional): User performing the deactivation
            
        Returns:
            User: Deactivated user instance
            
        Raises:
            UserServiceError: If deactivation fails
        """
        logger.info(f"Deactivating user ID: {user_id}")
        
        user = UserService.get_user_by_id(user_id, include_inactive=True)
        if not user:
            raise UserServiceError(
                "User not found",
                code="USER_NOT_FOUND",
                status_code=404
            )
        
        # Prevent self-deactivation
        if deactivated_by_user and deactivated_by_user.id == user_id:
            raise UserServiceError(
                "Cannot deactivate your own account",
                code="CANNOT_DEACTIVATE_SELF",
                status_code=400
            )
        
        if not user.is_active:
            logger.info(f"User {user.username} is already inactive")
            return user
        
        try:
            user.deactivate()
            user.updated_at = datetime.utcnow()
            db.session.commit()
            
            logger.info(f"User deactivated: {user.username} (ID: {user.id})")
            
            if deactivated_by_user:
                logger.info(f"User {user.username} deactivated by {deactivated_by_user.username}")
            
            return user
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error deactivating user {user_id}: {e}")
            raise UserServiceError(
                "User deactivation failed",
                code="DEACTIVATE_USER_ERROR",
                status_code=500
            )
    
    @staticmethod
    def unlock_user_account(user_id: int, unlocked_by_user: User = None) -> User:
        """
        Unlock user account (clear failed login attempts and lock).
        
        Args:
            user_id (int): User ID to unlock
            unlocked_by_user (User, optional): User performing the unlock
            
        Returns:
            User: Unlocked user instance
            
        Raises:
            UserServiceError: If unlock fails
        """
        logger.info(f"Unlocking user account ID: {user_id}")
        
        user = UserService.get_user_by_id(user_id, include_inactive=True)
        if not user:
            raise UserServiceError(
                "User not found",
                code="USER_NOT_FOUND",
                status_code=404
            )
        
        if not user.is_account_locked():
            logger.info(f"User {user.username} account is not locked")
            return user
        
        try:
            user.unlock_account()
            user.updated_at = datetime.utcnow()
            db.session.commit()
            
            logger.info(f"User account unlocked: {user.username} (ID: {user.id})")
            
            if unlocked_by_user:
                logger.info(f"User {user.username} unlocked by {unlocked_by_user.username}")
            
            return user
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error unlocking user {user_id}: {e}")
            raise UserServiceError(
                "User unlock failed",
                code="UNLOCK_USER_ERROR",
                status_code=500
            )
    
    @staticmethod
    def set_user_admin_status(user_id: int, is_admin: bool, 
                             updated_by_user: User = None) -> User:
        """
        Set user admin status.
        
        Args:
            user_id (int): User ID to update
            is_admin (bool): Whether user should be admin
            updated_by_user (User, optional): User performing the update
            
        Returns:
            User: Updated user instance
            
        Raises:
            UserServiceError: If update fails
        """
        logger.info(f"Setting admin status for user ID {user_id}: {is_admin}")
        
        user = UserService.get_user_by_id(user_id, include_inactive=True)
        if not user:
            raise UserServiceError(
                "User not found",
                code="USER_NOT_FOUND",
                status_code=404
            )
        
        # Prevent self-demotion from admin
        if (updated_by_user and updated_by_user.id == user_id and 
            updated_by_user.is_admin and not is_admin):
            raise UserServiceError(
                "Cannot remove admin privileges from your own account",
                code="CANNOT_DEMOTE_SELF",
                status_code=400
            )
        
        if user.is_admin == is_admin:
            logger.info(f"User {user.username} admin status is already {is_admin}")
            return user
        
        try:
            user.is_admin = is_admin
            user.updated_at = datetime.utcnow()
            db.session.commit()
            
            status = "granted" if is_admin else "revoked"
            logger.info(f"Admin privileges {status} for user: {user.username} (ID: {user.id})")
            
            if updated_by_user:
                logger.info(f"Admin status for {user.username} updated by {updated_by_user.username}")
            
            return user
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error setting admin status for user {user_id}: {e}")
            raise UserServiceError(
                "Admin status update failed",
                code="SET_ADMIN_STATUS_ERROR",
                status_code=500
            )
    
    @staticmethod
    def search_users(search_term: str, limit: int = 20, include_inactive: bool = False) -> List[User]:
        """
        Search users by username, email, or name.
        
        Args:
            search_term (str): Search term
            limit (int): Maximum number of results
            include_inactive (bool): Whether to include inactive users
            
        Returns:
            List[User]: List of matching users
        """
        logger.debug(f"Searching users with term: {search_term}")
        
        if not search_term or len(search_term.strip()) < 2:
            return []
        
        try:
            search_pattern = f"%{search_term.lower()}%"
            query = User.query.filter(
                or_(
                    User.username.ilike(search_pattern),
                    User.email.ilike(search_pattern),
                    User.first_name.ilike(search_pattern),
                    User.last_name.ilike(search_pattern)
                )
            )
            
            if not include_inactive:
                query = query.filter_by(is_active=True)
            
            users = query.limit(limit).all()
            
            logger.debug(f"Found {len(users)} users matching search term")
            return users
            
        except Exception as e:
            logger.error(f"Error searching users with term '{search_term}': {e}")
            return []
    
    @staticmethod
    def get_user_statistics() -> Dict[str, Any]:
        """
        Get user statistics.
        
        Returns:
            Dict[str, Any]: User statistics
        """
        logger.debug("Getting user statistics")
        
        try:
            total_users = User.query.count()
            active_users = User.query.filter_by(is_active=True).count()
            verified_users = User.query.filter_by(is_verified=True).count()
            admin_users = User.query.filter_by(is_admin=True).count()
            
            # Users created in last 30 days
            from datetime import datetime, timedelta
            thirty_days_ago = datetime.utcnow() - timedelta(days=30)
            recent_users = User.query.filter(User.created_at >= thirty_days_ago).count()
            
            stats = {
                'total_users': total_users,
                'active_users': active_users,
                'inactive_users': total_users - active_users,
                'verified_users': verified_users,
                'unverified_users': total_users - verified_users,
                'admin_users': admin_users,
                'recent_users_30_days': recent_users,
                'generated_at': datetime.utcnow().isoformat()
            }
            
            logger.debug(f"User statistics generated: {stats}")
            return stats
            
        except Exception as e:
            logger.error(f"Error getting user statistics: {e}")
            raise UserServiceError(
                "Failed to retrieve user statistics",
                code="GET_STATISTICS_ERROR",
                status_code=500
            )
    
    @staticmethod
    def check_user_permissions(user: User, required_permission: str) -> bool:
        """
        Check if user has required permission.
        
        Args:
            user (User): User to check
            required_permission (str): Required permission
            
        Returns:
            bool: True if user has permission, False otherwise
        """
        logger.debug(f"Checking permission '{required_permission}' for user: {user.username}")
        
        # Basic permission system - can be extended with roles/permissions table
        if not user.is_active:
            logger.debug(f"Permission denied - user {user.username} is inactive")
            return False
        
        if user.is_account_locked():
            logger.debug(f"Permission denied - user {user.username} is locked")
            return False
        
        # Admin users have all permissions
        if user.is_admin:
            logger.debug(f"Permission granted - user {user.username} is admin")
            return True
        
        # Define permission mappings (can be moved to database/config)
        user_permissions = {
            'read_own_profile': True,
            'update_own_profile': True,
            'change_own_password': True,
        }
        
        admin_permissions = {
            'read_all_users': True,
            'create_users': True,
            'update_users': True,
            'delete_users': True,
            'manage_user_permissions': True,
            'view_user_statistics': True,
        }
        
        # Check permission
        has_permission = user_permissions.get(required_permission, False)
        
        if user.is_admin:
            has_permission = admin_permissions.get(required_permission, has_permission)
        
        logger.debug(f"Permission check result for {user.username}: {has_permission}")
        return has_permission