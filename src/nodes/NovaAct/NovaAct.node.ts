import {
	IExecuteFunctions,
	INodeExecutionData,
	INodeType,
	INodeTypeDescription,
	NodeOperationError,
} from 'n8n-workflow';
import { spawn } from 'child_process';

export class NovaAct implements INodeType {
	description: INodeTypeDescription = {
		displayName: 'Nova Act',
		name: 'novaAct',
		icon: 'fa:robot',
		group: ['transform'],
		version: 1,
		description: 'Run an Amazon Nova Act prompt for browser automation',
		defaults: {
			name: 'Nova Act',
		},
		inputs: ['main'] as any,
		outputs: ['main'] as any,
		credentials: [
			{
				name: 'novaActApi',
				required: true,
			},
		],
		properties: [
			{
				displayName: 'Operation',
				name: 'operation',
				type: 'options',
				options: [
					{
						name: 'Perform Actions',
						value: 'action',
						description: 'Execute browser actions like clicking, typing, navigating',
					},
					{
						name: 'Extract Data',
						value: 'extract',
						description: 'Extract structured data from the page using a JSON schema',
					},
					{
						name: 'Action + Extract',
						value: 'action_extract',
						description: 'Perform actions then extract data with a schema',
					},
				],
				default: 'action',
				description: 'Type of operation to perform',
			},
			{
				displayName: 'Prompt',
				name: 'prompt',
				type: 'string',
				default: '',
				placeholder: 'Search for a coffee maker',
				required: true,
				typeOptions: {
					rows: 4,
				},
				description: 'Natural language prompt for Nova Act to execute',
			},
			{
				displayName: 'Start URL',
				name: 'url',
				type: 'string',
				default: 'https://www.amazon.com',
				placeholder: 'https://example.com',
				description: 'The URL to start the browser session',
			},
			{
				displayName: 'Data Schema (JSON)',
				name: 'schema',
				type: 'json',
				default: '',
				description: 'JSON schema defining the structure of data to extract. Leave empty for auto-generation based on prompt and URL.',
				placeholder: '{"products": [{"title": "string", "price": "string", "rating": "number"}]}',
				displayOptions: {
					show: {
						operation: ['extract', 'action_extract'],
					},
				},
			},
			{
				displayName: 'Headless Mode',
				name: 'headless',
				type: 'boolean',
				default: true,
				description: 'Whether to run the browser without a visible UI',
			},
			{
				displayName: 'Timeout (seconds)',
				name: 'timeout',
				type: 'number',
				default: 300,
				description: 'Maximum time to wait for the automation to complete',
			},
			{
				displayName: 'Options',
				name: 'options',
				type: 'collection',
				placeholder: 'Add Option',
				default: {},
				options: [
					{
						displayName: 'Capture Screenshots',
						name: 'captureScreenshots',
						type: 'boolean',
						default: true,
						description: 'Whether to capture screenshots during execution',
					},
					{
						displayName: 'Detailed Logging',
						name: 'detailedLogging',
						type: 'boolean',
						default: true,
						description: 'Whether to include detailed execution logs in the output',
					},
					{
						displayName: 'Include Stack Trace on Error',
						name: 'includeStackTrace',
						type: 'boolean',
						default: false,
						description: 'Whether to include full stack traces in error responses',
					},
				],
			},
		],
	};

	async execute(this: IExecuteFunctions): Promise<INodeExecutionData[][]> {
		const items = this.getInputData();
		const results: INodeExecutionData[] = [];

		for (let i = 0; i < items.length; i++) {
			try {
				// Get credentials
				const credentials = await this.getCredentials('novaActApi');
				const apiKey = credentials.apiKey as string;

				const operation = this.getNodeParameter('operation', i) as string;
				const prompt = this.getNodeParameter('prompt', i) as string;
				const url = this.getNodeParameter('url', i) as string;
				const schema = this.getNodeParameter('schema', i, '') as string;
				const headless = this.getNodeParameter('headless', i, true) as boolean;
				const timeout = this.getNodeParameter('timeout', i, 300) as number;
				const options = this.getNodeParameter('options', i, {}) as any;

				if (!prompt.trim()) {
					throw new NodeOperationError(this.getNode(), 'Prompt is required');
				}

				// Schema is now optional for extract operations (auto-generation available)

				// Prepare payload for Python script
				const payload: any = {
					operation,
					prompt: prompt.trim(),
					url: url || 'about:blank',
					headless,
					timeout,
					api_key: apiKey,
					capture_screenshots: options.captureScreenshots !== false, // default true
					detailed_logging: options.detailedLogging !== false, // default true
					include_stack_trace: options.includeStackTrace === true, // default false
				};

				// Add schema if provided
				if (schema && schema.trim()) {
					try {
						payload.schema = JSON.parse(schema);
					} catch (error) {
						throw new NodeOperationError(this.getNode(), 'Invalid JSON schema provided');
					}
				}

				// Spawn Python process
				const runnerPath = process.env.NOVA_RUNNER || '/opt/nova_runner.py';
				const child = spawn('python3', [runnerPath], {
					stdio: ['pipe', 'pipe', 'inherit'],
					env: { ...process.env }, // Pass NOVA_ACT_API_KEY etc.
				});

				// Send payload to Python script
				child.stdin.write(JSON.stringify(payload));
				child.stdin.end();

				// Collect output
				const chunks: Buffer[] = [];
				for await (const chunk of child.stdout) {
					chunks.push(chunk);
				}
				
				const output = Buffer.concat(chunks).toString();
				const result = JSON.parse(output);

				results.push({ json: result });

			} catch (error) {
				if (this.continueOnFail()) {
					results.push({
						json: {
							success: false,
							error: error.message,
						},
					});
					continue;
				}
				throw error;
			}
		}

		return [results];
	}
}