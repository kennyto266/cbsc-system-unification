"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const globals_1 = require("@jest/globals");
const glmClient_1 = require("../api/glmClient");
// Mock fetch globally
const mockFetch = jest.fn();
global.fetch = mockFetch;
(0, globals_1.describe)('GLMClient', () => {
    let client;
    (0, globals_1.beforeEach)(() => {
        client = new glmClient_1.GLMClient('test-api-key');
        mockFetch.mockClear();
    });
    (0, globals_1.afterEach)(() => {
        mockFetch.mockReset();
    });
    (0, globals_1.it)('should initialize with API key', () => {
        (0, globals_1.expect)(client).toBeDefined();
    });
    (0, globals_1.it)('should have correct base URL', () => {
        (0, globals_1.expect)(client).toBeInstanceOf(glmClient_1.GLMClient);
    });
    (0, globals_1.it)('should format GLM request correctly for chat', async () => {
        // Mock successful API response
        mockFetch.mockResolvedValueOnce({
            ok: true,
            json: async () => ({
                id: 'chat-123',
                created: 1234567890,
                model: 'glm-4-plus',
                choices: [{
                        index: 0,
                        message: {
                            role: 'assistant',
                            content: 'Test response'
                        },
                        finish_reason: 'stop'
                    }],
                usage: {
                    prompt_tokens: 10,
                    completion_tokens: 5,
                    total_tokens: 15
                }
            })
        });
        const messages = [
            { role: 'user', content: 'Hello' }
        ];
        await client.chat(messages);
        // Verify fetch was called with correct parameters
        (0, globals_1.expect)(mockFetch).toHaveBeenCalledTimes(1);
        const callArgs = mockFetch.mock.calls[0];
        (0, globals_1.expect)(callArgs[0]).toBe('https://open.bigmodel.cn/api/paas/v4/chat/completions');
        (0, globals_1.expect)(callArgs[1]?.method).toBe('POST');
        (0, globals_1.expect)(callArgs[1]?.headers).toMatchObject({
            'Content-Type': 'application/json',
            'Authorization': 'Bearer test-api-key'
        });
        const requestBody = JSON.parse(callArgs[1]?.body);
        (0, globals_1.expect)(requestBody.model).toBe('glm-4-plus');
        (0, globals_1.expect)(requestBody.messages).toEqual(messages);
        (0, globals_1.expect)(requestBody.temperature).toBe(0.7);
        (0, globals_1.expect)(requestBody.top_p).toBe(0.9);
        (0, globals_1.expect)(requestBody.max_tokens).toBe(2000);
    });
    (0, globals_1.it)('should return assistant content from chat response', async () => {
        mockFetch.mockResolvedValueOnce({
            ok: true,
            json: async () => ({
                id: 'chat-123',
                created: 1234567890,
                model: 'glm-4-plus',
                choices: [{
                        index: 0,
                        message: {
                            role: 'assistant',
                            content: 'This is a test response'
                        },
                        finish_reason: 'stop'
                    }],
                usage: {
                    prompt_tokens: 10,
                    completion_tokens: 5,
                    total_tokens: 15
                }
            })
        });
        const messages = [
            { role: 'user', content: 'Test' }
        ];
        const response = await client.chat(messages);
        (0, globals_1.expect)(response).toBe('This is a test response');
    });
    (0, globals_1.it)('should throw error when API request fails', async () => {
        mockFetch.mockResolvedValueOnce({
            ok: false,
            statusText: 'Unauthorized'
        });
        const messages = [
            { role: 'user', content: 'Test' }
        ];
        await (0, globals_1.expect)(client.chat(messages)).rejects.toThrow('GLM API error: Unauthorized');
    });
    (0, globals_1.it)('should generate strategy with correct system prompt', async () => {
        mockFetch.mockResolvedValueOnce({
            ok: true,
            json: async () => ({
                id: 'chat-123',
                choices: [{
                        index: 0,
                        message: {
                            role: 'assistant',
                            content: 'Generated strategy code'
                        },
                        finish_reason: 'stop'
                    }],
                usage: {
                    prompt_tokens: 100,
                    completion_tokens: 200,
                    total_tokens: 300
                }
            })
        });
        await client.generateStrategy('moving average crossover');
        (0, globals_1.expect)(mockFetch).toHaveBeenCalledTimes(1);
        const callArgs = mockFetch.mock.calls[0];
        const requestBody = JSON.parse(callArgs[1]?.body);
        // Verify system prompt is included
        const systemMessage = requestBody.messages.find((m) => m.role === 'system');
        (0, globals_1.expect)(systemMessage).toBeDefined();
        (0, globals_1.expect)(systemMessage.content).toContain('quantitative trading strategy expert');
        (0, globals_1.expect)(systemMessage.content).toContain('Jupyter notebook');
        // Verify user message includes strategy description
        const userMessage = requestBody.messages.find((m) => m.role === 'user');
        (0, globals_1.expect)(userMessage.content).toContain('moving average crossover');
    });
    (0, globals_1.it)('should handle network errors gracefully', async () => {
        mockFetch.mockRejectedValueOnce(new Error('Network error'));
        const messages = [
            { role: 'user', content: 'Test' }
        ];
        await (0, globals_1.expect)(client.chat(messages)).rejects.toThrow('Network error');
    });
    (0, globals_1.it)('should handle empty API response', async () => {
        mockFetch.mockResolvedValueOnce({
            ok: true,
            json: async () => ({
                choices: []
            })
        });
        const messages = [
            { role: 'user', content: 'Test' }
        ];
        await (0, globals_1.expect)(client.chat(messages)).rejects.toThrow();
    });
    (0, globals_1.it)('should have close method for API compatibility', async () => {
        // Verify close method exists and is callable
        (0, globals_1.expect)(typeof client.close).toBe('function');
        // close() should resolve without errors
        await (0, globals_1.expect)(client.close()).resolves.toBeUndefined();
        // Multiple close calls should be safe
        await (0, globals_1.expect)(client.close()).resolves.toBeUndefined();
    });
    (0, globals_1.it)('should maintain API consistency with Python service', async () => {
        // Verify GLMClient has the same interface as Python GLMService
        (0, globals_1.expect)(client.chat).toBeDefined();
        (0, globals_1.expect)(client.generateStrategy).toBeDefined();
        (0, globals_1.expect)(client.close).toBeDefined();
        // All methods should be functions
        (0, globals_1.expect)(typeof client.chat).toBe('function');
        (0, globals_1.expect)(typeof client.generateStrategy).toBe('function');
        (0, globals_1.expect)(typeof client.close).toBe('function');
    });
});
//# sourceMappingURL=glmClient.test.js.map