package com.cbsc.trading.api;

import com.cbsc.trading.api.models.*;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * Users API
 *
 * Handles user management operations including listing, creating, updating, and deleting users.
 */
public class UsersApi {
    private final CBSCApiClient client;

    public UsersApi(CBSCApiClient client) {
        this.client = client;
    }

    /**
     * Get list of users with optional filtering
     *
     * @param role Filter by user role (optional)
     * @param isActive Filter by active status (optional)
     * @param skip Number of users to skip (pagination)
     * @param limit Maximum number of users to return (pagination)
     * @return UserListResponse containing users and pagination info
     * @throws ApiException If request fails
     */
    public UserListResponse getUsers(UserRole role, Boolean isActive, Integer skip, Integer limit) throws ApiException {
        Map<String, String> queryParams = new HashMap<>();

        if (role != null) {
            queryParams.put("role", role.getValue());
        }
        if (isActive != null) {
            queryParams.put("is_active", isActive.toString());
        }
        if (skip != null && skip > 0) {
            queryParams.put("skip", skip.toString());
        }
        if (limit != null && limit > 0) {
            queryParams.put("limit", limit.toString());
        }

        ApiResponse response = client.get("/api/v1/users", queryParams);
        return response.as(UserListResponse.class);
    }

    /**
     * Get users with default pagination
     *
     * @return UserListResponse containing users and pagination info
     * @throws ApiException If request fails
     */
    public UserListResponse getUsers() throws ApiException {
        return getUsers(null, null, null, null);
    }

    /**
     * Get user by ID
     *
     * @param userId The user ID
     * @return UserResponse with user details
     * @throws ApiException If user not found or request fails
     */
    public UserResponse getUser(String userId) throws ApiException {
        String path = "/api/v1/users/" + userId;
        ApiResponse response = client.get(path);
        return response.as(UserResponse.class);
    }

    /**
     * Create a new user
     *
     * @param user User creation details
     * @return UserResponse for the created user
     * @throws ApiException If creation fails
     */
    public UserResponse createUser(UserCreate user) throws ApiException {
        ApiResponse response = client.post("/api/v1/users", user);
        return response.as(UserResponse.class);
    }

    /**
     * Update user information
     *
     * @param userId The user ID
     * @param updates Map of fields to update
     * @return UserResponse with updated user information
     * @throws ApiException If update fails
     */
    public UserResponse updateUser(String userId, Map<String, Object> updates) throws ApiException {
        String path = "/api/v1/users/" + userId;
        ApiResponse response = client.put(path, updates);
        return response.as(UserResponse.class);
    }

    /**
     * Delete a user
     *
     * @param userId The user ID
     * @throws ApiException If deletion fails
     */
    public void deleteUser(String userId) throws ApiException {
        String path = "/api/v1/users/" + userId;
        client.delete(path);
    }

    /**
     * Activate a user account
     *
     * @param userId The user ID
     * @return UserResponse with updated user status
     * @throws ApiException If activation fails
     */
    public UserResponse activateUser(String userId) throws ApiException {
        String path = "/api/v1/users/" + userId + "/activate";
        ApiResponse response = client.post(path, null);
        return response.as(UserResponse.class);
    }

    /**
     * Deactivate a user account
     *
     * @param userId The user ID
     * @return UserResponse with updated user status
     * @throws ApiException If deactivation fails
     */
    public UserResponse deactivateUser(String userId) throws ApiException {
        String path = "/api/v1/users/" + userId + "/deactivate";
        ApiResponse response = client.post(path, null);
        return response.as(UserResponse.class);
    }

    /**
     * Get API usage statistics for a user
     *
     * @param userId The user ID
     * @return ApiUsageResponse with usage statistics
     * @throws ApiException If request fails
     */
    public ApiUsageResponse getUserApiUsage(String userId) throws ApiException {
        String path = "/api/v1/users/" + userId + "/api-usage";
        ApiResponse response = client.get(path);
        return response.as(ApiUsageResponse.class);
    }

    /**
     * Reset user password
     *
     * @param userId The user ID
     * @param resetRequest Password reset request
     * @return UserResponse with updated user information
     * @throws ApiException If password reset fails
     */
    public UserResponse resetUserPassword(String userId, Map<String, Object> resetRequest) throws ApiException {
        String path = "/api/v1/users/" + userId + "/reset-password";
        ApiResponse response = client.post(path, resetRequest);
        return response.as(UserResponse.class);
    }

    /**
     * Get user statistics
     *
     * @return UserStatsResponse with overall user statistics
     * @throws ApiException If request fails
     */
    public UserStatsResponse getUsersStats() throws ApiException {
        ApiResponse response = client.get("/api/v1/users/stats");
        return response.as(UserStatsResponse.class);
    }
}