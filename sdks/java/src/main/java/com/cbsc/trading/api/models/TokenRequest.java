package com.cbsc.trading.api.models;

import com.fasterxml.jackson.annotation.JsonInclude;
import com.fasterxml.jackson.annotation.JsonProperty;

/**
 * Token Request model for OAuth2 authentication
 */
@JsonInclude(JsonInclude.Include.NON_NULL)
public class TokenRequest {
    @JsonProperty("grant_type")
    private GrantType grantType;

    @JsonProperty("client_id")
    private String clientId;

    @JsonProperty("client_secret")
    private String clientSecret;

    @JsonProperty("scope")
    private String scope;

    @JsonProperty("refresh_token")
    private String refreshToken;

    public TokenRequest() {}

    public TokenRequest(GrantType grantType, String clientId, String clientSecret) {
        this.grantType = grantType;
        this.clientId = clientId;
        this.clientSecret = clientSecret;
    }

    public GrantType getGrantType() {
        return grantType;
    }

    public void setGrantType(GrantType grantType) {
        this.grantType = grantType;
    }

    public String getClientId() {
        return clientId;
    }

    public void setClientId(String clientId) {
        this.clientId = clientId;
    }

    public String getClientSecret() {
        return clientSecret;
    }

    public void setClientSecret(String clientSecret) {
        this.clientSecret = clientSecret;
    }

    public String getScope() {
        return scope;
    }

    public void setScope(String scope) {
        this.scope = scope;
    }

    public String getRefreshToken() {
        return refreshToken;
    }

    public void setRefreshToken(String refreshToken) {
        this.refreshToken = refreshToken;
    }

    @Override
    public String toString() {
        return "TokenRequest{" +
                "grantType=" + grantType +
                ", clientId='" + clientId + '\'' +
                ", clientSecret='***'" +
                ", scope='" + scope + '\'' +
                ", refreshToken='" + refreshToken + '\'' +
                '}';
    }
}