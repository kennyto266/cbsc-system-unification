import { describe, it, expect, beforeEach, afterEach } from '@jest/globals';
import { GLMClient, GLMMessage } from '../api/glmClient';

// Mock fetch globally
const mockFetch = jest.fn();
global.fetch = mockFetch;

describe('GLMClient', () => {
  let client: GLMClient;

  beforeEach(() => {
    client = new GLMClient('test-api-key');
    mockFetch.mockClear();
  });

  afterEach(() => {
    mockFetch.mockReset();
  });

  it('should initialize with API key', () => {
    expect(client).toBeDefined();
  });

  it('should have correct base URL', () => {
    expect(client).toBeInstanceOf(GLMClient);
  });

  it('should format GLM request correctly for chat', async () => {
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

    const messages: GLMMessage[] = [
      { role: 'user', content: 'Hello' }
    ];

    await client.chat(messages);

    // Verify fetch was called with correct parameters
    expect(mockFetch).toHaveBeenCalledTimes(1);
    const callArgs = mockFetch.mock.calls[0];

    expect(callArgs[0]).toBe('https://open.bigmodel.cn/api/paas/v4/chat/completions');
    expect(callArgs[1]?.method).toBe('POST');
    expect(callArgs[1]?.headers).toMatchObject({
      'Content-Type': 'application/json',
      'Authorization': 'Bearer test-api-key'
    });

    const requestBody = JSON.parse(callArgs[1]?.body as string);
    expect(requestBody.model).toBe('glm-4-plus');
    expect(requestBody.messages).toEqual(messages);
    expect(requestBody.temperature).toBe(0.7);
    expect(requestBody.top_p).toBe(0.9);
    expect(requestBody.max_tokens).toBe(2000);
  });

  it('should return assistant content from chat response', async () => {
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

    const messages: GLMMessage[] = [
      { role: 'user', content: 'Test' }
    ];

    const response = await client.chat(messages);

    expect(response).toBe('This is a test response');
  });

  it('should throw error when API request fails', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: false,
      statusText: 'Unauthorized'
    });

    const messages: GLMMessage[] = [
      { role: 'user', content: 'Test' }
    ];

    await expect(client.chat(messages)).rejects.toThrow('GLM API error: Unauthorized');
  });

  it('should generate strategy with correct system prompt', async () => {
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

    expect(mockFetch).toHaveBeenCalledTimes(1);
    const callArgs = mockFetch.mock.calls[0];
    const requestBody = JSON.parse(callArgs[1]?.body as string);

    // Verify system prompt is included
    const systemMessage = requestBody.messages.find((m: GLMMessage) => m.role === 'system');
    expect(systemMessage).toBeDefined();
    expect(systemMessage.content).toContain('quantitative trading strategy expert');
    expect(systemMessage.content).toContain('Jupyter notebook');

    // Verify user message includes strategy description
    const userMessage = requestBody.messages.find((m: GLMMessage) => m.role === 'user');
    expect(userMessage.content).toContain('moving average crossover');
  });

  it('should handle network errors gracefully', async () => {
    mockFetch.mockRejectedValueOnce(new Error('Network error'));

    const messages: GLMMessage[] = [
      { role: 'user', content: 'Test' }
    ];

    await expect(client.chat(messages)).rejects.toThrow('Network error');
  });

  it('should handle empty API response', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        choices: []
      })
    });

    const messages: GLMMessage[] = [
      { role: 'user', content: 'Test' }
    ];

    await expect(client.chat(messages)).rejects.toThrow();
  });
});
