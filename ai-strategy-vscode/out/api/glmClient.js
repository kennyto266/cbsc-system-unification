"use strict";
/**
 * GLM 4.7 API Client
 * Interface to Zhipu AI's GLM-4-plus model for strategy generation
 */
Object.defineProperty(exports, "__esModule", { value: true });
exports.GLMClient = void 0;
class GLMClient {
    constructor(apiKey) {
        this.baseURL = 'https://open.bigmodel.cn/api/paas/v4/';
        this.apiKey = apiKey;
    }
    /**
     * Send chat request to GLM API
     * @param messages - Array of conversation messages
     * @returns Assistant's response content
     */
    async chat(messages) {
        const request = {
            model: 'glm-4-plus',
            messages,
            temperature: 0.7,
            top_p: 0.9,
            max_tokens: 2000
        };
        const response = await fetch(`${this.baseURL}chat/completions`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${this.apiKey}`
            },
            body: JSON.stringify(request)
        });
        if (!response.ok) {
            throw new Error(`GLM API error: ${response.statusText}`);
        }
        const data = await response.json();
        if (!data.choices || data.choices.length === 0) {
            throw new Error('GLM API returned no choices');
        }
        return data.choices[0].message.content;
    }
    /**
     * Generate trading strategy from description
     * @param description - Strategy description in natural language
     * @returns Generated Python code for the strategy
     */
    async generateStrategy(description) {
        const systemPrompt = {
            role: 'system',
            content: `You are a quantitative trading strategy expert. Generate Python code for trading strategies.
The strategy should be structured as a Jupyter notebook with the following cells:
1. Imports and configuration
2. Data fetching
3. Strategy parameters
4. Signal generation
5. Backtesting
6. Results visualization

Return ONLY valid Python code that can be executed in a Jupyter notebook.`
        };
        const userMessage = {
            role: 'user',
            content: `Create a trading strategy: ${description}`
        };
        return await this.chat([systemPrompt, userMessage]);
    }
    /**
     * Cleanup method for consistency with Python service
     * No-op for fetch-based client but maintains API compatibility
     */
    async close() {
        // No cleanup needed for fetch API
        // Kept for API compatibility with Python service
    }
}
exports.GLMClient = GLMClient;
//# sourceMappingURL=glmClient.js.map