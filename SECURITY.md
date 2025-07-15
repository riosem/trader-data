# Security Policy

## Supported Versions

This project is currently in active development. Only the latest version is supported with security updates.

| Version | Supported          |
| ------- | ------------------ |
| main    | :white_check_mark: |

## Reporting Security Vulnerabilities

If you discover a security vulnerability in this project, please report it by creating a GitHub issue with the "security" label. Please do not disclose security vulnerabilities publicly until they have been addressed.

## Security Practices

### Secrets Management
- All sensitive data (API keys, database credentials, etc.) are stored in AWS Systems Manager Parameter Store
- No hardcoded credentials are committed to version control
- Environment variables containing sensitive data use SSM parameter references

### AWS Security
- IAM roles follow the principle of least privilege
- All serverless functions run with minimal required permissions
- VPC configuration provides network isolation where appropriate
- Security groups restrict access to necessary ports and protocols only

### Container Security
- Docker images are scanned for vulnerabilities
- Base images are regularly updated
- No sensitive data is included in container images

### Code Security
- Dependencies are regularly updated
- Automated security scanning is recommended for production deployments
- Input validation is implemented for all external data sources

### Data Protection
- Data in transit is encrypted using TLS
- AWS services provide encryption at rest
- Temporary credentials are used where possible

## Security Configuration Checklist

Before deploying to production, ensure:

- [ ] All SSM parameters are properly configured
- [ ] IAM roles have minimal required permissions
- [ ] Security groups are properly configured
- [ ] VPC configuration provides appropriate network isolation
- [ ] All external API endpoints use HTTPS
- [ ] Logging is enabled for security monitoring
- [ ] AWS CloudTrail is enabled for audit logging

## Third-Party Services

This project integrates with several external services:
- **Auth0**: For authentication and authorization
- **Coinbase Advanced Trade API**: For cryptocurrency data
- **AWS Services**: For infrastructure and data processing
- **Ollama**: For LLM capabilities

Ensure all third-party service credentials are:
- Stored securely in AWS SSM Parameter Store
- Rotated regularly according to security best practices
- Monitored for unusual activity

## Updates and Maintenance

- Regularly update dependencies to address security vulnerabilities
- Monitor AWS security bulletins and apply patches as needed
- Review and rotate API keys and credentials periodically
- Audit IAM permissions and remove unnecessary access

## Contact

For security-related questions or concerns, please create an issue in this repository.
