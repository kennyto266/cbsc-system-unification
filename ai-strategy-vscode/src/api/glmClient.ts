/**
 * GLM 4.7 API Client
 * Interface to Zhipu AI's GLM-4-plus model for strategy generation
 */

export interface GLMMessage {
  role: 'system' | 'user' | 'assistant';
  content: string;
}

export interface GLMRequest {
  model: string;
  messages: GLMMessage[];
  temperature?: number;
  top_p?: number;
  max_tokens?: number;
}

export interface GLMChoice {
  index: number;
  message: GLMMessage;
  finish_reason: string;
}

export interface GLMUsage {
  prompt_tokens: number;
  completion_tokens: number;
  total_tokens: number;
}

export interface GLMResponse {
  id: string;
  created: number;
  model: string;
  choices: GLMChoice[];
  usage: GLMUsage;
}

export class GLMClient {
  private apiKey: string;
  private baseURL = 'https://open.bigmodel.cn/api/paas/v4/';

  constructor(apiKey: string) {
    this.apiKey = apiKey;
  }

  /**
   * Send chat request to GLM API
   * @param messages - Array of conversation messages
   * @returns Assistant's response content
   */
  async chat(messages: GLMMessage[]): Promise<string> {
    const request: GLMRequest = {
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

    const data: GLMResponse = await response.json();

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
  async generateStrategy(description: string): Promise<string> {
    const systemPrompt: GLMMessage = {
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

    const userMessage: GLMMessage = {
      role: 'user',
      content: `Create a trading strategy: ${description}`
    };

    return await this.chat([systemPrompt, userMessage]);
  }
}
