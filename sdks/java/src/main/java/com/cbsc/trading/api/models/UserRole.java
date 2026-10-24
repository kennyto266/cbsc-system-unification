package com.cbsc.trading.api.models;

/**
 * User Role enumeration
 */
public enum UserRole {
    @JsonProperty("admin")
    ADMIN("admin"),

    @JsonProperty("developer")
    DEVELOPER("developer"),

    @JsonProperty("user")
    USER("user"),

    @JsonProperty("readonly")
    READONLY("readonly");

    private final String value;

    UserRole(String value) {
        this.value = value;
    }

    public String getValue() {
        return value;
    }

    @Override
    public String toString() {
        return value;
    }

    public static UserRole fromValue(String value) {
        for (UserRole role : UserRole.values()) {
            if (role.value.equals(value)) {
                return role;
            }
        }
        throw new IllegalArgumentException("Invalid UserRole value: " + value);
    }
}