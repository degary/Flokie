"""
Authentication API namespace for Flask-RESTX documentation.

This module defines the authentication API endpoints with comprehensive
documentation using Flask-RESTX decorators and models.
"""

from flask import request
from flask_jwt_extended import get_current_user, jwt_required
from flask_restx import Namespace, Resource

from app.api.models import (
    change_password_model,
    email_verification_model,
    error_model,
    login_request_model,
    login_response_model,
    password_reset_model,
    password_reset_request_model,
    refresh_token_response_model,
    register_request_model,
    register_response_model,
    success_model,
    user_response_model,
    validation_error_model,
)
from app.controllers.auth_controller import auth_bp

# Create authentication namespace
auth_ns = Namespace("auth", description="Authentication operations", path="/auth")

# Add models to namespace
auth_ns.models[login_request_model.name] = login_request_model
auth_ns.models[login_response_model.name] = login_response_model
auth_ns.models[register_request_model.name] = register_request_model
auth_ns.models[register_response_model.name] = register_response_model
auth_ns.models[refresh_token_response_model.name] = refresh_token_response_model
auth_ns.models[password_reset_request_model.name] = password_reset_request_model
auth_ns.models[password_reset_model.name] = password_reset_model
auth_ns.models[change_password_model.name] = change_password_model
auth_ns.models[email_verification_model.name] = email_verification_model
auth_ns.models[user_response_model.name] = user_response_model
auth_ns.models[success_model.name] = success_model
auth_ns.models[error_model.name] = error_model
auth_ns.models[validation_error_model.name] = validation_error_model


@auth_ns.route("/login")
class LoginResource(Resource):
    @auth_ns.doc("login_user")
    @auth_ns.expect(login_request_model, validate=True)
    @auth_ns.marshal_with(
        login_response_model, code=200, description="Login successful"
    )
    @auth_ns.response(400, "Invalid request data", validation_error_model)
    @auth_ns.response(401, "Invalid credentials", error_model)
    @auth_ns.response(403, "Account inactive", error_model)
    @auth_ns.response(423, "Account locked", error_model)
    @auth_ns.response(500, "Internal server error", error_model)
    def post(self):
        """
        User login

        Authenticate user with username/email and password.
        Returns JWT tokens for subsequent API calls.
        """
        # This is handled by the actual controller
        pass


@auth_ns.route("/register")
class RegisterResource(Resource):
    @auth_ns.doc("register_user")
    @auth_ns.expect(register_request_model, validate=True)
    @auth_ns.marshal_with(
        register_response_model, code=201, description="Registration successful"
    )
    @auth_ns.response(400, "Invalid request data", validation_error_model)
    @auth_ns.response(409, "Username or email already exists", error_model)
    @auth_ns.response(500, "Internal server error", error_model)
    def post(self):
        """
        User registration

        Create a new user account with email verification.
        Returns user information and verification token.
        """
        # This is handled by the actual controller
        pass


@auth_ns.route("/refresh")
class RefreshTokenResource(Resource):
    @auth_ns.doc("refresh_token", security="Bearer")
    @auth_ns.marshal_with(
        refresh_token_response_model,
        code=200,
        description="Token refreshed successfully",
    )
    @auth_ns.response(401, "Invalid or expired refresh token", error_model)
    @auth_ns.response(403, "Account inactive or locked", error_model)
    @auth_ns.response(500, "Internal server error", error_model)
    @jwt_required(refresh=True)
    def post(self):
        """
        Refresh access token

        Generate a new access token using a valid refresh token.
        Requires a valid refresh token in the Authorization header.
        """
        # This is handled by the actual controller
        pass


@auth_ns.route("/password/reset-request")
class PasswordResetRequestResource(Resource):
    @auth_ns.doc("request_password_reset")
    @auth_ns.expect(password_reset_request_model, validate=True)
    @auth_ns.marshal_with(
        success_model, code=200, description="Reset request processed"
    )
    @auth_ns.response(400, "Invalid request data", validation_error_model)
    @auth_ns.response(500, "Internal server error", error_model)
    def post(self):
        """
        Request password reset

        Send password reset email to the specified address.
        Always returns success for security reasons.
        """
        # This is handled by the actual controller
        pass


@auth_ns.route("/password/reset")
class PasswordResetResource(Resource):
    @auth_ns.doc("reset_password")
    @auth_ns.expect(password_reset_model, validate=True)
    @auth_ns.marshal_with(
        success_model, code=200, description="Password reset successful"
    )
    @auth_ns.response(400, "Invalid request data or token", validation_error_model)
    @auth_ns.response(500, "Internal server error", error_model)
    def post(self):
        """
        Reset password

        Reset user password using a valid reset token.
        The token is typically sent via email.
        """
        # This is handled by the actual controller
        pass


@auth_ns.route("/password/change")
class ChangePasswordResource(Resource):
    @auth_ns.doc("change_password", security="Bearer")
    @auth_ns.expect(change_password_model, validate=True)
    @auth_ns.marshal_with(
        success_model, code=200, description="Password changed successfully"
    )
    @auth_ns.response(
        400, "Invalid request data or current password", validation_error_model
    )
    @auth_ns.response(401, "Invalid or expired access token", error_model)
    @auth_ns.response(500, "Internal server error", error_model)
    @jwt_required()
    def post(self):
        """
        Change password

        Change the current user's password.
        Requires authentication and current password verification.
        """
        # This is handled by the actual controller
        pass


@auth_ns.route("/email/verify")
class EmailVerificationResource(Resource):
    @auth_ns.doc("verify_email")
    @auth_ns.expect(email_verification_model, validate=True)
    @auth_ns.marshal_with(
        success_model, code=200, description="Email verified successfully"
    )
    @auth_ns.response(400, "Invalid request data or token", validation_error_model)
    @auth_ns.response(500, "Internal server error", error_model)
    def post(self):
        """
        Verify email address

        Verify user email address using a verification token.
        The token is typically sent via email during registration.
        """
        # This is handled by the actual controller
        pass


@auth_ns.route("/logout")
class LogoutResource(Resource):
    @auth_ns.doc("logout_user", security="Bearer")
    @auth_ns.marshal_with(success_model, code=200, description="Logout successful")
    @auth_ns.response(401, "Invalid or expired access token", error_model)
    @auth_ns.response(500, "Internal server error", error_model)
    @jwt_required()
    def post(self):
        """
        User logout

        Logout the current user and invalidate tokens.
        Requires a valid access token.
        """
        # This is handled by the actual controller
        pass


@auth_ns.route("/me")
class CurrentUserResource(Resource):
    @auth_ns.doc("get_current_user", security="Bearer")
    @auth_ns.marshal_with(
        user_response_model,
        code=200,
        description="User information retrieved successfully",
    )
    @auth_ns.response(401, "Invalid or expired access token", error_model)
    @auth_ns.response(500, "Internal server error", error_model)
    @jwt_required()
    def get(self):
        """
        Get current user information

        Retrieve information about the currently authenticated user.
        Requires a valid access token.
        """
        # This is handled by the actual controller
        pass
