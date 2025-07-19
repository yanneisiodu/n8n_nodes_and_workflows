import { ICredentialType, INodeProperties } from 'n8n-workflow';

export class NovaActApi implements ICredentialType {
	name = 'novaActApi';
	displayName = 'Amazon Nova Act API';
	documentationUrl = 'https://nova.amazon.com/act';
	properties: INodeProperties[] = [
		{
			displayName: 'API Key',
			name: 'apiKey',
			type: 'string',
			typeOptions: {
				password: true,
			},
			default: '',
			required: true,
			description: 'Your Amazon Nova Act API Key. Get it from nova.amazon.com/act',
		},
	];
}