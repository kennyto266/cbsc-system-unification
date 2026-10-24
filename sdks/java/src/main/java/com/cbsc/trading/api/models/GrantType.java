package com.cbsc.trading.api.models;

/**
 * OAuth2 Grant Type enumeration
 */
public enum GrantType {
    @JsonProperty("client_credentials")
    CLIENT_CREDENTIALS("client_credentials"),

    @JsonProperty("authorization_code")
    AUTHORIZATION_CODE("authorization_code"),

    @JsonProperty("refresh_token")
    REFRESH_TOKEN("refresh_token");

    private final String value;

    GrantType(String value) {
        this.value = value;
    }

    public String getValue() {
        return value;
    }

    @Override
    public String toString() {
        return value;
    }

    public static GrantType fromValue(String value) {
        for (GrantType type : GrantType.values()) {
            if (type.value.equals(value)) {
                return type;
            }
        }
        throw new IllegalArgumentException("Invalid GrantType value: " + value);
    }
}