import {
	IExecuteFunctions,
	INodeExecutionData,
	INodeType,
	INodeTypeDescription,
	NodeApiError,
	NodeOperationError,
	INode,
} from 'n8n-workflow';
import { promisify } from 'util';
import { exec } from 'child_process';
import * as path from 'path';

class NovaActHelper {
	static async executeScript(
		nodeInstance: INode,
		apiKey: string,
		operation: string,
		params: any
	): Promise<any> {
		const pExec = promisify(exec);
		
		// Path to the Python script (use relative path from dist)
		const scriptPath = path.join(__dirname, 'nova_act_runner.py');
		
		// Prepare arguments
		const args = [
			'python3',
			scriptPath,
			'--api_key', `"${apiKey}"`,
			'--operation', operation,
			'--params', `'${JSON.stringify(params)}'`
		];

		const command = args.join(' ');

		try {
			const { stdout, stderr } = await pExec(command, {
				timeout: (params.timeout || 300) * 1000, // Convert to milliseconds
			});

			if (stderr && !stderr.includes('WARNING')) {
				throw new NodeApiError(nodeInstance, {
					message: `Nova Act script error: ${stderr}`,
					description: 'Check your API key and commands',
				});
			}

			// Parse the JSON output from the Python script
			try {
				return JSON.parse(stdout.trim());
			} catch (parseError) {
				// If JSON parsing fails, return the raw output
				return { stdout: stdout.trim(), stderr: stderr || null };
			}

		} catch (error: any) {
			throw new NodeOperationError(nodeInstance, 
				`Failed to execute Nova Act automation: ${error.message}`
			);
		}
	}
}

export class NovaAct implements INodeType {
	description: INodeTypeDescription = {
		displayName: 'Amazon Nova Act',
		name: 'novaAct',
		icon: 'file:novaAct.svg',
		group: ['automation'],
		version: 1,
		description: 'Automates browser actions using natural language with Amazon Nova Act',
		defaults: {
			name: 'Amazon Nova Act',
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
				displayName: 'Resource',
				name: 'resource',
				type: 'options',
				options: [
					{
						name: 'Browser',
						value: 'browser',
					},
				],
				default: 'browser',
				noDataExpression: true,
			},
			{
				displayName: 'Operation',
				name: 'operation',
				type: 'options',
				displayOptions: {
					show: {
						resource: ['browser'],
					},
				},
				options: [
					{
						name: 'Perform Actions',
						value: 'performActions',
						action: 'Perform browser actions using natural language commands',
						description: 'Execute a series of browser actions',
					},
					{
						name: 'Extract Data',
						value: 'extractData',
						action: 'Extract structured data from a webpage',
						description: 'Navigate to a page and extract specific information',
					},
				],
				default: 'performActions',
				noDataExpression: true,
			},
			{
				displayName: 'Starting URL',
				name: 'startingUrl',
				type: 'string',
				default: '',
				placeholder: 'https://example.com',
				description: 'The URL to start the browser session (optional)',
				displayOptions: {
					show: {
						resource: ['browser'],
					},
				},
			},
			{
				displayName: 'Headless Mode',
				name: 'headless',
				type: 'boolean',
				default: true,
				description: 'Whether to run the browser without a visible UI. Turn off for debugging.',
				displayOptions: {
					show: {
						resource: ['browser'],
					},
				},
			},
			{
				displayName: 'Commands',
				name: 'commands',
				type: 'string',
				default: '',
				required: true,
				typeOptions: {
					rows: 8,
				},
				description: 'Natural language commands to execute, one per line',
				placeholder: 'Go to https://example.com\nClick the "Sign up" button\nFill in the form\nTake a screenshot',
				displayOptions: {
					show: {
						resource: ['browser'],
						operation: ['performActions'],
					},
				},
			},
			{
				displayName: 'Data Schema (JSON)',
				name: 'dataSchema',
				type: 'json',
				default: '{\n  "title": "string",\n  "price": "string",\n  "description": "string"\n}',
				description: 'JSON schema defining the structure of data to extract',
				displayOptions: {
					show: {
						resource: ['browser'],
						operation: ['extractData'],
					},
				},
			},
			{
				displayName: 'Navigation Commands',
				name: 'navigationCommands',
				type: 'string',
				default: '',
				typeOptions: {
					rows: 4,
				},
				description: 'Commands to navigate and find the data (optional)',
				placeholder: 'Search for "laptop"\nClick on the first result\nScroll to product details',
				displayOptions: {
					show: {
						resource: ['browser'],
						operation: ['extractData'],
					},
				},
			},
			{
				displayName: 'Session Timeout (seconds)',
				name: 'timeout',
				type: 'number',
				default: 300,
				description: 'Maximum time to wait for the automation to complete',
				displayOptions: {
					show: {
						resource: ['browser'],
					},
				},
			},
		],
	};

	async execute(this: IExecuteFunctions): Promise<INodeExecutionData[][]> {
		const items = this.getInputData();
		const returnData: INodeExecutionData[] = [];

		for (let i = 0; i < items.length; i++) {
			try {
				const credentials = await this.getCredentials('novaActApi');
				const resource = this.getNodeParameter('resource', i) as string;
				const operation = this.getNodeParameter('operation', i) as string;
				const startingUrl = this.getNodeParameter('startingUrl', i, '') as string;
				const headless = this.getNodeParameter('headless', i, true) as boolean;
				const timeout = this.getNodeParameter('timeout', i, 300) as number;

				if (resource === 'browser') {
					if (operation === 'performActions') {
						const commands = this.getNodeParameter('commands', i, '') as string;
						
						if (!commands.trim()) {
							throw new NodeOperationError(this.getNode(), 'No commands provided');
						}

						const result = await NovaActHelper.executeScript(
							this.getNode(),
							credentials.apiKey as string,
							'perform_actions',
							{
								commands: commands.trim(),
								starting_url: startingUrl,
								headless,
								timeout,
							}
						);

						returnData.push({
							json: {
								success: true,
								result: result.stdout,
								screenshots: result.screenshots || [],
								executedCommands: commands.split('\n').filter(cmd => cmd.trim()),
							},
						});

					} else if (operation === 'extractData') {
						const dataSchema = this.getNodeParameter('dataSchema', i, '{}') as string;
						const navigationCommands = this.getNodeParameter('navigationCommands', i, '') as string;

						if (!startingUrl.trim()) {
							throw new NodeOperationError(this.getNode(), 'Starting URL is required for data extraction');
						}

						let parsedSchema;
						try {
							parsedSchema = JSON.parse(dataSchema);
						} catch (error) {
							throw new NodeOperationError(this.getNode(), 'Invalid JSON schema provided');
						}

						const result = await NovaActHelper.executeScript(
							this.getNode(),
							credentials.apiKey as string,
							'extract_data',
							{
								starting_url: startingUrl,
								navigation_commands: navigationCommands.trim(),
								data_schema: parsedSchema,
								headless,
								timeout,
							}
						);

						returnData.push({
							json: {
								success: true,
								extractedData: result.extracted_data || {},
								screenshots: result.screenshots || [],
								url: startingUrl,
							},
						});
					}
				}
			} catch (error) {
				if (this.continueOnFail()) {
					returnData.push({
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

		return [returnData];
	}
}